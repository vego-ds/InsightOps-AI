from pydantic import BaseModel, Field

from insightops.forecasting.readiness import evaluate_forecast_readiness
from insightops.governance.quality_gate import QualityGateResult
from insightops.trends.time_series import TimeSeriesTrendAnalysis


class ForecastPoint(BaseModel):
    period: str
    metric: str
    forecast_value: float
    method: str
    confidence: str
    explanation: str


class MetricForecast(BaseModel):
    metric: str
    next_period: str
    last_period_forecast: ForecastPoint
    moving_average_forecast: ForecastPoint
    trend_projection_forecast: ForecastPoint
    selected_baseline_method: str
    selected_forecast_value: float
    confidence: str
    warnings: list[str] = Field(default_factory=list)


class ForecastAnalysis(BaseModel):
    readiness_status: str
    confidence_level: str
    next_period: str | None
    revenue_forecast: MetricForecast | None
    order_count_forecast: MetricForecast | None
    average_order_value_forecast: MetricForecast | None
    units_sold_forecast: MetricForecast | None
    average_discount_forecast: MetricForecast | None
    warnings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


def generate_forecast_analysis(
    trend_analysis: TimeSeriesTrendAnalysis,
    quality_gate: QualityGateResult,
) -> ForecastAnalysis:
    readiness = evaluate_forecast_readiness(trend_analysis, quality_gate)
    next_period = _next_period(trend_analysis.data[-1].period) if trend_analysis.data else None
    warnings = _analysis_warnings(readiness.status, quality_gate.status, trend_analysis)

    if next_period is None:
        forecasts = {
            "revenue_forecast": None,
            "order_count_forecast": None,
            "average_order_value_forecast": None,
            "units_sold_forecast": None,
            "average_discount_forecast": None,
        }
    else:
        forecasts = {
            "revenue_forecast": _metric_forecast(
                "revenue",
                [point.revenue for point in trend_analysis.data],
                next_period,
                readiness.status,
            ),
            "order_count_forecast": _metric_forecast(
                "order_count",
                [float(point.order_count) for point in trend_analysis.data],
                next_period,
                readiness.status,
            ),
            "average_order_value_forecast": _metric_forecast(
                "average_order_value",
                [point.average_order_value for point in trend_analysis.data],
                next_period,
                readiness.status,
            ),
            "units_sold_forecast": _metric_forecast(
                "units_sold",
                [float(point.units_sold) for point in trend_analysis.data],
                next_period,
                readiness.status,
            ),
            "average_discount_forecast": _metric_forecast(
                "average_discount",
                [point.average_discount for point in trend_analysis.data],
                next_period,
                readiness.status,
            ),
        }

    return ForecastAnalysis(
        readiness_status=readiness.status,
        confidence_level=readiness.confidence_level,
        next_period=next_period,
        warnings=warnings,
        recommended_actions=readiness.required_actions,
        **forecasts,
    )


def _metric_forecast(
    metric: str,
    values: list[float],
    next_period: str,
    readiness_status: str,
) -> MetricForecast:
    confidence = "medium" if readiness_status == "ready" else "low"
    last_period = _last_period_forecast(metric, values, next_period, confidence)
    moving_average = _moving_average_forecast(metric, values, next_period, confidence)
    trend_projection = _trend_projection_forecast(metric, values, next_period, confidence)
    selected_method = _selected_method(readiness_status)
    selected_point = {
        "moving_average": moving_average,
        "last_period": last_period,
        "trend_projection": trend_projection,
    }[selected_method]
    warnings = _metric_warnings(metric, values, readiness_status)

    return MetricForecast(
        metric=metric,
        next_period=next_period,
        last_period_forecast=last_period,
        moving_average_forecast=moving_average,
        trend_projection_forecast=trend_projection,
        selected_baseline_method=selected_method,
        selected_forecast_value=selected_point.forecast_value,
        confidence=confidence,
        warnings=warnings,
    )


def _last_period_forecast(
    metric: str,
    values: list[float],
    next_period: str,
    confidence: str,
) -> ForecastPoint:
    value = round(values[-1], 2) if values else 0.0
    return ForecastPoint(
        period=next_period,
        metric=metric,
        forecast_value=value,
        method="last_period",
        confidence=confidence,
        explanation="Uses the most recent observed monthly value as the next baseline.",
    )


def _moving_average_forecast(
    metric: str,
    values: list[float],
    next_period: str,
    confidence: str,
) -> ForecastPoint:
    selected_values = values[-3:] if len(values) >= 3 else values
    value = (
        round(sum(selected_values) / len(selected_values), 2)
        if selected_values
        else 0.0
    )
    method_confidence = confidence if len(values) >= 3 else "low"
    return ForecastPoint(
        period=next_period,
        metric=metric,
        forecast_value=value,
        method="moving_average",
        confidence=method_confidence,
        explanation=(
            "Uses the average of the last three monthly values when available; "
            "uses all available periods when fewer than three exist."
        ),
    )


def _trend_projection_forecast(
    metric: str,
    values: list[float],
    next_period: str,
    confidence: str,
) -> ForecastPoint:
    if len(values) < 2:
        value = round(values[-1], 2) if values else 0.0
        method_confidence = "low"
        explanation = (
            "Not enough periods exist for average change, so this falls back "
            "to the last observed value."
        )
    else:
        changes = [
            values[index] - values[index - 1]
            for index in range(1, len(values))
        ]
        average_change = sum(changes) / len(changes)
        value = round(values[-1] + average_change, 2)
        method_confidence = confidence
        explanation = (
            "Adds the average observed period-to-period change to the latest value."
        )

    return ForecastPoint(
        period=next_period,
        metric=metric,
        forecast_value=value,
        method="trend_projection",
        confidence=method_confidence,
        explanation=explanation,
    )


def _selected_method(readiness_status: str) -> str:
    if readiness_status == "ready":
        return "moving_average"
    return "last_period"


def _next_period(period: str) -> str:
    year_text, month_text = period.split("-")
    year = int(year_text)
    month = int(month_text)
    if month == 12:
        return f"{year + 1}-01"
    return f"{year:04d}-{month + 1:02d}"


def _analysis_warnings(
    readiness_status: str,
    quality_gate_status: str,
    trend_analysis: TimeSeriesTrendAnalysis,
) -> list[str]:
    warnings = [
        "Forecasts are deterministic baselines, not predictive ML forecasts.",
    ]
    if readiness_status in {"not_ready", "limited"}:
        warnings.append("Insufficient periods are available for reliable forecasting.")
    if quality_gate_status == "blocked":
        warnings.append("Quality gate is blocked, so forecasts are low confidence.")
    elif quality_gate_status == "warning":
        warnings.append("Quality gate warnings reduce forecast confidence.")
    if trend_analysis.average_discount_trend.direction == "increasing":
        warnings.append(
            "Average discount forecasts should be interpreted cautiously because discount trend is increasing."
        )
    return _deduplicate(warnings)


def _metric_warnings(
    metric: str,
    values: list[float],
    readiness_status: str,
) -> list[str]:
    warnings: list[str] = []
    if len(values) < 3:
        warnings.append("Fewer than three periods are available for moving average.")
    if readiness_status != "ready":
        warnings.append("Forecast confidence is low due to readiness limitations.")
    if metric == "average_discount":
        warnings.append("Discount forecast should be reviewed with pricing context.")
    return _deduplicate(warnings)


def _deduplicate(values: list[str]) -> list[str]:
    deduplicated: list[str] = []
    for value in values:
        if value not in deduplicated:
            deduplicated.append(value)
    return deduplicated
