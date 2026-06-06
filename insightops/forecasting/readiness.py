from pydantic import BaseModel, Field

from insightops.governance.quality_gate import QualityGateResult
from insightops.trends.time_series import TimeSeriesTrendAnalysis

MINIMUM_REQUIRED_PERIODS = 3


class ForecastReadinessResult(BaseModel):
    status: str
    confidence_level: str
    total_periods: int
    minimum_required_periods: int
    reasons: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)


def evaluate_forecast_readiness(
    trend_analysis: TimeSeriesTrendAnalysis,
    quality_gate: QualityGateResult,
) -> ForecastReadinessResult:
    reasons: list[str] = []
    limitations: list[str] = []
    required_actions: list[str] = []
    total_periods = trend_analysis.total_periods

    if total_periods < 2:
        status = "not_ready"
        confidence_level = "low"
        reasons.append(
            "Insufficient monthly time periods are available for forecasting."
        )
        required_actions.append(
            "Collect at least three monthly periods before using forecasts for planning."
        )
    elif total_periods == 2:
        status = "limited"
        confidence_level = "low"
        reasons.append(
            "Only two monthly periods are available, so forecasts are limited."
        )
        limitations.append(
            "Two periods can show direction but are not enough for reliable baselines."
        )
        required_actions.append(
            "Use forecasts only as directional planning signals until more history is available."
        )
    else:
        status = "ready"
        confidence_level = "medium"
        reasons.append(
            "At least three monthly periods are available for baseline forecasting."
        )
        required_actions.append(
            "Use baseline forecasts as planning inputs and compare them with pipeline context."
        )

    if quality_gate.status == "blocked":
        status = "not_ready"
        confidence_level = "low"
        limitations.append(
            "The quality gate is blocked, so forecasts should not be used for planning."
        )
        required_actions.append(
            "Resolve blocked quality gate issues before using forecast outputs."
        )
    elif quality_gate.status == "warning":
        confidence_level = "medium" if status == "ready" else "low"
        limitations.append(
            "Quality gate warnings limit forecast confidence."
        )
        required_actions.append(
            "Review quality gate warnings before using baseline forecasts."
        )

    return ForecastReadinessResult(
        status=status,
        confidence_level=confidence_level,
        total_periods=total_periods,
        minimum_required_periods=MINIMUM_REQUIRED_PERIODS,
        reasons=_deduplicate(reasons),
        limitations=_deduplicate(limitations),
        required_actions=_deduplicate(required_actions),
    )


def _deduplicate(values: list[str]) -> list[str]:
    deduplicated: list[str] = []
    for value in values:
        if value not in deduplicated:
            deduplicated.append(value)
    return deduplicated
