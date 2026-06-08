from collections import Counter

from pydantic import BaseModel, Field

from insightops.anomalies.detector import AnomalyDetectionResult
from insightops.charts.interpretations import (
    anomaly_severity_interpretation,
    discount_concentration_interpretation,
    pareto_concentration_interpretation,
    quality_score_interpretation,
    revenue_share,
    top_category_interpretation,
    trend_direction_interpretation,
)
from insightops.forecasting.baselines import ForecastAnalysis, MetricForecast
from insightops.insights.generator import ExecutiveInsightReport
from insightops.metrics.kpis import SalesKPIResult
from insightops.preparation.manipulations import ManipulationSummary
from insightops.profiling.quality_score import DataQualityScore
from insightops.trends.time_series import TimeSeriesTrendAnalysis


class ChartDataPoint(BaseModel):
    label: str
    value: float | int
    secondary_value: float | int | None = None


class ChartSeries(BaseModel):
    chart_id: str
    title: str
    chart_type: str
    metric: str
    x_axis: str
    y_axis: str
    business_question: str = ""
    interpretation: str = ""
    related_insight_ids: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    data: list[ChartDataPoint] = Field(default_factory=list)


class SalesChartData(BaseModel):
    charts: list[ChartSeries] = Field(default_factory=list)


def build_sales_chart_data(
    kpis: SalesKPIResult,
    anomalies: AnomalyDetectionResult,
    quality_score: DataQualityScore | None = None,
    manipulation_summary: ManipulationSummary | None = None,
    insights: ExecutiveInsightReport | None = None,
    trend_analysis: TimeSeriesTrendAnalysis | None = None,
    forecast_analysis: ForecastAnalysis | None = None,
) -> SalesChartData:
    insight_ids = _insight_ids_by_type(insights)
    recommended_actions = insights.recommended_actions if insights else []

    res = SalesChartData(
        charts=[
            _build_revenue_chart(
                chart_id="revenue_by_region",
                title="Revenue by Region",
                metric="revenue",
                x_axis="region",
                grouped_revenue=kpis.revenue_by_region,
                business_question="Which regions generate the most revenue?",
                interpretation=top_category_interpretation(
                    category_name="region",
                    grouped_values=kpis.revenue_by_region,
                    metric_label="revenue",
                ),
                related_insight_ids=insight_ids.get("revenue", []),
                recommended_actions=recommended_actions,
            ),
            _build_revenue_chart(
                chart_id="revenue_by_product",
                title="Revenue by Product",
                metric="revenue",
                x_axis="product",
                grouped_revenue=kpis.revenue_by_product,
                business_question="Which products generate the most revenue?",
                interpretation=top_category_interpretation(
                    category_name="product",
                    grouped_values=kpis.revenue_by_product,
                    metric_label="revenue",
                ),
                related_insight_ids=insight_ids.get("product", []),
                recommended_actions=recommended_actions,
            ),
            _build_revenue_chart(
                chart_id="revenue_by_sales_rep",
                title="Revenue by Sales Rep",
                metric="revenue",
                x_axis="sales_rep",
                grouped_revenue=kpis.revenue_by_sales_rep,
                business_question="Which sales reps are driving revenue?",
                interpretation=top_category_interpretation(
                    category_name="sales rep",
                    grouped_values=kpis.revenue_by_sales_rep,
                    metric_label="revenue",
                ),
                related_insight_ids=insight_ids.get("sales_rep", []),
                recommended_actions=recommended_actions,
            ),
            _build_monthly_net_revenue_chart(
                trend_analysis,
                insight_ids.get("trend_revenue", []),
                recommended_actions,
            ),
            _build_trend_chart(
                trend_analysis=trend_analysis,
                chart_id="monthly_order_count_trend",
                title="Monthly Order Count Trend",
                metric="order_count",
                y_axis="order_count",
                business_question="Is order volume increasing, decreasing, or flat?",
                related_insight_ids=insight_ids.get("trend_order_volume", []),
                recommended_actions=recommended_actions,
            ),
            _build_trend_chart(
                trend_analysis=trend_analysis,
                chart_id="average_order_value_trend",
                title="Average Order Value Trend",
                metric="average_order_value",
                y_axis="average_order_value",
                business_question="Is average order value changing over time?",
                related_insight_ids=[],
                recommended_actions=recommended_actions,
            ),
            _build_trend_chart(
                trend_analysis=trend_analysis,
                chart_id="average_discount_trend",
                title="Average Discount Trend",
                metric="average_discount",
                y_axis="average_discount",
                business_question="Is discount pressure increasing over time?",
                related_insight_ids=insight_ids.get("trend_discount", []),
                recommended_actions=recommended_actions,
            ),
            _build_forecast_chart(
                trend_analysis=trend_analysis,
                forecast=(
                    forecast_analysis.revenue_forecast
                    if forecast_analysis is not None
                    else None
                ),
                chart_id="revenue_forecast_baseline",
                title="Revenue Baseline Forecast",
                metric="revenue",
                y_axis="revenue",
                business_question=(
                    "What is the deterministic baseline revenue for the next period?"
                ),
                related_insight_ids=insight_ids.get("forecast_revenue", []),
                recommended_actions=recommended_actions,
            ),
            _build_forecast_chart(
                trend_analysis=trend_analysis,
                forecast=(
                    forecast_analysis.order_count_forecast
                    if forecast_analysis is not None
                    else None
                ),
                chart_id="order_count_forecast_baseline",
                title="Order Count Baseline Forecast",
                metric="order_count",
                y_axis="order_count",
                business_question=(
                    "What is the deterministic baseline order volume for the next period?"
                ),
                related_insight_ids=insight_ids.get("forecast_order_count", []),
                recommended_actions=recommended_actions,
            ),
            _build_discount_summary_chart(
                manipulation_summary,
                insight_ids.get("discount_concentration", []),
                recommended_actions,
            ),
            _build_anomalies_by_severity_chart(
                anomalies,
                insight_ids.get("anomaly", []),
                recommended_actions,
            ),
            _build_quality_score_chart(
                quality_score,
                insight_ids.get("data_quality_risk", []),
                recommended_actions,
            ),
            _build_pareto_revenue_by_product_chart(
                kpis.revenue_by_product,
                insight_ids.get("product", [])
                + insight_ids.get("business_concentration", []),
                recommended_actions,
            ),
        ]
    )

    for chart in res.charts:
        chart.recommended_actions = _get_chart_specific_actions(
            chart.chart_id, chart.recommended_actions
        )

    return res


