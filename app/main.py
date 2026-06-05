from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from insightops.api.contracts import AnalysisResponse, ErrorResponse, HealthResponse
from insightops.pipeline.sample_analysis import (
    analyze_sales_csv_file,
    analyze_sample_sales_data,
)

app = FastAPI(
    title="InsightOps-AI",
    description=(
        "Governed sales analytics API for deterministic validation, KPI "
        "computation, security scanning, anomaly detection, chart data, "
        "executive insights, and audit events."
    ),
    version="0.13.0",
)
MAX_UPLOAD_BYTES = 1_000_000
STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
        "Runs the bundled sample sales CSV through validation, security, "
        "KPI, anomaly, chart data, insight, and audit stages."
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
        "Accepts a CSV upload up to 1 MB and returns the same typed "
        "analysis response contract as sample analysis."
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
    if file is None:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    filename = file.filename or ""
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    if not filename.casefold().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be a CSV file.",
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Uploaded CSV file exceeds the 1 MB size limit.",
        )

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")

    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        return analyze_sales_csv_file(str(temp_path))
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
