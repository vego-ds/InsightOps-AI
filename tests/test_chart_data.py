from insightops.anomalies.detector import (
    AnomalyDetectionResult,
    SalesAnomaly,
)
from insightops.charts.chart_data import build_sales_chart_data
from insightops.metrics.kpis import SalesKPIResult


def test_build_sales_chart_data_returns_four_chart_series() -> None:
    chart_data = build_sales_chart_data(_kpi_result(), _anomaly_result())

    assert len(chart_data.charts) == 4


def test_expected_sales_charts_exist() -> None:
    chart_data = build_sales_chart_data(_kpi_result(), _anomaly_result())
    chart_ids = {chart.chart_id for chart in chart_data.charts}

    assert "revenue_by_region" in chart_ids
    assert "revenue_by_product" in chart_ids
    assert "revenue_by_sales_rep" in chart_ids
    assert "anomalies_by_severity" in chart_ids


def test_revenue_chart_data_is_sorted_by_value_descending() -> None:
    chart_data = build_sales_chart_data(_kpi_result(), _anomaly_result())
    region_chart = _chart_by_id(chart_data.charts, "revenue_by_region")

    assert [point.label for point in region_chart.data] == [
        "North",
        "East",
        "West",
    ]
    assert [point.value for point in region_chart.data] == [
        300.0,
        200.0,
        200.0,
    ]


def test_empty_anomaly_input_returns_empty_anomaly_chart_data() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        AnomalyDetectionResult(total_anomalies=0, anomalies=[]),
    )
    anomaly_chart = _chart_by_id(chart_data.charts, "anomalies_by_severity")

    assert anomaly_chart.data == []


def _chart_by_id(charts: list, chart_id: str):
    return next(chart for chart in charts if chart.chart_id == chart_id)


def _kpi_result() -> SalesKPIResult:
    return SalesKPIResult(
        total_revenue=700.0,
        total_orders=3,
        total_units_sold=7,
        average_order_value=233.33,
        revenue_by_region={
            "West": 200.0,
            "North": 300.0,
            "East": 200.0,
        },
        revenue_by_product={
            "Analytics Pro": 500.0,
            "Insights Basic": 200.0,
        },
        revenue_by_sales_rep={
            "Ava Singh": 400.0,
            "Noah Chen": 300.0,
        },
    )


def _anomaly_result() -> AnomalyDetectionResult:
    return AnomalyDetectionResult(
        total_anomalies=2,
        anomalies=[
            SalesAnomaly(
                anomaly_type="high_discount",
                severity="high",
                order_id="ORD-1",
                field="discount",
                value=0.5,
                message="Discount is unusually high.",
            ),
            SalesAnomaly(
                anomaly_type="high_revenue",
                severity="medium",
                order_id="ORD-2",
                field="revenue",
                value=5000.0,
                message="Revenue is unusually high.",
            ),
        ],
    )
