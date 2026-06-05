from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile

from insightops.api.contracts import AnalysisResponse
from insightops.pipeline.sample_analysis import (
    analyze_sales_csv_file,
    analyze_sample_sales_data,
)

app = FastAPI(title="InsightOps-AI")
MAX_UPLOAD_BYTES = 1_000_000


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "insightops-ai"}


@app.get("/analysis/sample", response_model=AnalysisResponse)
def analyze_sample_sales() -> AnalysisResponse:
    try:
        return analyze_sample_sales_data()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@app.post("/analysis/upload", response_model=AnalysisResponse)
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
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV file.")

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
