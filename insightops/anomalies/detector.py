from pydantic import BaseModel, Field

from insightops.statistics.outliers import calculate_iqr_bounds
from insightops.validation.models import SalesRecord


class SalesAnomaly(BaseModel):
    anomaly_type: str
    severity: str
    order_id: str
    field: str
    value: float | int | str
    message: str
    method: str | None = None
    threshold: float | None = None
    comparison: str | None = None


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

    anomalies.extend(_detect_iqr_high_revenue(records))
    anomalies.extend(_detect_iqr_high_quantity(records))
    anomalies.extend(_detect_iqr_high_discount(records))
    anomalies.extend(_detect_product_relative_high_revenue(records))
    anomalies = _deduplicate_anomalies(anomalies)
    anomalies = sorted(
        anomalies,
        key=lambda anomaly: (
            anomaly.order_id,
            anomaly.anomaly_type,
            anomaly.field,
        ),
    )

    return AnomalyDetectionResult(
        total_anomalies=len(anomalies),
        anomalies=anomalies,
    )


def _detect_iqr_high_revenue(records: list[SalesRecord]) -> list[SalesAnomaly]:
    bounds = calculate_iqr_bounds([record.revenue for record in records])
    if bounds is None:
        return []

    return [
        SalesAnomaly(
            anomaly_type="iqr_high_revenue",
            severity="medium",
            order_id=record.order_id,
            field="revenue",
            value=record.revenue,
            message="Revenue is above the IQR upper bound.",
            method="iqr",
            threshold=bounds.upper_bound,
            comparison="value > upper_bound",
        )
        for record in records
        if record.revenue > bounds.upper_bound
    ]


def _detect_iqr_high_quantity(records: list[SalesRecord]) -> list[SalesAnomaly]:
    bounds = calculate_iqr_bounds([float(record.quantity) for record in records])
    if bounds is None:
        return []

    return [
        SalesAnomaly(
            anomaly_type="iqr_high_quantity",
            severity="medium",
            order_id=record.order_id,
            field="quantity",
            value=record.quantity,
            message="Quantity is above the IQR upper bound.",
            method="iqr",
            threshold=bounds.upper_bound,
            comparison="value > upper_bound",
        )
        for record in records
        if record.quantity > bounds.upper_bound
    ]


def _detect_iqr_high_discount(records: list[SalesRecord]) -> list[SalesAnomaly]:
    bounds = calculate_iqr_bounds([record.discount for record in records])
    if bounds is None:
        return []

    return [
        SalesAnomaly(
            anomaly_type="iqr_high_discount",
            severity="high",
            order_id=record.order_id,
            field="discount",
            value=record.discount,
            message="Discount is above the IQR upper bound.",
            method="iqr",
            threshold=bounds.upper_bound,
            comparison="value > upper_bound",
        )
        for record in records
        if record.discount > bounds.upper_bound
    ]


def _detect_product_relative_high_revenue(
    records: list[SalesRecord],
) -> list[SalesAnomaly]:
    records_by_product: dict[str, list[SalesRecord]] = {}
    for record in records:
        records_by_product.setdefault(record.product, []).append(record)

    anomalies: list[SalesAnomaly] = []
    for product, product_records in sorted(records_by_product.items()):
        bounds = calculate_iqr_bounds([record.revenue for record in product_records])
        if bounds is None:
            continue

        anomalies.extend(
            SalesAnomaly(
                anomaly_type="product_relative_high_revenue",
                severity="medium",
                order_id=record.order_id,
                field="revenue",
                value=record.revenue,
                message=(
                    f"Revenue is above the product-level IQR upper bound for {product}."
                ),
                method="segment_iqr",
                threshold=bounds.upper_bound,
                comparison="value > product_upper_bound",
            )
            for record in product_records
            if record.revenue > bounds.upper_bound
        )

    return anomalies


def _deduplicate_anomalies(
    anomalies: list[SalesAnomaly],
) -> list[SalesAnomaly]:
    unique: list[SalesAnomaly] = []
    seen: set[tuple] = set()

    for anomaly in anomalies:
        key = (
            anomaly.anomaly_type,
            anomaly.severity,
            anomaly.order_id,
            anomaly.field,
            anomaly.value,
            anomaly.method,
            anomaly.threshold,
            anomaly.comparison,
        )
        if key not in seen:
            seen.add(key)
            unique.append(anomaly)

    return unique
