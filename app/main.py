from fastapi import FastAPI

app = FastAPI(title="InsightOps-AI")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "insightops-ai"}
