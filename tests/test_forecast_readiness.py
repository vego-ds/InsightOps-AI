from insightops.forecasting.readiness import evaluate_forecast_readiness
from insightops.governance.quality_gate import QualityGateResult
from insightops.trends.time_series import (
    MetricTrendSummary,
    TimeSeriesTrendAnalysis,
    TrendDataPoint,
)


def test_fewer_than_two_periods_returns_not_ready() -> None:
    result = evaluate_forecast_readiness(_trend_analysis(1), _quality_gate())

    assert result.status == "not_ready"
    assert result.confidence_level == "low"
    assert result.minimum_required_periods == 3


def test_exactly_two_periods_returns_limited() -> None:
    result = evaluate_forecast_readiness(_trend_analysis(2), _quality_gate())

    assert result.status == "limited"
    assert result.confidence_level == "low"
    assert any("two monthly periods" in reason for reason in result.reasons)


def test_three_or_more_periods_returns_ready() -> None:
    result = evaluate_forecast_readiness(_trend_analysis(3), _quality_gate())

    assert result.status == "ready"
    assert result.confidence_level == "medium"


def test_blocked_quality_gate_returns_not_ready() -> None:
    result = evaluate_forecast_readiness(
        _trend_analysis(3),
        _quality_gate(status="blocked", confidence_level="low"),
    )

    assert result.status == "not_ready"
    assert result.confidence_level == "low"
    assert any("quality gate is blocked" in item for item in result.limitations)


def test_warning_quality_gate_limits_confidence() -> None:
    result = evaluate_forecast_readiness(
        _trend_analysis(3),
        _quality_gate(status="warning", confidence_level="medium"),
    )

    assert result.status == "ready"
    assert result.confidence_level == "medium"
    assert any("Quality gate warnings" in item for item in result.limitations)


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


def _trend_analysis(total_periods: int) -> TimeSeriesTrendAnalysis:
    data = [
        TrendDataPoint(
            period=f"2026-{index + 1:02d}",
            revenue=100.0 + index,
            order_count=10 + index,
            units_sold=20 + index,
            average_order_value=10.0,
            average_discount=0.1,
        )
        for index in range(total_periods)
    ]
    return TimeSeriesTrendAnalysis(
        period_grain="month",
        total_periods=total_periods,
        data=data,
        revenue_trend=_summary("revenue"),
        order_count_trend=_summary("order_count"),
        average_order_value_trend=_summary("average_order_value"),
        units_sold_trend=_summary("units_sold"),
        average_discount_trend=_summary("average_discount"),
        warnings=[],
    )


def _summary(metric: str) -> MetricTrendSummary:
    return MetricTrendSummary(
        metric=metric,
        start_value=1.0,
        end_value=2.0,
        absolute_change=1.0,
        percent_change=100.0,
        direction="increasing",
        interpretation=f"{metric} is increasing.",
    )
