from pathlib import Path
from uuid import uuid4

import json
from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from insightops.api.contracts import (
    AnalysisRequest,
    AnalysisRequestResponse,
    AnalysisRunCreatedResponse,
    AnalysisRunCreateRequest,
    AnalysisResponse,
    DatasetUploadErrorResponse,
    DatasetUploadSuccessResponse,
    ErrorResponse,
    HealthResponse,
    CsvUploadPreviewResponse,
    RunCodeEvent,
    RunFinalEvent,
    RunStdoutEvent,
    RunStatusEvent,
)
from insightops.config import load_app_settings
from insightops.validation.schema import (
    CsvSchemaError,
    CsvDecodeError,
    CsvIncompatibleSchemaError,
    inspect_sales_csv_schema,
)
from insightops.io.csv_compatibility import prepare_csv_for_analysis
from insightops.io.dataset_preview import build_dataset_preview, is_supported_csv_upload
from insightops.pipeline.sample_analysis import (
    analyze_sales_csv_file,
    analyze_sample_sales_data,
)
from insightops.io.upload_guardrails import persist_upload_temporarily
from insightops.reports.export_service import (
    ReportGenerationBlockedError,
    UnsupportedReportFormatError,
    export_analysis_report,
    normalize_report_format,
)

import os
from pydantic import BaseModel
from app.interpreter import PythonInterpreterSandbox
from app.chat_agent import ChatAgentCodeGenerator

# Create generated directory for dynamic charts
STATIC_DIR = Path(__file__).parent / "static"
os.makedirs(STATIC_DIR / "generated", exist_ok=True)
DATASET_STORAGE_DIR = STATIC_DIR / "generated" / "datasets"
os.makedirs(DATASET_STORAGE_DIR, exist_ok=True)

sessions: dict[str, PythonInterpreterSandbox] = {}
code_generator = ChatAgentCodeGenerator()


class ChatRequest(BaseModel):
    prompt: str
    session_id: str


class ChatResponse(BaseModel):
    prompt: str
    code: str
    stdout: str
    stderr: str
    error: str | None
    charts: list[str]
    attempts: list[dict]
    code_executed: str


class ExecuteRequest(BaseModel):
    code: str
    session_id: str


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    error: str | None
    charts: list[str]
    attempts: list[dict]
    code_executed: str


class ResetRequest(BaseModel):
    session_id: str


class SaveNotebookRequest(BaseModel):
    session_id: str
    notebook_name: str
    cells: list[dict]


class ScheduleRequest(BaseModel):
    session_id: str
    cron_expression: str
    email: str


settings = load_app_settings()
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
    StaticFiles(directory=STATIC_DIR / "generated"),
    name="static_generated",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.post("/api/chat", response_model=ChatResponse, tags=["interpreter"])
def api_chat(req: ChatRequest) -> ChatResponse:
    sandbox = sessions.setdefault(req.session_id, PythonInterpreterSandbox())

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
    responses={400: {"model": ErrorResponse}},
)
def create_analysis_run(
    request: AnalysisRunCreateRequest,
) -> AnalysisRunCreatedResponse:
    if request.version != "insightops.analysis-run-create.v1":
        raise HTTPException(
            status_code=400,
            detail="Unsupported analysis run create version.",
        )
    if not request.datasetId.strip():
        raise HTTPException(status_code=400, detail="datasetId must be a non-empty string.")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message must be a non-empty string.")

    run_id = uuid4().hex
    return AnalysisRunCreatedResponse(
        version="insightops.analysis-run-created.v1",
        status="created",
        runId=run_id,
        streamUrl=f"/api/analysis/runs/{run_id}/events",
    )


