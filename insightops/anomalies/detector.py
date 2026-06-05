from pydantic import BaseModel, Field

from insightops.validation.models import SalesRecord


class SalesAnomaly(BaseModel):
    anomaly_type: str
    severity: str
    order_id: str
    field: str
    value: float | int | str
    message: str


class AnomalyDetectionResult(BaseModel):
    total_anomalies: int
    anomalies: list[SalesAnomaly] = Field(default_factory=list)


def detect_sales_anomalies(
    records: list[SalesRecord],
) -> AnomalyDetectionResult:
    anomalies: list[SalesAnomaly] = []

    for record in records:
        if record.revenue >= 5000:
            anomalies.append(
                SalesAnomaly(
                    anomaly_type="high_revenue",
                    severity="medium",
                    order_id=record.order_id,
                    field="revenue",
                    value=record.revenue,
                    message="Revenue is unusually high.",
                )
            )

        if record.quantity >= 50:
            anomalies.append(
                SalesAnomaly(
                    anomaly_type="high_quantity",
                    severity="medium",
                    order_id=record.order_id,
                    field="quantity",
                    value=record.quantity,
                    message="Quantity is unusually high.",
                )
            )

        if record.discount >= 0.5:
            anomalies.append(
                SalesAnomaly(
                    anomaly_type="high_discount",
                    severity="high",
                    order_id=record.order_id,
                    field="discount",
                    value=record.discount,
                    message="Discount is unusually high.",
                )
            )

        if record.revenue == 0:
            anomalies.append(
                SalesAnomaly(
                    anomaly_type="zero_revenue",
                    severity="high",
                    order_id=record.order_id,
                    field="revenue",
                    value=record.revenue,
                    message="Revenue is zero.",
                )
            )

    return AnomalyDetectionResult(
        total_anomalies=len(anomalies),
        anomalies=anomalies,
    )
