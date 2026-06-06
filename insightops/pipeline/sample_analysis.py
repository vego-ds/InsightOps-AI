from pathlib import Path

from insightops.anomalies.detector import detect_sales_anomalies
from insightops.audit.events import (
    create_anomaly_detection_completed_event,
    create_chart_data_generated_event,
    create_csv_loaded_event,
    create_data_profile_generated_event,
    create_insights_generated_event,
    create_kpi_computed_event,
    create_quality_score_generated_event,
    create_security_scan_completed_event,
    create_validation_completed_event,
)
from insightops.api.contracts import AnalysisResponse
from insightops.charts.chart_data import build_sales_chart_data
from insightops.ingestion.csv_loader import load_sales_csv
from insightops.insights.generator import generate_executive_insights
from insightops.metrics.kpis import compute_sales_kpis
from insightops.profiling.data_profile import build_sales_data_profile
from insightops.profiling.quality_score import compute_data_quality_score
from insightops.security.policy import scan_sales_records_for_security

SAMPLE_SALES_CSV = Path("data/sample/sales_sample.csv")


def analyze_sales_csv_file(path: str) -> AnalysisResponse:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError("Sales CSV file is missing.")

    validation_report = load_sales_csv(str(csv_path))
    data_profile = build_sales_data_profile(validation_report)
    quality_score = compute_data_quality_score(data_profile)
    security = scan_sales_records_for_security(validation_report.records)
    kpis = compute_sales_kpis(validation_report.records)
    anomalies = detect_sales_anomalies(validation_report.records)
    charts = build_sales_chart_data(kpis, anomalies)
    insights = generate_executive_insights(
        validation_report,
        kpis,
        anomalies,
        security,
        data_profile,
        quality_score,
    )
    audit_events = [
        create_csv_loaded_event(validation_report.total_rows),
        create_validation_completed_event(
            validation_report.valid_rows,
            validation_report.invalid_rows,
        ),
        create_data_profile_generated_event(),
        create_quality_score_generated_event(
            quality_score.score,
            quality_score.grade,
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

    return AnalysisResponse(
        validation=validation_report,
        data_profile=data_profile,
        quality_score=quality_score,
        kpis=kpis,
        security=security,
        anomalies=anomalies,
        charts=charts,
        insights=insights,
        audit_events=audit_events,
    )


def analyze_sample_sales_data() -> AnalysisResponse:
    if not SAMPLE_SALES_CSV.exists():
        raise FileNotFoundError("Sample sales CSV file is missing.")

    return analyze_sales_csv_file(str(SAMPLE_SALES_CSV))
