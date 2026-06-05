from fastapi import FastAPI, HTTPException

from insightops.pipeline.sample_analysis import analyze_sample_sales_data

app = FastAPI(title="InsightOps-AI")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "insightops-ai"}


@app.get("/analysis/sample")
def analyze_sample_sales() -> dict[str, object]:
    try:
        return analyze_sample_sales_data()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error
