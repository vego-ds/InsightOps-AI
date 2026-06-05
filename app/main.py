from pathlib import Path

from fastapi import FastAPI, HTTPException

from insightops.anomalies.detector import detect_sales_anomalies
from insightops.audit.events import (
    create_anomaly_detection_completed_event,
    create_chart_data_generated_event,
    create_csv_loaded_event,
    create_insights_generated_event,
    create_kpi_computed_event,
    create_security_scan_completed_event,
    create_validation_completed_event,
)
from insightops.charts.chart_data import build_sales_chart_data
from insightops.ingestion.csv_loader import load_sales_csv
from insightops.insights.generator import generate_executive_insights
from insightops.metrics.kpis import compute_sales_kpis
from insightops.security.policy import scan_sales_records_for_security

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
    security = scan_sales_records_for_security(validation_report.records)
    kpis = compute_sales_kpis(validation_report.records)
    anomalies = detect_sales_anomalies(validation_report.records)
    charts = build_sales_chart_data(kpis, anomalies)
    insights = generate_executive_insights(
        validation_report,
        kpis,
        anomalies,
        security,
    )
    audit_events = [
        create_csv_loaded_event(validation_report.total_rows),
        create_validation_completed_event(
            validation_report.valid_rows,
            validation_report.invalid_rows,
        ),
        create_kpi_computed_event(kpis.total_orders, kpis.total_revenue),
        create_security_scan_completed_event(
            security.prompt_injection_detected,
            security.human_review_required,
        ),
        create_anomaly_detection_completed_event(
            anomalies.total_anomalies,
        ),
        create_chart_data_generated_event(len(charts.charts)),
        create_insights_generated_event(len(insights.insights)),
    ]

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
        "security": security.model_dump(),
        "anomalies": anomalies.model_dump(),
        "charts": charts.model_dump(),
        "insights": insights.model_dump(),
        "audit_events": [event.model_dump() for event in audit_events],
    }