def _get_chart_specific_actions(chart_id: str, all_actions: list[str]) -> list[str]:
    # 1. Filter out generic quality actions
    generic_substrings = [
        "invalid sales",
        "quality score",
        "missing value",
        "data quality",
        "missing field",
        "kpi and chart",
        "fill missing",
        "correct missing",
    ]

    filtered = []
    for action in all_actions:
        lower_action = action.lower()
        is_generic = any(sub in lower_action for sub in generic_substrings)

        # Exception: if the chart is specifically about data quality, keep them
        if is_generic and chart_id == "data_quality_score":
            filtered.append(action)
        elif not is_generic:
            filtered.append(action)

    # Deduplicate
    deduped = []
    for action in filtered:
        if action not in deduped:
            deduped.append(action)

    # Keep at most 1 to 2 actions
    chart_specific = deduped[:2]

    # Fallback if empty
    if not chart_specific:
        chart_specific = [
            "Use this visual as supporting evidence for the related business recommendation."
        ]

    return chart_specific


def _build_revenue_chart(
    *,
    chart_id: str,
    title: str,
    metric: str,
    x_axis: str,
    grouped_revenue: dict[str, float],
    business_question: str,
    interpretation: str,
    related_insight_ids: list[str],
    recommended_actions: list[str],
) -> ChartSeries:
    return ChartSeries(
        chart_id=chart_id,
        title=title,
        chart_type="bar",
        metric=metric,
        x_axis=x_axis,
        y_axis="revenue",
        business_question=business_question,
        interpretation=interpretation,
        related_insight_ids=related_insight_ids,
        recommended_actions=recommended_actions,
        data=[
            ChartDataPoint(label=label, value=value)
            for label, value in sorted(
                grouped_revenue.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    )


def _build_anomalies_by_severity_chart(
    anomalies: AnomalyDetectionResult,
    related_insight_ids: list[str],
    recommended_actions: list[str],
) -> ChartSeries:
    severity_counts = Counter(anomaly.severity for anomaly in anomalies.anomalies)

    return ChartSeries(
        chart_id="anomalies_by_severity",
        title="Anomalies by Severity",
        chart_type="bar",
        metric="anomaly_count",
        x_axis="severity",
        y_axis="count",
        business_question="How severe are detected sales anomalies?",
        interpretation=anomaly_severity_interpretation(dict(severity_counts)),
        related_insight_ids=related_insight_ids,
        recommended_actions=recommended_actions,
        data=[
            ChartDataPoint(label=severity, value=count)
            for severity, count in sorted(severity_counts.items())
        ],
    )


def _build_monthly_net_revenue_chart(
    trend_analysis: TimeSeriesTrendAnalysis | None,
    related_insight_ids: list[str],
    recommended_actions: list[str],
) -> ChartSeries:
    points = trend_analysis.data if trend_analysis is not None else []
    ordered_points = sorted(points, key=lambda point: point.period)

    return ChartSeries(
        chart_id="monthly_net_revenue_trend",
        title="Monthly Net Revenue Trend",
        chart_type="line",
        metric="net_revenue",
        x_axis="month",
        y_axis="net_revenue",
        business_question="Is revenue trending up, down, or flat over time?",
        interpretation=(
            trend_analysis.revenue_trend.interpretation
            if trend_analysis is not None
            else trend_direction_interpretation([])
        ),
        related_insight_ids=related_insight_ids,
        recommended_actions=recommended_actions,
        data=[
            ChartDataPoint(label=point.period, value=point.revenue)
            for point in ordered_points
        ],
    )


def _build_trend_chart(
    *,
    trend_analysis: TimeSeriesTrendAnalysis | None,
    chart_id: str,
    title: str,
    metric: str,
    y_axis: str,
    business_question: str,
    related_insight_ids: list[str],
    recommended_actions: list[str],
) -> ChartSeries:
    points = trend_analysis.data if trend_analysis is not None else []
    ordered_points = sorted(points, key=lambda point: point.period)
    trend_summary = (
        getattr(trend_analysis, f"{metric}_trend", None) if trend_analysis else None
    )

    return ChartSeries(
        chart_id=chart_id,
        title=title,
        chart_type="line",
        metric=metric,
        x_axis="month",
        y_axis=y_axis,
        business_question=business_question,
        interpretation=(
            trend_summary.interpretation
            if trend_summary is not None
            else trend_direction_interpretation([])
        ),
        related_insight_ids=related_insight_ids,
        recommended_actions=recommended_actions,
        data=[
            ChartDataPoint(label=point.period, value=getattr(point, metric))
            for point in ordered_points
        ],
    )


def _build_forecast_chart(
    *,
    trend_analysis: TimeSeriesTrendAnalysis | None,
    forecast: MetricForecast | None,
    chart_id: str,
    title: str,
    metric: str,
    y_axis: str,
    business_question: str,
    related_insight_ids: list[str],
    recommended_actions: list[str],
) -> ChartSeries:
    observed_points = trend_analysis.data if trend_analysis is not None else []
    data = [
        ChartDataPoint(label=point.period, value=getattr(point, metric))
        for point in sorted(observed_points, key=lambda point: point.period)
    ]
    if forecast is not None:
        data.append(
            ChartDataPoint(
                label=forecast.next_period,
                value=forecast.selected_forecast_value,
            )
        )

    return ChartSeries(
        chart_id=chart_id,
        title=title,
        chart_type="line",
        metric=metric,
        x_axis="month",
        y_axis=y_axis,
        business_question=business_question,
        interpretation=(
            _forecast_interpretation(forecast)
            if forecast is not None
            else "No forecast baseline is available."
        ),
        related_insight_ids=related_insight_ids,
        recommended_actions=recommended_actions,
        data=data,
    )


def _forecast_interpretation(forecast: MetricForecast) -> str:
    return (
        f"Selected {forecast.selected_baseline_method} baseline for "
        f"{forecast.next_period} is {forecast.selected_forecast_value:.2f} "
        f"with {forecast.confidence} confidence."
    )


def _build_discount_summary_chart(
    manipulation_summary: ManipulationSummary | None,
    related_insight_ids: list[str],
    recommended_actions: list[str],
) -> ChartSeries:
    summaries = (
        manipulation_summary.discount_summary_by_product
        if manipulation_summary is not None
        else []
    )
    ordered = sorted(
        summaries,
        key=lambda item: (-item.average_discount, item.product),
    )

    return ChartSeries(
        chart_id="discount_summary_by_product",
        title="Average Discount by Product",
        chart_type="bar",
        metric="average_discount",
        x_axis="product",
        y_axis="average_discount",
        business_question="Which products rely most on discounting?",
        interpretation=discount_concentration_interpretation(
            [(item.product, item.average_discount) for item in ordered]
        ),
        related_insight_ids=related_insight_ids,
        recommended_actions=recommended_actions,
        data=[
            ChartDataPoint(
                label=item.product,
                value=item.average_discount,
                secondary_value=item.discounted_order_count,
            )
            for item in ordered
        ],
    )


def _build_quality_score_chart(
    quality_score: DataQualityScore | None,
    related_insight_ids: list[str],
    recommended_actions: list[str],
) -> ChartSeries:
    data = (
        [ChartDataPoint(label=quality_score.grade, value=quality_score.score)]
        if quality_score is not None
        else []
    )

    return ChartSeries(
        chart_id="data_quality_score",
        title="Data Quality Score",
        chart_type="gauge_like_bar",
        metric="quality_score",
        x_axis="grade",
        y_axis="score",
        business_question=("Is the dataset reliable enough for executive reporting?"),
        interpretation=quality_score_interpretation(quality_score),
        related_insight_ids=related_insight_ids,
        recommended_actions=recommended_actions,
        data=data,
    )


def _build_pareto_revenue_by_product_chart(
    revenue_by_product: dict[str, float],
    related_insight_ids: list[str],
    recommended_actions: list[str],
) -> ChartSeries:
    ordered = sorted(
        revenue_by_product.items(),
        key=lambda item: (-item[1], item[0]),
    )
    total_revenue = sum(value for _, value in ordered)
    cumulative_revenue = 0.0
    data: list[ChartDataPoint] = []
    for label, value in ordered:
        cumulative_revenue += value
        data.append(
            ChartDataPoint(
                label=label,
                value=value,
                secondary_value=revenue_share(
                    cumulative_revenue,
                    total_revenue,
                ),
            )
        )

    return ChartSeries(
        chart_id="pareto_revenue_by_product",
        title="Pareto Revenue by Product",
        chart_type="bar",
        metric="revenue",
        x_axis="product",
        y_axis="revenue",
        business_question=("Is revenue concentrated in a small number of products?"),
        interpretation=pareto_concentration_interpretation(revenue_by_product),
        related_insight_ids=related_insight_ids,
        recommended_actions=recommended_actions,
        data=data,
    )


def _insight_ids_by_type(
    insights: ExecutiveInsightReport | None,
) -> dict[str, list[str]]:
    insight_ids: dict[str, list[str]] = {}
    if insights is None:
        return insight_ids

    for insight in insights.insights:
        insight_ids.setdefault(insight.insight_type, []).append(insight.insight_id)

    return insight_ids
