from pydantic import BaseModel, Field

AuditMetadataValue = str | int | float | bool


class AuditEvent(BaseModel):
    event_type: str
    message: str
    metadata: dict[str, AuditMetadataValue] = Field(default_factory=dict)


def create_csv_loaded_event(total_rows: int) -> AuditEvent:
    return AuditEvent(
        event_type="csv_loaded",
        message="Sales CSV loaded.",
        metadata={"total_rows": total_rows},
    )


def create_source_metadata_collected_event(
    source_type: str,
    record_count: int,
) -> AuditEvent:
    return AuditEvent(
        event_type="source_metadata_collected",
        message="Dataset source metadata collected.",
        metadata={"source_type": source_type, "record_count": record_count},
    )


def create_validation_completed_event(
    valid_rows: int,
    invalid_rows: int,
) -> AuditEvent:
    return AuditEvent(
        event_type="validation_completed",
        message="Sales CSV validation completed.",
        metadata={"valid_rows": valid_rows, "invalid_rows": invalid_rows},
    )


def create_data_profile_generated_event() -> AuditEvent:
    return AuditEvent(
        event_type="data_profile_generated",
        message="Sales data profile generated.",
        metadata={},
    )


def create_quality_score_generated_event(
    score: int,
    grade: str,
) -> AuditEvent:
    return AuditEvent(
        event_type="quality_score_generated",
        message="Sales data quality score generated.",
        metadata={"score": score, "grade": grade},
    )


def create_quality_gate_evaluated_event(
    status: str,
    confidence_level: str,
) -> AuditEvent:
    return AuditEvent(
        event_type="quality_gate_evaluated",
        message="Data quality gate evaluated.",
        metadata={"status": status, "confidence_level": confidence_level},
    )


def create_data_preparation_completed_event(total_records: int) -> AuditEvent:
    return AuditEvent(
        event_type="data_preparation_completed",
        message="Sales data preparation completed.",
        metadata={"total_records": total_records},
    )


def create_transformation_log_generated_event(total_steps: int) -> AuditEvent:
    return AuditEvent(
        event_type="transformation_log_generated",
        message="Sales transformation lineage generated.",
        metadata={"total_steps": total_steps},
    )


def create_manipulation_summary_generated_event() -> AuditEvent:
    return AuditEvent(
        event_type="manipulation_summary_generated",
        message="Sales manipulation summary generated.",
        metadata={},
    )


def create_trend_analysis_completed_event(total_periods: int) -> AuditEvent:
    return AuditEvent(
        event_type="trend_analysis_completed",
        message="Sales trend analysis completed.",
        metadata={"total_periods": total_periods},
    )


def create_forecast_analysis_completed_event(
    readiness_status: str,
    confidence_level: str,
) -> AuditEvent:
    return AuditEvent(
        event_type="forecast_analysis_completed",
        message="Sales forecast analysis completed.",
        metadata={
            "readiness_status": readiness_status,
            "confidence_level": confidence_level,
        },
    )


def create_kpi_computed_event(
    total_orders: int,
    total_revenue: float,
) -> AuditEvent:
    return AuditEvent(
        event_type="kpi_computed",
        message="Sales KPIs computed.",
        metadata={
            "total_orders": total_orders,
            "total_revenue": total_revenue,
        },
    )


def create_security_scan_completed_event(
    prompt_injection_detected: bool,
    human_review_required: bool,
) -> AuditEvent:
    return AuditEvent(
        event_type="security_scan_completed",
        message="Sales records security scan completed.",
        metadata={
            "prompt_injection_detected": prompt_injection_detected,
            "human_review_required": human_review_required,
        },
    )


def create_anomaly_detection_completed_event(
    total_anomalies: int,
) -> AuditEvent:
    return AuditEvent(
        event_type="anomaly_detection_completed",
        message="Sales anomaly detection completed.",
        metadata={"total_anomalies": total_anomalies},
    )


def create_chart_data_generated_event(total_charts: int) -> AuditEvent:
    return AuditEvent(
        event_type="chart_data_generated",
        message="Sales chart data generated.",
        metadata={"total_charts": total_charts},
    )


def create_chart_artifacts_generated_event(total_artifacts: int) -> AuditEvent:
    return AuditEvent(
        event_type="chart_artifacts_generated",
        message="Sales chart artifacts generated.",
        metadata={"total_artifacts": total_artifacts},
    )


def create_insights_generated_event(total_insights: int) -> AuditEvent:
    return AuditEvent(
        event_type="insights_generated",
        message="Executive insights generated.",
        metadata={"total_insights": total_insights},
    )


def create_recommendations_generated_event(
    total_recommendations: int,
) -> AuditEvent:
    return AuditEvent(
        event_type="recommendations_generated",
        message="Business recommendations generated.",
        metadata={"total_recommendations": total_recommendations},
    )


def create_workflow_improvements_generated_event(
    total_workflows: int,
) -> AuditEvent:
    return AuditEvent(
        event_type="workflow_improvements_generated",
        message="Workflow improvements generated.",
        metadata={"total_workflows": total_workflows},
    )


def create_report_generated_event(
    report_id: str,
    file_name: str,
) -> AuditEvent:
    return AuditEvent(
        event_type="report_generated",
        message="Executive Markdown report generated.",
        metadata={"report_id": report_id, "file_name": file_name},
    )


def create_pdf_report_generated_event(
    report_id: str,
    file_name: str,
) -> AuditEvent:
    return AuditEvent(
        event_type="pdf_report_generated",
        message="Executive PDF report generated.",
        metadata={"report_id": report_id, "file_name": file_name},
    )


def create_narrative_generated_event(mode: str) -> AuditEvent:
    return AuditEvent(
        event_type="narrative_generated",
        message="Executive narrative generated.",
        metadata={"mode": mode},
    )
