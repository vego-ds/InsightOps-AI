from insightops.charts.interpretations import (
    anomaly_severity_interpretation,
    discount_concentration_interpretation,
    pareto_concentration_interpretation,
    quality_score_interpretation,
    revenue_share,
    top_category_interpretation,
    trend_direction_interpretation,
)
from insightops.profiling.quality_score import DataQualityScore


def test_revenue_share_handles_zero_total() -> None:
    assert revenue_share(10.0, 0.0) == 0.0


def test_top_category_interpretation_identifies_leader() -> None:
    interpretation = top_category_interpretation(
        category_name="region",
        grouped_values={"West": 100.0, "East": 300.0},
        metric_label="revenue",
    )

    assert "East leads revenue" in interpretation
    assert "75.00%" in interpretation


def test_trend_direction_interpretation_is_deterministic() -> None:
    assert "increasing" in trend_direction_interpretation(
        [("2026-01", 100.0), ("2026-02", 200.0)]
    )
    assert "Insufficient" in trend_direction_interpretation(
        [("2026-01", 100.0)]
    )


def test_discount_concentration_interpretation_identifies_top_discount() -> None:
    interpretation = discount_concentration_interpretation(
        [("Basic", 0.1), ("Pro", 0.2)]
    )

    assert "Pro" in interpretation
    assert "0.20" in interpretation


def test_anomaly_and_quality_interpretations_are_explicit() -> None:
    assert "2 high severity" in anomaly_severity_interpretation(
        {"high": 2, "medium": 1}
    )
    assert "70/100" in quality_score_interpretation(
        DataQualityScore(score=70, grade="fair")
    )


def test_pareto_interpretation_mentions_cumulative_revenue_share() -> None:
    interpretation = pareto_concentration_interpretation(
        {"A": 80.0, "B": 20.0}
    )

    assert "80.00%" in interpretation
    assert "80% cumulative" in interpretation
