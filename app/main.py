from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from insightops.api.contracts import AnalysisResponse, ErrorResponse, HealthResponse
from insightops.config import load_app_settings
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
    try:
        # Initialize sandbox and pre-load dataframe
        sandbox = sessions.setdefault(session_id, PythonInterpreterSandbox())
        sandbox.load_dataframe(str(uploaded_file.path))

        # Run standard validation pipeline
        analysis = analyze_sales_csv_file(
            str(uploaded_file.path),
            uploaded_file_name=uploaded_file.original_filename,
            uploaded_file_size_bytes=uploaded_file.size_bytes,
        )
        return analysis
    finally:
        if uploaded_file.path.exists():
            uploaded_file.path.unlink(missing_ok=True)


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
    try:
        return analyze_sales_csv_file(
            str(uploaded_file.path),
            uploaded_file_name=uploaded_file.original_filename,
            uploaded_file_size_bytes=uploaded_file.size_bytes,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
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
    try:
        analysis = analyze_sales_csv_file(
            str(uploaded_file.path),
            uploaded_file_name=uploaded_file.original_filename,
            uploaded_file_size_bytes=uploaded_file.size_bytes,
        )
        return _report_response(analysis, normalized_format)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
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


def _normalize_report_format_for_request(report_format: str) -> str:
    try:
        return normalize_report_format(report_format)
    except UnsupportedReportFormatError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
