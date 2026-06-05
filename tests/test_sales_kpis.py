from datetime import date

from insightops.metrics.kpis import compute_sales_kpis
from insightops.validation.models import SalesRecord


def test_compute_sales_kpis_returns_core_metrics() -> None:
    records = [
        SalesRecord(
            order_id="ORD-1",
            order_date=date(2026, 1, 1),
            customer_id="CUST-1",
            region="North",
            product="Analytics Pro",
            sales_rep="Ava Singh",
            quantity=2,
            unit_price=100.0,
            discount=0.0,
            revenue=200.0,
        ),
        SalesRecord(
            order_id="ORD-2",
            order_date=date(2026, 1, 2),
            customer_id="CUST-2",
            region="North",
            product="Insights Basic",
            sales_rep="Noah Chen",
            quantity=1,
            unit_price=150.0,
            discount=0.0,
            revenue=150.0,
        ),
        SalesRecord(
            order_id="ORD-3",
            order_date=date(2026, 1, 3),
            customer_id="CUST-3",
            region="West",
            product="Analytics Pro",
            sales_rep="Ava Singh",
            quantity=3,
            unit_price=50.0,
            discount=0.0,
            revenue=150.0,
        ),
    ]

    result = compute_sales_kpis(records)

    assert result.total_revenue == 500.0
    assert result.total_orders == 3
    assert result.total_units_sold == 6
    assert result.average_order_value == 166.67
    assert result.revenue_by_region == {"North": 350.0, "West": 150.0}
    assert result.revenue_by_product == {
        "Analytics Pro": 350.0,
        "Insights Basic": 150.0,
    }
    assert result.revenue_by_sales_rep == {
        "Ava Singh": 350.0,
        "Noah Chen": 150.0,
    }


def test_compute_sales_kpis_empty_input_returns_safe_zero_values() -> None:
    result = compute_sales_kpis([])

    assert result.total_revenue == 0.0
    assert result.total_orders == 0
    assert result.total_units_sold == 0
    assert result.average_order_value == 0.0
    assert result.revenue_by_region == {}
    assert result.revenue_by_product == {}
    assert result.revenue_by_sales_rep == {}
