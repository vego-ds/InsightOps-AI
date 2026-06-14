from collections.abc import AsyncIterator
import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from insightops.api.contracts import (
    AnalysisRequest,
    AnalysisRequestResponse,
    AnalysisRunCreatedResponse,
    AnalysisRunCreateRequest,
    AnalysisResponse,
    CsvUploadPreviewResponse,
    DatasetDeleteResponse,
    DatasetUploadErrorResponse,
    DatasetUploadSuccessResponse,
    ErrorResponse,
    HealthResponse,
)
from insightops.config import load_app_settings
from insightops.conversation import conversation_store
from insightops.datasets import (
    DatasetMetadata,
    delete_registered_dataset,
    get_dataset,
    get_dataset_path,
    register_dataset,
    save_dataset_file,
)
from insightops.datasets.storage import DATASET_STORAGE_ROOT
from insightops.validation.schema import (
    CsvSchemaError,
    CsvDecodeError,
    CsvIncompatibleSchemaError,
    CsvSchemaInspection,
    inspect_sales_csv_schema,
)
from insightops.io.csv_compatibility import prepare_csv_for_analysis
from insightops.io.csv_compatibility import PreparedCsvForAnalysis
from insightops.io.dataset_preview import build_dataset_preview, is_supported_csv_upload
from insightops.pipeline.sample_analysis import (
    analyze_sales_csv_file,
    analyze_sample_sales_data,
)
from insightops.io.upload_guardrails import persist_upload_temporarily
from insightops.io.upload_guardrails import UploadedCsvFile
from insightops.reports.export_service import (
    ReportGenerationBlockedError,
    UnsupportedReportFormatError,
    export_analysis_report,
    normalize_report_format,
)
from insightops.runtime import (
    DockerRuntimeAdapter,
    LocalPythonRuntimeAdapter,
    MockRuntimeAdapter,
    RunContext,
    RuntimeAdapter,
)

from app.interpreter import PythonInterpreterSandbox
from app.chat_agent import ChatAgentCodeGenerator

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
GENERATED_DIR = STATIC_DIR / "generated"
NOTEBOOK_DIR = GENERATED_DIR / "notebooks"
SCHEDULES_PATH = GENERATED_DIR / "schedules.json"
for directory in (GENERATED_DIR, NOTEBOOK_DIR):
    directory.mkdir(parents=True, exist_ok=True)

DATASET_STORAGE_DIR = DATASET_STORAGE_ROOT
DATASET_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

sessions: dict[str, PythonInterpreterSandbox] = {}
analysis_run_contexts: dict[str, RunContext] = {}
code_generator = ChatAgentCodeGenerator()

JsonObject = dict[str, Any]


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    session_id: str = Field(min_length=1, max_length=128)


class ChatResponse(BaseModel):
    prompt: str
    code: str
    stdout: str
    stderr: str
    error: str | None
    charts: list[str]
    attempts: list[JsonObject]
    code_executed: str


class ExecuteRequest(BaseModel):
    code: str = Field(min_length=1)
    session_id: str = Field(min_length=1, max_length=128)


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    error: str | None
    charts: list[str]
    attempts: list[JsonObject]
    code_executed: str


class ResetRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)


class SaveNotebookRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    notebook_name: str = Field(min_length=1, max_length=200)
    cells: list[JsonObject] = Field(default_factory=list)


class ScheduleRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    cron_expression: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)


def _select_runtime_adapter(runtime_name: str) -> RuntimeAdapter:
    if runtime_name == "docker":
        return DockerRuntimeAdapter()
    if runtime_name == "local_python":
        return LocalPythonRuntimeAdapter()
    return MockRuntimeAdapter()


settings = load_app_settings()
runtime_adapter: RuntimeAdapter = _select_runtime_adapter(settings.runtime)
app = FastAPI(
    title=settings.app_name,
    description=(
        "Governed sales analytics API for deterministic source metadata, "
        "validation, preparation, KPI computation, security scanning, "
        "anomaly detection, chart data, executive insights, and audit events."
    ),
    version="0.13.0",
)

