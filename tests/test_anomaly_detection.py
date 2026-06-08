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


def test_high_revenue_statistical_outlier_is_detected() -> None:
    result = detect_sales_anomalies(
        [
            _sales_record(order_id="ORD-1", revenue=100.0),
            _sales_record(order_id="ORD-2", revenue=110.0),
            _sales_record(order_id="ORD-3", revenue=120.0),
            _sales_record(order_id="ORD-4", revenue=130.0),
            _sales_record(order_id="ORD-5", revenue=1000.0),
        ]
    )

    anomaly = _anomaly_by_type(result, "iqr_high_revenue")

    assert anomaly.method == "iqr"
    assert anomaly.threshold == 160.0
    assert anomaly.comparison == "value > upper_bound"


def test_high_quantity_statistical_outlier_is_detected() -> None:
    result = detect_sales_anomalies(
        [
            _sales_record(order_id="ORD-1", quantity=1),
            _sales_record(order_id="ORD-2", quantity=2),
            _sales_record(order_id="ORD-3", quantity=3),
            _sales_record(order_id="ORD-4", quantity=4),
            _sales_record(order_id="ORD-5", quantity=50),
        ]
    )

    anomaly = _anomaly_by_type(result, "iqr_high_quantity")

    assert anomaly.method == "iqr"
    assert anomaly.threshold == 7.0


def test_high_discount_statistical_outlier_is_detected() -> None:
    result = detect_sales_anomalies(
        [
            _sales_record(order_id="ORD-1", discount=0.01),
            _sales_record(order_id="ORD-2", discount=0.02),
            _sales_record(order_id="ORD-3", discount=0.03),
            _sales_record(order_id="ORD-4", discount=0.04),
            _sales_record(order_id="ORD-5", discount=0.2),
        ]
    )

    anomaly = _anomaly_by_type(result, "iqr_high_discount")

    assert anomaly.method == "iqr"
    assert anomaly.severity == "high"


def test_segment_relative_product_outlier_is_detected() -> None:
    result = detect_sales_anomalies(
        [
            _sales_record(order_id="ORD-1", product="Analytics Pro", revenue=100.0),
            _sales_record(order_id="ORD-2", product="Analytics Pro", revenue=110.0),
            _sales_record(order_id="ORD-3", product="Analytics Pro", revenue=120.0),
            _sales_record(order_id="ORD-4", product="Analytics Pro", revenue=130.0),
            _sales_record(order_id="ORD-5", product="Analytics Pro", revenue=1000.0),
            _sales_record(order_id="ORD-6", product="Insights Basic", revenue=900.0),
        ]
    )

    anomaly = _anomaly_by_type(result, "product_relative_high_revenue")

    assert anomaly.order_id == "ORD-5"
    assert anomaly.method == "segment_iqr"
    assert anomaly.threshold == 160.0


def test_insufficient_data_does_not_crash_or_add_statistical_anomalies() -> None:
    result = detect_sales_anomalies(
        [
            _sales_record(order_id="ORD-1", revenue=100.0),
            _sales_record(order_id="ORD-2", revenue=200.0),
            _sales_record(order_id="ORD-3", revenue=300.0),
        ]
    )

    assert all(anomaly.method is None for anomaly in result.anomalies)


def test_anomaly_output_order_is_deterministic() -> None:
    result = detect_sales_anomalies(
        [
            _sales_record(order_id="ORD-2", revenue=1000.0),
            _sales_record(order_id="ORD-1", quantity=50, revenue=100.0),
            _sales_record(order_id="ORD-3", revenue=110.0),
            _sales_record(order_id="ORD-4", revenue=120.0),
            _sales_record(order_id="ORD-5", revenue=130.0),
        ]
    )

    assert [
        (anomaly.order_id, anomaly.anomaly_type) for anomaly in result.anomalies
    ] == sorted(
        (anomaly.order_id, anomaly.anomaly_type) for anomaly in result.anomalies
    )


def _sales_record(
    *,
    order_id: str = "ORD-1",
    product: str = "Analytics Pro",
    quantity: int = 1,
    discount: float = 0.0,
    revenue: float = 100.0,
) -> SalesRecord:
    return SalesRecord(
        order_id=order_id,
        order_date=date(2026, 1, 1),
        customer_id="CUST-1",
        region="North",
        product=product,
        sales_rep="Ava Singh",
        quantity=quantity,
        unit_price=100.0,
        discount=discount,
        revenue=revenue,
    )


def _anomaly_by_type(result, anomaly_type: str):
    return next(
        anomaly for anomaly in result.anomalies if anomaly.anomaly_type == anomaly_type
    )
