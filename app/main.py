from pathlib import Path

from fastapi import FastAPI, HTTPException

from insightops.ingestion.csv_loader import load_sales_csv
from insightops.metrics.kpis import compute_sales_kpis

app = FastAPI(title="InsightOps-AI")
SAMPLE_SALES_CSV = Path("data/sample/sales_sample.csv")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "insightops-ai"}


@app.get("/analysis/sample")
def analyze_sample_sales() -> dict[str, object]:
    if not SAMPLE_SALES_CSV.exists():
        raise HTTPException(
            status_code=500,
            detail="Sample sales CSV file is missing.",
        )

    validation_report = load_sales_csv(str(SAMPLE_SALES_CSV))
    kpis = compute_sales_kpis(validation_report.records)

    return {
        "validation": {
            "total_rows": validation_report.total_rows,
            "valid_rows": validation_report.valid_rows,
            "invalid_rows": validation_report.invalid_rows,
            "errors": [
                error.model_dump() for error in validation_report.errors
            ],
        },
        "kpis": kpis.model_dump(),
    }
