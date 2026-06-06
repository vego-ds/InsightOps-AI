from insightops.anomalies.detector import (
    AnomalyDetectionResult,
    SalesAnomaly,
)
from insightops.charts.chart_data import build_sales_chart_data
from insightops.metrics.kpis import SalesKPIResult
from insightops.preparation.manipulations import (
    ManipulationDataPoint,
    ManipulationSummary,
    ProductDiscountSummary,
)
from insightops.profiling.quality_score import DataQualityScore


def test_build_sales_chart_data_returns_expected_chart_series() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
    )

    assert len(chart_data.charts) == 8


def test_expected_sales_charts_exist() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
    )
    chart_ids = {chart.chart_id for chart in chart_data.charts}

    assert "revenue_by_region" in chart_ids
    assert "revenue_by_product" in chart_ids
    assert "revenue_by_sales_rep" in chart_ids
    assert "monthly_net_revenue_trend" in chart_ids
    assert "discount_summary_by_product" in chart_ids
    assert "anomalies_by_severity" in chart_ids
    assert "data_quality_score" in chart_ids
    assert "pareto_revenue_by_product" in chart_ids


def test_revenue_chart_data_is_sorted_by_value_descending() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
    )
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


def test_each_chart_has_visual_analytics_context() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
    )

    for chart in chart_data.charts:
        assert chart.business_question
        assert chart.interpretation
        assert isinstance(chart.related_insight_ids, list)
        assert isinstance(chart.recommended_actions, list)


def test_monthly_revenue_trend_is_chronological() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
    )
    chart = _chart_by_id(chart_data.charts, "monthly_net_revenue_trend")

    assert chart.chart_type == "line"
    assert [point.label for point in chart.data] == ["2026-01", "2026-02"]


def test_pareto_chart_includes_cumulative_share() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
    )
    chart = _chart_by_id(chart_data.charts, "pareto_revenue_by_product")

    assert chart.data[0].label == "Analytics Pro"
    assert chart.data[0].secondary_value is not None
    assert chart.data[-1].secondary_value == 100.0


def test_quality_score_and_discount_charts_exist() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
    )

    assert _chart_by_id(chart_data.charts, "data_quality_score").data[0].value == 70
    assert (
        _chart_by_id(chart_data.charts, "discount_summary_by_product")
        .data[0]
        .label
        == "Insights Basic"
    )


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


def _quality_score() -> DataQualityScore:
    return DataQualityScore(
        score=70,
        grade="fair",
        issues=["2 invalid rows detected"],
        recommendations=["Review invalid rows before executive reporting"],
    )


def _manipulation_summary() -> ManipulationSummary:
    return ManipulationSummary(
        monthly_revenue=[
            ManipulationDataPoint(label="2026-02", value=200.0),
            ManipulationDataPoint(label="2026-01", value=500.0),
        ],
        discount_summary_by_product=[
            ProductDiscountSummary(
                product="Analytics Pro",
                average_discount=0.1,
                discounted_order_count=1,
                total_orders=2,
            ),
            ProductDiscountSummary(
                product="Insights Basic",
                average_discount=0.2,
                discounted_order_count=1,
                total_orders=1,
            ),
        ],
    )
