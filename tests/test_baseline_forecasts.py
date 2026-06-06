from insightops.forecasting.baselines import (
    ForecastAnalysis,
    generate_forecast_analysis,
)
from insightops.governance.quality_gate import QualityGateResult
from insightops.trends.time_series import (
    MetricTrendSummary,
    TimeSeriesTrendAnalysis,
    TrendDataPoint,
)


def test_next_month_calculation_handles_normal_month() -> None:
    analysis = generate_forecast_analysis(
        _trend_analysis(["2026-01", "2026-02", "2026-03"]),
        _quality_gate(),
    )

    assert analysis.next_period == "2026-04"


def test_next_month_calculation_handles_december_rollover() -> None:
    analysis = generate_forecast_analysis(
        _trend_analysis(["2026-10", "2026-11", "2026-12"]),
        _quality_gate(),
    )

    assert analysis.next_period == "2027-01"


def test_last_period_forecast_equals_last_observed_value() -> None:
    analysis = generate_forecast_analysis(
        _trend_analysis(["2026-01", "2026-02", "2026-03"]),
        _quality_gate(),
    )

    assert analysis.revenue_forecast is not None
    assert analysis.revenue_forecast.last_period_forecast.forecast_value == 300.0


def test_moving_average_uses_last_three_periods() -> None:
    analysis = generate_forecast_analysis(
        _trend_analysis(["2026-01", "2026-02", "2026-03", "2026-04"]),
        _quality_gate(),
    )

    assert analysis.revenue_forecast is not None
    assert analysis.revenue_forecast.moving_average_forecast.forecast_value == 300.0
    assert analysis.revenue_forecast.selected_baseline_method == "moving_average"
    assert analysis.revenue_forecast.selected_forecast_value == 300.0


def test_simple_trend_projection_uses_average_period_change() -> None:
    analysis = generate_forecast_analysis(
        _trend_analysis(["2026-01", "2026-02", "2026-03"]),
        _quality_gate(),
    )

    assert analysis.revenue_forecast is not None
    assert analysis.revenue_forecast.trend_projection_forecast.forecast_value == 400.0


def test_empty_trend_data_does_not_crash() -> None:
    analysis = generate_forecast_analysis(_empty_trend_analysis(), _quality_gate())

    assert isinstance(analysis, ForecastAnalysis)
    assert analysis.readiness_status == "not_ready"
    assert analysis.next_period is None
    assert analysis.revenue_forecast is None


def test_limited_readiness_selects_last_period_forecast() -> None:
    analysis = generate_forecast_analysis(
        _trend_analysis(["2026-01", "2026-02"]),
        _quality_gate(),
    )

    assert analysis.readiness_status == "limited"
    assert analysis.revenue_forecast is not None
    assert analysis.revenue_forecast.selected_baseline_method == "last_period"
    assert analysis.revenue_forecast.confidence == "low"


def test_forecast_warnings_include_baseline_caveat() -> None:
    analysis = generate_forecast_analysis(
        _trend_analysis(["2026-01", "2026-02"]),
        _quality_gate(status="warning", confidence_level="medium"),
    )

    assert any("not predictive ML" in warning for warning in analysis.warnings)
    assert any("Quality gate warnings" in warning for warning in analysis.warnings)


def _quality_gate(
    *,
    status: str = "pass",
    confidence_level: str = "high",
) -> QualityGateResult:
    return QualityGateResult(
        status=status,
        confidence_level=confidence_level,
        can_generate_kpis=status != "blocked",
        can_generate_charts=status != "blocked",
        can_generate_reports=status != "blocked",
        can_generate_llm_narrative=False,
        human_review_required=status == "blocked",
        reasons=[],
        required_actions=[],
    )


def _trend_analysis(periods: list[str]) -> TimeSeriesTrendAnalysis:
    data = [
        TrendDataPoint(
            period=period,
            revenue=float((index + 1) * 100),
            order_count=index + 1,
            units_sold=(index + 1) * 10,
            average_order_value=100.0,
            average_discount=round(0.1 + (index * 0.01), 2),
        )
        for index, period in enumerate(periods)
    ]
    return TimeSeriesTrendAnalysis(
        period_grain="month",
        total_periods=len(data),
        data=data,
        revenue_trend=_summary("revenue"),
        order_count_trend=_summary("order_count"),
        average_order_value_trend=_summary("average_order_value"),
        units_sold_trend=_summary("units_sold"),
        average_discount_trend=_summary("average_discount"),
        warnings=[],
    )


def _empty_trend_analysis() -> TimeSeriesTrendAnalysis:
    return TimeSeriesTrendAnalysis(
        period_grain="month",
        total_periods=0,
        data=[],
        revenue_trend=_summary("revenue", direction="insufficient_data"),
        order_count_trend=_summary("order_count", direction="insufficient_data"),
        average_order_value_trend=_summary(
            "average_order_value",
            direction="insufficient_data",
        ),
        units_sold_trend=_summary("units_sold", direction="insufficient_data"),
        average_discount_trend=_summary(
            "average_discount",
            direction="insufficient_data",
        ),
        warnings=[],
    )


def _summary(
    metric: str,
    *,
    direction: str = "increasing",
) -> MetricTrendSummary:
    return MetricTrendSummary(
        metric=metric,
        start_value=1.0,
        end_value=2.0,
        absolute_change=1.0,
        percent_change=100.0,
        direction=direction,
        interpretation=f"{metric} is {direction}.",
    )
