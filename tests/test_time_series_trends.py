from datetime import date

from insightops.preparation.prepared_dataset import (
    PreparedSalesDataset,
    PreparedSalesRecord,
)
from insightops.trends.time_series import (
    TimeSeriesTrendAnalysis,
    analyze_time_series_trends,
)


def test_empty_dataset_returns_insufficient_data_trends() -> None:
    analysis = analyze_time_series_trends(
        PreparedSalesDataset(records=[], total_records=0)
    )

    assert isinstance(analysis, TimeSeriesTrendAnalysis)
    assert analysis.period_grain == "month"
    assert analysis.total_periods == 0
    assert analysis.data == []
    assert analysis.revenue_trend.direction == "insufficient_data"
    assert analysis.warnings


def test_single_period_returns_insufficient_data() -> None:
    analysis = analyze_time_series_trends(
        _dataset([_record("ORD-1", "2026-01-10", 100.0)])
    )

    assert analysis.total_periods == 1
    assert analysis.order_count_trend.direction == "insufficient_data"


def test_monthly_trends_are_chronological_and_increasing() -> None:
    analysis = analyze_time_series_trends(
        _dataset(
            [
                _record("ORD-2", "2026-02-10", 250.0, quantity=5),
                _record("ORD-1", "2026-01-10", 100.0, quantity=2),
            ]
        )
    )

    assert [point.period for point in analysis.data] == ["2026-01", "2026-02"]
    assert analysis.revenue_trend.direction == "increasing"
    assert analysis.revenue_trend.start_value == 100.0
    assert analysis.revenue_trend.end_value == 250.0
    assert analysis.revenue_trend.percent_change == 150.0
    assert analysis.units_sold_trend.direction == "increasing"


def test_decreasing_revenue_and_order_count_are_detected() -> None:
    analysis = analyze_time_series_trends(
        _dataset(
            [
                _record("ORD-1", "2026-01-10", 100.0),
                _record("ORD-2", "2026-01-11", 120.0),
                _record("ORD-3", "2026-02-10", 80.0),
            ]
        )
    )

    assert analysis.revenue_trend.direction == "decreasing"
    assert analysis.order_count_trend.direction == "decreasing"
    assert any("Order volume" in warning for warning in analysis.warnings)


def test_less_than_one_percent_change_is_flat() -> None:
    analysis = analyze_time_series_trends(
        _dataset(
            [
                _record("ORD-1", "2026-01-10", 100.0),
                _record("ORD-2", "2026-02-10", 100.5),
            ]
        )
    )

    assert analysis.revenue_trend.direction == "flat"


def test_percent_change_is_none_when_start_value_is_zero() -> None:
    analysis = analyze_time_series_trends(
        _dataset(
            [
                _record("ORD-1", "2026-01-10", 0.0),
                _record("ORD-2", "2026-02-10", 100.0),
            ]
        )
    )

    assert analysis.revenue_trend.direction == "increasing"
    assert analysis.revenue_trend.percent_change is None


def test_material_average_discount_increase_adds_warning() -> None:
    analysis = analyze_time_series_trends(
        _dataset(
            [
                _record("ORD-1", "2026-01-10", 100.0, discount=0.1),
                _record("ORD-2", "2026-02-10", 100.0, discount=0.2),
            ]
        )
    )

    assert analysis.average_discount_trend.direction == "increasing"
    assert analysis.average_discount_trend.percent_change == 100.0
    assert any("Average discount" in warning for warning in analysis.warnings)


def _dataset(records: list[PreparedSalesRecord]) -> PreparedSalesDataset:
    return PreparedSalesDataset(records=records, total_records=len(records))


def _record(
    order_id: str,
    order_date: str,
    net_revenue: float,
    *,
    quantity: int = 1,
    discount: float = 0.0,
) -> PreparedSalesRecord:
    parsed_date = date.fromisoformat(order_date)
    gross_revenue = round(net_revenue / (1 - discount), 2) if discount < 1 else 0.0
    unit_price = round(gross_revenue / quantity, 2) if quantity else 0.0

    return PreparedSalesRecord(
        order_id=order_id,
        order_date=parsed_date,
        customer_id="CUST-1",
        region="North",
        product="Analytics Pro",
        sales_rep="Ava Singh",
        quantity=quantity,
        unit_price=unit_price,
        discount=discount,
        revenue=net_revenue,
        gross_revenue=gross_revenue,
        discount_amount=round(gross_revenue * discount, 2),
        net_revenue=net_revenue,
        average_unit_revenue=round(net_revenue / quantity, 2) if quantity else 0.0,
        order_year=parsed_date.year,
        order_month=parsed_date.month,
        order_quarter=((parsed_date.month - 1) // 3) + 1,
        is_discounted=discount > 0,
        is_high_value_order=net_revenue >= 5000,
        revenue_reconciliation_difference=0.0,
    )
