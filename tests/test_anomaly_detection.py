from datetime import date

from insightops.anomalies.detector import detect_sales_anomalies
from insightops.validation.models import SalesRecord


def test_empty_input_returns_zero_anomalies() -> None:
    result = detect_sales_anomalies([])

    assert result.total_anomalies == 0
    assert result.anomalies == []


def test_high_revenue_is_detected() -> None:
    result = detect_sales_anomalies([_sales_record(revenue=5000.0)])

    assert result.total_anomalies == 1
    assert result.anomalies[0].anomaly_type == "high_revenue"
    assert result.anomalies[0].severity == "medium"


def test_high_quantity_is_detected() -> None:
    result = detect_sales_anomalies([_sales_record(quantity=50)])

    assert result.total_anomalies == 1
    assert result.anomalies[0].anomaly_type == "high_quantity"
    assert result.anomalies[0].severity == "medium"


def test_high_discount_is_detected() -> None:
    result = detect_sales_anomalies([_sales_record(discount=0.5)])

    assert result.total_anomalies == 1
    assert result.anomalies[0].anomaly_type == "high_discount"
    assert result.anomalies[0].severity == "high"


def test_zero_revenue_is_detected() -> None:
    result = detect_sales_anomalies([_sales_record(revenue=0.0)])

    assert result.total_anomalies == 1
    assert result.anomalies[0].anomaly_type == "zero_revenue"
    assert result.anomalies[0].severity == "high"


def test_one_record_can_produce_multiple_anomalies() -> None:
    result = detect_sales_anomalies(
        [
            _sales_record(
                quantity=50,
                discount=0.5,
                revenue=5000.0,
            )
        ]
    )

    anomaly_types = {anomaly.anomaly_type for anomaly in result.anomalies}

    assert result.total_anomalies == 3
    assert anomaly_types == {
        "high_revenue",
        "high_quantity",
        "high_discount",
    }


def _sales_record(
    *,
    quantity: int = 1,
    discount: float = 0.0,
    revenue: float = 100.0,
) -> SalesRecord:
    return SalesRecord(
        order_id="ORD-1",
        order_date=date(2026, 1, 1),
        customer_id="CUST-1",
        region="North",
        product="Analytics Pro",
        sales_rep="Ava Singh",
        quantity=quantity,
        unit_price=100.0,
        discount=discount,
        revenue=revenue,
    )
