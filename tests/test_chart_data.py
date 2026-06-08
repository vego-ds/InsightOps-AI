from insightops.anomalies.detector import (
    AnomalyDetectionResult,
    SalesAnomaly,
)
from insightops.charts.chart_data import build_sales_chart_data
from insightops.forecasting.baselines import (
    ForecastAnalysis,
    ForecastPoint,
    MetricForecast,
)
from insightops.metrics.kpis import SalesKPIResult
from insightops.preparation.manipulations import (
    ManipulationDataPoint,
    ManipulationSummary,
    ProductDiscountSummary,
)
from insightops.profiling.quality_score import DataQualityScore
from insightops.trends.time_series import (
    MetricTrendSummary,
    TimeSeriesTrendAnalysis,
    TrendDataPoint,
)


def test_build_sales_chart_data_returns_expected_chart_series() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
    )

    assert len(chart_data.charts) == 13


def test_expected_sales_charts_exist() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
    )
    chart_ids = {chart.chart_id for chart in chart_data.charts}

    assert "revenue_by_region" in chart_ids
    assert "revenue_by_product" in chart_ids
    assert "revenue_by_sales_rep" in chart_ids
    assert "monthly_net_revenue_trend" in chart_ids
    assert "monthly_order_count_trend" in chart_ids
    assert "average_order_value_trend" in chart_ids
    assert "average_discount_trend" in chart_ids
    assert "revenue_forecast_baseline" in chart_ids
    assert "order_count_forecast_baseline" in chart_ids
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
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
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
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
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
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
    )
    chart = _chart_by_id(chart_data.charts, "monthly_net_revenue_trend")

    assert chart.chart_type == "line"
    assert [point.label for point in chart.data] == ["2026-01", "2026-02"]
    assert [point.value for point in chart.data] == [500.0, 200.0]


def test_time_series_trend_charts_use_trend_analysis() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
    )

    order_chart = _chart_by_id(chart_data.charts, "monthly_order_count_trend")
    aov_chart = _chart_by_id(chart_data.charts, "average_order_value_trend")
    discount_chart = _chart_by_id(chart_data.charts, "average_discount_trend")

    assert order_chart.chart_type == "line"
    assert [point.value for point in order_chart.data] == [2, 1]
    assert [point.value for point in aov_chart.data] == [250.0, 200.0]
    assert [point.value for point in discount_chart.data] == [0.1, 0.2]


def test_forecast_baseline_charts_include_context() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
    )

    revenue_chart = _chart_by_id(chart_data.charts, "revenue_forecast_baseline")
    order_chart = _chart_by_id(chart_data.charts, "order_count_forecast_baseline")

    assert revenue_chart.chart_type == "line"
    assert revenue_chart.business_question
    assert revenue_chart.interpretation
    assert revenue_chart.data[-1].label == "2026-03"
    assert order_chart.business_question
    assert order_chart.interpretation


def test_pareto_chart_includes_cumulative_share() -> None:
    chart_data = build_sales_chart_data(
        _kpi_result(),
        _anomaly_result(),
        _quality_score(),
        _manipulation_summary(),
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
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
        trend_analysis=_trend_analysis(),
        forecast_analysis=_forecast_analysis(),
    )

    assert _chart_by_id(chart_data.charts, "data_quality_score").data[0].value == 70
    assert (
        _chart_by_id(chart_data.charts, "discount_summary_by_product").data[0].label
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


def _trend_analysis() -> TimeSeriesTrendAnalysis:
    return TimeSeriesTrendAnalysis(
        period_grain="month",
        total_periods=2,
        data=[
            TrendDataPoint(
                period="2026-01",
                revenue=500.0,
                order_count=2,
                units_sold=5,
                average_order_value=250.0,
                average_discount=0.1,
            ),
            TrendDataPoint(
                period="2026-02",
                revenue=200.0,
                order_count=1,
                units_sold=2,
                average_order_value=200.0,
                average_discount=0.2,
            ),
        ],
        revenue_trend=_trend_summary("revenue", "decreasing"),
        order_count_trend=_trend_summary("order_count", "decreasing"),
        average_order_value_trend=_trend_summary(
            "average_order_value",
            "decreasing",
        ),
        units_sold_trend=_trend_summary("units_sold", "decreasing"),
        average_discount_trend=_trend_summary(
            "average_discount",
            "increasing",
        ),
        warnings=[],
    )


def _trend_summary(metric: str, direction: str) -> MetricTrendSummary:
    return MetricTrendSummary(
        metric=metric,
        start_value=1.0,
        end_value=2.0,
        absolute_change=1.0,
        percent_change=100.0,
        direction=direction,
        interpretation=f"{metric} is {direction}.",
    )


def _forecast_analysis() -> ForecastAnalysis:
    return ForecastAnalysis(
        readiness_status="limited",
        confidence_level="low",
        next_period="2026-03",
        revenue_forecast=_metric_forecast("revenue", 200.0),
        order_count_forecast=_metric_forecast("order_count", 1.0),
        average_order_value_forecast=_metric_forecast("average_order_value", 200.0),
        units_sold_forecast=_metric_forecast("units_sold", 2.0),
        average_discount_forecast=_metric_forecast("average_discount", 0.2),
        warnings=["Forecasts are deterministic baselines."],
        recommended_actions=[],
    )


def _metric_forecast(metric: str, value: float) -> MetricForecast:
    point = ForecastPoint(
        period="2026-03",
        metric=metric,
        forecast_value=value,
        method="last_period",
        confidence="low",
        explanation="Uses the most recent observed monthly value.",
    )
    return MetricForecast(
        metric=metric,
        next_period="2026-03",
        last_period_forecast=point,
        moving_average_forecast=point,
        trend_projection_forecast=point,
        selected_baseline_method="last_period",
        selected_forecast_value=value,
        confidence="low",
        warnings=[],
    )