app.mount(
    "/static/generated",
    StaticFiles(directory=GENERATED_DIR),
    name="static_generated",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _get_sandbox(session_id: str) -> PythonInterpreterSandbox:
    return sessions.setdefault(session_id, PythonInterpreterSandbox())


def _json_error(status_code: int, detail: str, error_code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error_code": error_code},
    )


def _prepare_csv_or_http_error(source_path: Path) -> PreparedCsvForAnalysis:
    try:
        return prepare_csv_for_analysis(source_path)
    except CsvDecodeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except CsvIncompatibleSchemaError as error:
        detail = (
            f"{error}\n"
            "Supported schemas:\n"
            "- canonical InsightOps sales schema\n"
            "- classic_sales_sample mapping"
        )
        raise HTTPException(status_code=400, detail=detail) from error
    except CsvSchemaError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _apply_schema_mapping_notes(
    analysis: AnalysisResponse,
    prepared: PreparedCsvForAnalysis,
) -> AnalysisResponse:
    if prepared.was_mapped:
        warnings_text = "; ".join(prepared.warnings)
        analysis.source_metadata.notes = (
            f"Schema mapped from {prepared.detected_schema}. Warnings: {warnings_text}"
        )
    return analysis


def _cleanup_uploaded_analysis_file(
    uploaded_file: UploadedCsvFile,
    prepared: PreparedCsvForAnalysis | None,
) -> None:
    if prepared and prepared.was_mapped and prepared.analysis_path.exists():
        prepared.analysis_path.unlink(missing_ok=True)
    if uploaded_file.path.exists():
        uploaded_file.path.unlink(missing_ok=True)


def _analyze_uploaded_csv(
    uploaded_file: UploadedCsvFile,
    prepared: PreparedCsvForAnalysis,
) -> AnalysisResponse:
    analysis = analyze_sales_csv_file(
        str(prepared.analysis_path),
        uploaded_file_name=uploaded_file.original_filename,
        uploaded_file_size_bytes=uploaded_file.size_bytes,
    )
    return _apply_schema_mapping_notes(analysis, prepared)


def _safe_generated_file(directory: Path, filename: str) -> Path:
    root = directory.resolve()
    path = (directory / filename).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(status_code=400, detail="Unsafe generated file path.")
    return path


def _notebook_path(session_id: str) -> Path:
    return _safe_generated_file(NOTEBOOK_DIR, f"{session_id}.json")


def _generated_chart_paths_for_session(session_id: str) -> list[Path]:
    prefix = f"chart_{session_id}_"
    return [
        path
        for path in GENERATED_DIR.glob("chart_*.png")
        if path.is_file() and path.name.startswith(prefix)
    ]


def _inspect_csv_or_http_error(source_path: Path) -> CsvSchemaInspection:
    try:
        return inspect_sales_csv_schema(source_path)
    except CsvDecodeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except CsvSchemaError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _load_json_object(path: Path) -> JsonObject:
    try:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as error:
        logger.warning("Ignoring invalid JSON state file %s: %s", path, error)
        return {}
    except OSError as error:
        logger.warning("Unable to read JSON state file %s: %s", path, error)
        return {}

    if isinstance(value, dict):
        return value
    logger.warning("Ignoring non-object JSON state file %s", path)
    return {}


@app.post("/api/chat", response_model=ChatResponse, tags=["interpreter"])
def api_chat(req: ChatRequest) -> ChatResponse:
    sandbox = _get_sandbox(req.session_id)

    # Get dataframe columns from locals to pass to code generator
    columns = []
    if "df" in sandbox.locals:
        columns = list(sandbox.locals["df"].columns)

    generated_code = code_generator.generate_code(req.prompt, columns)
    res = sandbox.execute(generated_code, req.session_id, prompt=req.prompt)

    return ChatResponse(
        prompt=req.prompt,
        code=generated_code,
        stdout=res["stdout"],
        stderr=res["stderr"],
        error=res["error"],
        charts=res["charts"],
        attempts=res["attempts"],
        code_executed=res["code_executed"],
    )


@app.post(
    "/api/analysis/request",
    response_model=AnalysisRequestResponse,
    tags=["analysis"],
    responses={400: {"model": ErrorResponse}},
)
def request_analysis(
    request: AnalysisRequest,
) -> AnalysisRequestResponse:
    if request.version != "insightops.analysis-request.v1":
        raise HTTPException(status_code=400, detail="Unsupported analysis request version.")
    if not request.datasetId.strip():
        raise HTTPException(status_code=400, detail="datasetId must be a non-empty string.")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message must be a non-empty string.")

    return AnalysisRequestResponse(
        version="insightops.analysis-response.v1",
        status="accepted",
        runId=uuid4().hex,
        assistantMessage=(
            "Analysis request accepted. Backend analysis execution will be "
            "connected in Milestone 6; no AI, code execution, or streaming was run."
        ),
    )


@app.post(
    "/api/analysis/runs",
    response_model=AnalysisRunCreatedResponse,
    tags=["analysis"],
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def create_analysis_run(
    request: AnalysisRunCreateRequest,
) -> AnalysisRunCreatedResponse | JSONResponse:
    if request.version != "insightops.analysis-run-create.v1":
        raise HTTPException(
            status_code=400,
            detail="Unsupported analysis run create version.",
        )
    if not request.datasetId.strip():
        raise HTTPException(status_code=400, detail="datasetId must be a non-empty string.")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message must be a non-empty string.")

    dataset_metadata = get_dataset(request.datasetId)
    dataset_path = get_dataset_path(request.datasetId)
    if dataset_metadata is None or dataset_path is None:
        return _json_error(404, "Unknown datasetId.", "UNKNOWN_DATASET")

    run_id = uuid4().hex
    conversation_id = request.conversationId or f"dataset:{request.datasetId}"
    conversation_context = conversation_store.get_or_create(
        conversation_id,
        request.datasetId,
    )
    analysis_run_contexts[run_id] = RunContext(
        run_id=run_id,
        dataset_id=request.datasetId,
        message=request.message,
        schema=[column.model_dump() for column in request.schema_],
        preview_rows=request.previewRows,
        conversation_id=conversation_id,
        conversation_context=conversation_context,
        dataset_metadata=dataset_metadata,
        dataset_path=dataset_path,
    )
    return AnalysisRunCreatedResponse(
        version="insightops.analysis-run-created.v1",
        status="created",
        runId=run_id,
        streamUrl=f"/api/analysis/runs/{run_id}/events",
    )


@app.get("/api/analysis/runs/{run_id}/events", tags=["analysis"])
def stream_analysis_run_events(run_id: str) -> StreamingResponse:
    return StreamingResponse(
        _analysis_run_event_stream(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/execute", response_model=ExecuteResponse, tags=["interpreter"])
def api_execute(req: ExecuteRequest) -> ExecuteResponse:
    sandbox = _get_sandbox(req.session_id)
    res = sandbox.execute(req.code, req.session_id, prompt="Raw code execution")
    return ExecuteResponse(
        stdout=res["stdout"],
        stderr=res["stderr"],
        error=res["error"],
        charts=res["charts"],
        attempts=res["attempts"],
        code_executed=res["code_executed"],
    )


@app.post("/api/save_notebook", tags=["interpreter"])
def api_save_notebook(req: SaveNotebookRequest) -> dict[str, str]:
    path = _notebook_path(req.session_id)
    data = {
        "session_id": req.session_id,
        "notebook_name": req.notebook_name,
        "cells": req.cells,
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    return {
        "status": "saved",
        "path": f"/static/generated/notebooks/{req.session_id}.json",
    }


@app.get("/api/list_notebooks", tags=["interpreter"])
def api_list_notebooks() -> list[JsonObject]:
    notebooks = []
    for path in NOTEBOOK_DIR.glob("*.json"):
        data = _load_json_object(path)
        if not data:
            continue
        cells = data.get("cells", [])
        notebooks.append(
            {
                "session_id": data.get("session_id"),
                "notebook_name": data.get("notebook_name"),
                "cell_count": len(cells) if isinstance(cells, list) else 0,
            }
        )
    return notebooks


@app.get("/api/load_notebook", tags=["interpreter"])
def api_load_notebook(session_id: str = Query(..., min_length=1, max_length=128)) -> JsonObject:
    path = _notebook_path(session_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Notebook not found")
    return _load_json_object(path)


@app.post("/api/schedule", tags=["interpreter"])
def api_schedule(req: ScheduleRequest) -> dict[str, str]:
    schedules = _load_json_object(SCHEDULES_PATH)
    schedules[req.session_id] = {"cron": req.cron_expression, "email": req.email}
    with SCHEDULES_PATH.open("w", encoding="utf-8") as file:
        json.dump(schedules, file, indent=2)
    return {"status": "scheduled"}


@app.post("/api/upload_dataset", tags=["interpreter"])
async def api_upload_dataset(
    session_id: str = Query(..., min_length=1, max_length=128),
    file: UploadFile | None = File(default=None),
) -> AnalysisResponse:
    uploaded_file = await persist_upload_temporarily(file, settings.max_upload_bytes)
    prepared = None
    try:
        prepared = _prepare_csv_or_http_error(uploaded_file.path)

        sandbox = _get_sandbox(session_id)
        sandbox.load_dataframe(str(prepared.analysis_path))

        return _analyze_uploaded_csv(uploaded_file, prepared)
    finally:
        _cleanup_uploaded_analysis_file(uploaded_file, prepared)


@app.post(
    "/api/datasets/upload",
    response_model=DatasetUploadSuccessResponse,
    tags=["datasets"],
    responses={400: {"model": DatasetUploadErrorResponse}},
)
async def upload_dataset_preview(
    file: UploadFile | None = File(default=None),
) -> DatasetUploadSuccessResponse | JSONResponse:
    if file is None or not is_supported_csv_upload(file.filename or "", file.content_type):
        return _unsupported_dataset_file_type_response()

    uploaded_file = await persist_upload_temporarily(file, settings.max_upload_bytes)
    try:
        dataset_id = uuid4().hex
        stored_path = save_dataset_file(
            uploaded_file.path,
            dataset_id=dataset_id,
            storage_root=DATASET_STORAGE_DIR,
        )
        dataset = build_dataset_preview(
            stored_path,
            dataset_id=dataset_id,
            original_filename=uploaded_file.original_filename,
            size_bytes=uploaded_file.size_bytes,
        )
        register_dataset(
            DatasetMetadata(
                dataset_id=dataset_id,
                file_name=uploaded_file.original_filename,
                mime_type="text/csv",
                size_bytes=uploaded_file.size_bytes,
                path=stored_path,
                storage_root=DATASET_STORAGE_DIR,
            )
        )
    finally:
        if uploaded_file.path.exists():
            uploaded_file.path.unlink(missing_ok=True)

    return DatasetUploadSuccessResponse(
        version="insightops.file-preview.v1",
        status="ok",
        dataset=dataset,
        warnings=[],
    )


@app.delete(
    "/api/datasets/{dataset_id}",
    response_model=DatasetDeleteResponse,
    tags=["datasets"],
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def delete_dataset(dataset_id: str) -> DatasetDeleteResponse | JSONResponse:
    try:
        deleted = delete_registered_dataset(dataset_id)
    except ValueError as error:
        return _json_error(400, str(error), "UNSAFE_DATASET_PATH")

    if deleted is None:
        return _json_error(404, "Unknown datasetId.", "UNKNOWN_DATASET")

    return DatasetDeleteResponse(
        version="insightops.dataset-delete.v1",
        status="deleted",
        datasetId=dataset_id,
    )


@app.post("/api/sample_dataset", tags=["interpreter"])
def api_sample_dataset(
    session_id: str = Query(..., min_length=1, max_length=128),
) -> AnalysisResponse:
    sandbox = _get_sandbox(session_id)
    sample_path = Path("data/sample/sales_sample.csv")
    sandbox.load_dataframe(str(sample_path))
    analysis = analyze_sample_sales_data()
    return analysis


@app.post("/api/reset", tags=["interpreter"])
def api_reset(req: ResetRequest) -> dict[str, str]:
    sessions.pop(req.session_id, None)

    for chart_path in _generated_chart_paths_for_session(req.session_id):
        try:
            chart_path.unlink()
        except OSError as error:
            logger.warning("Unable to remove generated chart %s: %s", chart_path, error)

    return {"status": "reset"}


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health",
    description="Returns a deterministic health response for InsightOps-AI.",
    tags=["health"],
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="insightops-ai")


@app.get(
    "/analysis/sample",
    response_model=AnalysisResponse,
    summary="Analyze sample sales CSV",
    description=(
        "Runs the bundled sample sales CSV through collection metadata, "
        "validation, preparation, security, KPI, anomaly, chart data, "
        "insight, and audit stages."
    ),
    tags=["analysis"],
    responses={500: {"model": ErrorResponse}},
)
def analyze_sample_sales() -> AnalysisResponse:
    try:
        return analyze_sample_sales_data()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@app.post(
    "/analysis/upload",
    response_model=AnalysisResponse,
    summary="Analyze uploaded sales CSV",
    description=(
        "Accepts a CSV upload up to 100 MB via memory-safe chunked streaming "
        "and returns the same typed analysis response contract as sample analysis. "
        "The temporary file is cleaned up after request completion."
    ),
    tags=["analysis"],
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def analyze_uploaded_sales(
    file: UploadFile | None = File(default=None),
) -> AnalysisResponse:
    uploaded_file = await persist_upload_temporarily(file, settings.max_upload_bytes)
    prepared = None
    try:
        prepared = _prepare_csv_or_http_error(uploaded_file.path)
        return _analyze_uploaded_csv(uploaded_file, prepared)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        _cleanup_uploaded_analysis_file(uploaded_file, prepared)


@app.post(
    "/analysis/sample/report",
    summary="Generate sample analysis report",
    description=(
        "Generates a Markdown or PDF executive report from the bundled sample "
        "sales CSV and returns it as a downloadable file."
    ),
    tags=["analysis"],
    responses={
        200: {
            "content": {
                "application/pdf": {},
                "text/markdown": {},
            },
            "description": "Generated report file.",
        },
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def export_sample_report(
    report_format: str = Query(default="pdf", alias="format"),
) -> Response:
    normalized_format = _normalize_report_format_for_request(report_format)
    try:
        analysis = analyze_sample_sales_data()
        return _report_response(analysis, normalized_format)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post(
    "/analysis/upload/report",
    summary="Generate uploaded CSV analysis report",
    description=(
        "Accepts a CSV upload up to 100 MB via memory-safe chunked streaming, "
        "runs the analysis pipeline, and returns a Markdown or PDF executive report "
        "as a downloadable file. Uses the same upload guardrails and unlinks the "
        "temporary file immediately after request completion."
    ),
    tags=["analysis"],
    responses={
        200: {
            "content": {
                "application/pdf": {},
                "text/markdown": {},
            },
            "description": "Generated report file.",
        },
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def export_uploaded_report(
    file: UploadFile | None = File(default=None),
    report_format: str = Query(default="pdf", alias="format"),
) -> Response:
    normalized_format = _normalize_report_format_for_request(report_format)
    uploaded_file = await persist_upload_temporarily(file, settings.max_upload_bytes)
    prepared = None
    try:
        prepared = _prepare_csv_or_http_error(uploaded_file.path)
        analysis = _analyze_uploaded_csv(uploaded_file, prepared)
        return _report_response(analysis, normalized_format)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        _cleanup_uploaded_analysis_file(uploaded_file, prepared)


@app.post(
    "/analysis/upload/preview",
    response_model=CsvUploadPreviewResponse,
    summary="Preview uploaded sales CSV schema",
    description="Inspects the CSV file schema and returns metadata for layout previews.",
    tags=["analysis"],
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
    },
)
async def preview_uploaded_sales(
    file: UploadFile | None = File(default=None),
) -> CsvUploadPreviewResponse:
    uploaded_file = await persist_upload_temporarily(file, settings.max_upload_bytes)
    try:
        inspection = _inspect_csv_or_http_error(uploaded_file.path)

        compatible = inspection.is_canonical or inspection.is_mappable

        return CsvUploadPreviewResponse(
            filename=uploaded_file.original_filename,
            size_bytes=uploaded_file.size_bytes,
            detected_schema=inspection.detected_schema,
            original_headers=inspection.original_headers,
            normalized_headers=inspection.normalized_headers,
            is_canonical=inspection.is_canonical,
            is_mappable=inspection.is_mappable,
            mapped_columns=inspection.mapped_columns,
            missing_required_columns=inspection.missing_required_columns,
            warnings=inspection.warnings,
            compatible=compatible,
            detected_encoding=inspection.detected_encoding,
        )
    finally:
        if uploaded_file.path.exists():
            uploaded_file.path.unlink(missing_ok=True)


def _report_response(
    analysis: AnalysisResponse,
    report_format: str,
) -> Response:
    try:
        report = export_analysis_report(analysis, report_format)
    except UnsupportedReportFormatError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ReportGenerationBlockedError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return Response(
        content=report.content,
        media_type=report.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{report.file_name}"',
            "X-Report-Id": report.report_id,
            "X-Report-Format": report.format,
            "X-Report-Size-Bytes": str(report.size_bytes),
        },
    )


def _unsupported_dataset_file_type_response() -> JSONResponse:
    error = DatasetUploadErrorResponse(
        version="insightops.file-preview.v1",
        status="error",
        error={
            "code": "UNSUPPORTED_FILE_TYPE",
            "message": "Only CSV files are supported.",
            "recoverable": True,
        },
    )
    return JSONResponse(status_code=400, content=error.model_dump())


async def _analysis_run_event_stream(run_id: str) -> AsyncIterator[str]:
    context = analysis_run_contexts.get(run_id)
    if context is None:
        context = RunContext(
            run_id=run_id,
            dataset_id="",
            message="",
            schema=[],
            preview_rows=[],
            conversation_id=f"dataset:{run_id}",
        )

    async for event in runtime_adapter.stream_events(context):
        event_type = event.get("type")
        event_name = "run.artifact" if event_type == "artifact" else event_type
        yield f"event: {event_name}\n"
        yield f"data: {json.dumps(event, separators=(',', ':'))}\n\n"


def _normalize_report_format_for_request(report_format: str) -> str:
    try:
        return normalize_report_format(report_format)
    except UnsupportedReportFormatError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
