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