@app.get("/api/analysis/runs/{run_id}/events", tags=["analysis"])
def stream_analysis_run_events(run_id: str) -> StreamingResponse:
    return StreamingResponse(
        _mock_analysis_run_event_stream(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/execute", response_model=ExecuteResponse, tags=["interpreter"])
def api_execute(req: ExecuteRequest) -> ExecuteResponse:
    sandbox = sessions.setdefault(req.session_id, PythonInterpreterSandbox())
    res = sandbox.execute(req.code, req.session_id, prompt="Raw code execution")
    return ExecuteResponse(
        stdout=res["stdout"],
        stderr=res["stderr"],
        error=res["error"],
        charts=res["charts"],
        attempts=res["attempts"],
        code_executed=res["code_executed"],
    )


# Create notebooks folder
os.makedirs(STATIC_DIR / "generated" / "notebooks", exist_ok=True)


@app.post("/api/save_notebook", tags=["interpreter"])
def api_save_notebook(req: SaveNotebookRequest):
    import json

    path = STATIC_DIR / "generated" / "notebooks" / f"{req.session_id}.json"
    data = {
        "session_id": req.session_id,
        "notebook_name": req.notebook_name,
        "cells": req.cells,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {
        "status": "saved",
        "path": f"/static/generated/notebooks/{req.session_id}.json",
    }


@app.get("/api/list_notebooks", tags=["interpreter"])
def api_list_notebooks():
    import glob
    import json

    notebooks = []
    pattern = str(STATIC_DIR / "generated" / "notebooks" / "*.json")
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                notebooks.append(
                    {
                        "session_id": data.get("session_id"),
                        "notebook_name": data.get("notebook_name"),
                        "cell_count": len(data.get("cells", [])),
                    }
                )
        except Exception:
            pass
    return notebooks


@app.get("/api/load_notebook", tags=["interpreter"])
def api_load_notebook(session_id: str = Query(...)):
    import json

    path = STATIC_DIR / "generated" / "notebooks" / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Notebook not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/schedule", tags=["interpreter"])
def api_schedule(req: ScheduleRequest):
    import json

    path = STATIC_DIR / "generated" / "schedules.json"
    schedules = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                schedules = json.load(f)
        except Exception:
            pass
    schedules[req.session_id] = {"cron": req.cron_expression, "email": req.email}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schedules, f, indent=2)
    return {"status": "scheduled"}


@app.post("/api/upload_dataset", tags=["interpreter"])
async def api_upload_dataset(
    session_id: str = Query(...), file: UploadFile | None = File(default=None)
):
    uploaded_file = await persist_upload_temporarily(file, settings.max_upload_bytes)
    prepared = None
    try:
        try:
            prepared = prepare_csv_for_analysis(uploaded_file.path)
        except CsvDecodeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except CsvIncompatibleSchemaError as e:
            detail = (
                f"{str(e)}\n"
                "Supported schemas:\n"
                "- canonical InsightOps sales schema\n"
                "- classic_sales_sample mapping"
            )
            raise HTTPException(status_code=400, detail=detail)
        except CsvSchemaError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Initialize sandbox and pre-load dataframe
        sandbox = sessions.setdefault(session_id, PythonInterpreterSandbox())
        sandbox.load_dataframe(str(prepared.analysis_path))

        # Run standard validation pipeline
        analysis = analyze_sales_csv_file(
            str(prepared.analysis_path),
            uploaded_file_name=uploaded_file.original_filename,
            uploaded_file_size_bytes=uploaded_file.size_bytes,
        )
        if prepared.was_mapped:
            warnings_str = "; ".join(prepared.warnings)
            analysis.source_metadata.notes = f"Schema mapped from {prepared.detected_schema}. Warnings: {warnings_str}"
        return analysis
    finally:
        if prepared and prepared.was_mapped and prepared.analysis_path.exists():
            prepared.analysis_path.unlink(missing_ok=True)
        if uploaded_file.path.exists():
            uploaded_file.path.unlink(missing_ok=True)


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
        dataset = build_dataset_preview(
            uploaded_file.path,
            original_filename=uploaded_file.original_filename,
            size_bytes=uploaded_file.size_bytes,
            storage_dir=DATASET_STORAGE_DIR,
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


@app.post("/api/sample_dataset", tags=["interpreter"])
def api_sample_dataset(session_id: str = Query(...)):
    sandbox = sessions.setdefault(session_id, PythonInterpreterSandbox())
    sample_path = Path("data/sample/sales_sample.csv")
    sandbox.load_dataframe(str(sample_path))
    analysis = analyze_sample_sales_data()
    return analysis


@app.post("/api/reset", tags=["interpreter"])
def api_reset(req: ResetRequest):
    if req.session_id in sessions:
        del sessions[req.session_id]

    # Also clean up generated charts for this session
    import glob

    for f in glob.glob(f"app/static/generated/chart_{req.session_id}_*.png"):
        try:
            os.remove(f)
        except OSError:
            pass

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
        try:
            prepared = prepare_csv_for_analysis(uploaded_file.path)
        except CsvDecodeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except CsvIncompatibleSchemaError as e:
            detail = (
                f"{str(e)}\n"
                "Supported schemas:\n"
                "- canonical InsightOps sales schema\n"
                "- classic_sales_sample mapping"
            )
            raise HTTPException(status_code=400, detail=detail)
        except CsvSchemaError as e:
            raise HTTPException(status_code=400, detail=str(e))

        analysis = analyze_sales_csv_file(
            str(prepared.analysis_path),
            uploaded_file_name=uploaded_file.original_filename,
            uploaded_file_size_bytes=uploaded_file.size_bytes,
        )
        if prepared.was_mapped:
            warnings_str = "; ".join(prepared.warnings)
            analysis.source_metadata.notes = f"Schema mapped from {prepared.detected_schema}. Warnings: {warnings_str}"
        return analysis
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        if prepared and prepared.was_mapped and prepared.analysis_path.exists():
            prepared.analysis_path.unlink(missing_ok=True)
        if uploaded_file.path.exists():
            uploaded_file.path.unlink(missing_ok=True)


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
        try:
            prepared = prepare_csv_for_analysis(uploaded_file.path)
        except CsvDecodeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except CsvIncompatibleSchemaError as e:
            detail = (
                f"{str(e)}\n"
                "Supported schemas:\n"
                "- canonical InsightOps sales schema\n"
                "- classic_sales_sample mapping"
            )
            raise HTTPException(status_code=400, detail=detail)
        except CsvSchemaError as e:
            raise HTTPException(status_code=400, detail=str(e))

        analysis = analyze_sales_csv_file(
            str(prepared.analysis_path),
            uploaded_file_name=uploaded_file.original_filename,
            uploaded_file_size_bytes=uploaded_file.size_bytes,
        )
        if prepared.was_mapped:
            warnings_str = "; ".join(prepared.warnings)
            analysis.source_metadata.notes = f"Schema mapped from {prepared.detected_schema}. Warnings: {warnings_str}"
        return _report_response(analysis, normalized_format)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        if prepared and prepared.was_mapped and prepared.analysis_path.exists():
            prepared.analysis_path.unlink(missing_ok=True)
        if uploaded_file.path.exists():
            uploaded_file.path.unlink(missing_ok=True)


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
        try:
            inspection = inspect_sales_csv_schema(uploaded_file.path)
        except CsvDecodeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except CsvSchemaError as e:
            raise HTTPException(status_code=400, detail=str(e))

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


def _mock_analysis_run_event_stream(run_id: str):
    events = [
        RunStatusEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=1,
            type="run.status",
            status="agent_planning",
        ),
        RunCodeEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=2,
            type="run.code",
            language="python",
            code=(
                "import pandas as pd\n"
                "# Mock deterministic analysis plan only; no code was executed.\n"
                "print('Preparing dataset profile...')"
            ),
        ),
        RunStdoutEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=3,
            type="run.stdout",
            stdout="Mock stdout: dataset preview received; execution runtime not connected.",
        ),
        RunStatusEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=4,
            type="run.status",
            status="rendering_view",
        ),
        RunFinalEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=5,
            type="run.final",
            assistantMessage=(
                "Deterministic mock analysis complete. Streaming execution events "
                "are connected; real sandbox execution will arrive in a later milestone."
            ),
        ),
    ]

    for event in events:
        yield f"event: {event.type}\n"
        yield f"data: {json.dumps(event.model_dump(), separators=(',', ':'))}\n\n"


def _normalize_report_format_for_request(report_format: str) -> str:
    try:
        return normalize_report_format(report_format)
    except UnsupportedReportFormatError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
