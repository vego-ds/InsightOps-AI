from pathlib import Path

from insightops.anomalies.detector import detect_sales_anomalies
from insightops.audit.events import (
    create_anomaly_detection_completed_event,
    create_chart_data_generated_event,
    create_csv_loaded_event,
    create_data_profile_generated_event,
    create_data_preparation_completed_event,
    create_insights_generated_event,
    create_kpi_computed_event,
    create_manipulation_summary_generated_event,
    create_quality_gate_evaluated_event,
    create_quality_score_generated_event,
    create_recommendations_generated_event,
    create_security_scan_completed_event,
    create_source_metadata_collected_event,
    create_transformation_log_generated_event,
    create_trend_analysis_completed_event,
    create_validation_completed_event,
    create_workflow_improvements_generated_event,
)
from insightops.api.contracts import AnalysisResponse
from insightops.charts.chart_data import build_sales_chart_data
from insightops.governance.quality_gate import evaluate_quality_gate
from insightops.ingestion.csv_loader import load_sales_csv
from insightops.insights.generator import generate_executive_insights
from insightops.metrics.kpis import compute_sales_kpis
from insightops.preparation.manipulations import build_manipulation_summary
from insightops.preparation.transformations import prepare_sales_records
from insightops.profiling.data_profile import build_sales_data_profile
from insightops.profiling.quality_score import compute_data_quality_score
from insightops.recommendations.action_plan import generate_recommendation_plan
from insightops.recommendations.workflow_improvements import (
    generate_workflow_improvement_plan,
)
from insightops.security.policy import scan_sales_records_for_security
from insightops.sources.source_metadata import (
    DatasetSourceMetadata,
    create_sample_source_metadata,
    create_uploaded_source_metadata,
)
from insightops.trends.time_series import analyze_time_series_trends

SAMPLE_SALES_CSV = Path("data/sample/sales_sample.csv")


def analyze_sales_csv_file(
    path: str,
    *,
    uploaded_file_name: str | None = None,
    uploaded_file_size_bytes: int | None = None,
) -> AnalysisResponse:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError("Sales CSV file is missing.")

    validation_report = load_sales_csv(str(csv_path))
    source_metadata = _create_source_metadata(
        csv_path,
        validation_report.total_rows,
        uploaded_file_name,
        uploaded_file_size_bytes,
    )
    data_profile = build_sales_data_profile(validation_report)
    quality_score = compute_data_quality_score(data_profile)
    security = scan_sales_records_for_security(validation_report.records)
    quality_gate = evaluate_quality_gate(
        validation_report,
        data_profile,
        quality_score,
        security,
    )
    preparation, transformation_log = prepare_sales_records(
        validation_report.records
    )
    manipulation_summary = build_manipulation_summary(preparation)
    trend_analysis = analyze_time_series_trends(preparation)
    kpis = compute_sales_kpis(validation_report.records)
    anomalies = detect_sales_anomalies(validation_report.records)
    insights = generate_executive_insights(
        validation_report,
        kpis,
        anomalies,
        security,
        data_profile,
        quality_score,
        quality_gate,
        preparation,
        manipulation_summary,
        trend_analysis,
    )
    charts = build_sales_chart_data(
        kpis,
        anomalies,
        quality_score,
        manipulation_summary,
        insights,
        trend_analysis,
    )
    recommendation_plan = generate_recommendation_plan(
        _analysis_without_recommendations(
            source_metadata=source_metadata,
            validation_report=validation_report,
            data_profile=data_profile,
            quality_score=quality_score,
            quality_gate=quality_gate,
            preparation=preparation,
            transformation_log=transformation_log,
            manipulation_summary=manipulation_summary,
            trend_analysis=trend_analysis,
            kpis=kpis,
            security=security,
            anomalies=anomalies,
            charts=charts,
            insights=insights,
        )
    )
    workflow_improvement_plan = generate_workflow_improvement_plan(
        recommendation_plan
    )
    audit_events = [
        create_source_metadata_collected_event(
            source_metadata.source_type,
            source_metadata.record_count,
        ),
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
        create_quality_gate_evaluated_event(
            quality_gate.status,
            quality_gate.confidence_level,
        ),
        create_data_preparation_completed_event(preparation.total_records),
        create_transformation_log_generated_event(
            len(transformation_log.entries),
        ),
        create_manipulation_summary_generated_event(),
        create_trend_analysis_completed_event(trend_analysis.total_periods),
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
        create_recommendations_generated_event(
            recommendation_plan.total_recommendations,
        ),
        create_workflow_improvements_generated_event(
            workflow_improvement_plan.total_workflows,
        ),
    ]

    return AnalysisResponse(
        source_metadata=source_metadata,
        validation=validation_report,
        data_profile=data_profile,
        quality_score=quality_score,
        quality_gate=quality_gate,
        preparation=preparation,
        transformation_log=transformation_log,
        manipulation_summary=manipulation_summary,
        trend_analysis=trend_analysis,
        kpis=kpis,
        security=security,
        anomalies=anomalies,
        charts=charts,
        insights=insights,
        recommendation_plan=recommendation_plan,
        workflow_improvement_plan=workflow_improvement_plan,
        audit_events=audit_events,
    )


def analyze_sample_sales_data() -> AnalysisResponse:
    if not SAMPLE_SALES_CSV.exists():
        raise FileNotFoundError("Sample sales CSV file is missing.")

    return analyze_sales_csv_file(str(SAMPLE_SALES_CSV))


def _create_source_metadata(
    csv_path: Path,
    record_count: int,
    uploaded_file_name: str | None,
    uploaded_file_size_bytes: int | None,
) -> DatasetSourceMetadata:
    if uploaded_file_name is not None and uploaded_file_size_bytes is not None:
        return create_uploaded_source_metadata(
            uploaded_file_name,
            uploaded_file_size_bytes,
            record_count,
        )

    return create_sample_source_metadata(str(csv_path), record_count)


def _analysis_without_recommendations(
    *,
    source_metadata,
    validation_report,
    data_profile,
    quality_score,
    quality_gate,
    preparation,
    transformation_log,
    manipulation_summary,
    trend_analysis,
    kpis,
    security,
    anomalies,
    charts,
    insights,
) -> AnalysisResponse:
    from insightops.recommendations.action_plan import RecommendationPlan
    from insightops.recommendations.workflow_improvements import (
        WorkflowImprovementPlan,
    )

    return AnalysisResponse(
        source_metadata=source_metadata,
        validation=validation_report,
        data_profile=data_profile,
        quality_score=quality_score,
        quality_gate=quality_gate,
        preparation=preparation,
        transformation_log=transformation_log,
        manipulation_summary=manipulation_summary,
        trend_analysis=trend_analysis,
        kpis=kpis,
        security=security,
        anomalies=anomalies,
        charts=charts,
        insights=insights,
        recommendation_plan=RecommendationPlan(
            total_recommendations=0,
            recommendations=[],
        ),
        workflow_improvement_plan=WorkflowImprovementPlan(
            total_workflows=0,
            workflows=[],
        ),
        audit_events=[],
    )
