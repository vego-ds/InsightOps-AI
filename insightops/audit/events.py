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
