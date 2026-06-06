from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from insightops.api.contracts import AnalysisResponse

RecommendationEvidenceValue = str | int | float | bool


class BusinessRecommendation(BaseModel):
    recommendation_id: str
    priority: str
    business_area: str
    title: str
    problem: str
    evidence: dict[str, RecommendationEvidenceValue] = Field(
        default_factory=dict
    )
    recommended_action: str
    expected_impact: str
    workflow_stage: str
    owner_role: str
    implementation_difficulty: str
    follow_up_metric: str
    related_insight_ids: list[str] = Field(default_factory=list)
    related_chart_ids: list[str] = Field(default_factory=list)


class RecommendationPlan(BaseModel):
    total_recommendations: int
    recommendations: list[BusinessRecommendation] = Field(default_factory=list)


def generate_recommendation_plan(
    analysis: AnalysisResponse,
) -> RecommendationPlan:
    recommendations = [
        recommendation
        for recommendation in [
            _data_quality_recommendation(analysis),
            _data_completeness_recommendation(analysis),
            _data_integrity_recommendation(analysis),
            _discount_workflow_recommendation(analysis),
            _revenue_concentration_recommendation(analysis),
            _anomaly_review_recommendation(analysis),
            _security_review_recommendation(analysis),
            _portfolio_focus_recommendation(analysis),
            _revenue_trend_recommendation(analysis),
            _order_volume_trend_recommendation(analysis),
            _discount_trend_recommendation(analysis),
            _forecast_readiness_recommendation(analysis),
            _baseline_forecast_review_recommendation(analysis),
            _forecast_revenue_risk_recommendation(analysis),
            _forecast_discount_pressure_recommendation(analysis),
        ]
        if recommendation is not None
    ]
    recommendations = sorted(
        recommendations,
        key=lambda recommendation: recommendation.recommendation_id,
    )

    return RecommendationPlan(
        total_recommendations=len(recommendations),
        recommendations=recommendations,
    )


def _data_quality_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    if analysis.quality_gate.status not in {"blocked", "warning"}:
        return None

    priority = "high" if analysis.quality_gate.status == "blocked" else "medium"
    return BusinessRecommendation(
        recommendation_id="data_quality_001",
        priority=priority,
        business_area="data_quality",
        title="Remediate data quality before executive decisions",
        problem=(
            "The quality gate found data quality risk that reduces analysis "
            "confidence."
        ),
        evidence={
            "quality_gate_status": analysis.quality_gate.status,
            "confidence_level": analysis.quality_gate.confidence_level,
            "quality_score": analysis.quality_score.score,
            "invalid_rows": analysis.validation.invalid_rows,
        },
        recommended_action=(
            "Clean invalid rows, missing fields, and duplicate identifiers "
            "before relying on executive decisions."
        ),
        expected_impact="Improves confidence in KPIs, charts, and reporting.",
        workflow_stage="data_intake",
        owner_role="Data Operations Lead",
        implementation_difficulty="medium",
        follow_up_metric="quality_score",
        related_insight_ids=_insight_ids(analysis, "governance")
        + _insight_ids(analysis, "data_quality_risk"),
        related_chart_ids=["data_quality_score"],
    )


def _data_completeness_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    missing_field_total = sum(analysis.data_profile.missing_field_counts.values())
    if missing_field_total == 0:
        return None

    return BusinessRecommendation(
        recommendation_id="data_completeness_001",
        priority="medium",
        business_area="data_completeness",
        title="Add required field checks upstream",
        problem="Required sales fields are missing from source records.",
        evidence={
            "missing_field_total": missing_field_total,
            "fields_with_missing_values": len(
                analysis.data_profile.missing_field_counts
            ),
        },
        recommended_action=(
            "Enforce required field validation in the source sales entry "
            "workflow before CSV export."
        ),
        expected_impact="Reduces invalid records and manual cleanup.",
        workflow_stage="source_system_entry",
        owner_role="Sales Operations Manager",
        implementation_difficulty="low",
        follow_up_metric="missing_field_total",
        related_insight_ids=_insight_ids(analysis, "data_completeness"),
        related_chart_ids=["data_quality_score"],
    )


def _data_integrity_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    if analysis.data_profile.duplicate_order_ids == 0:
        return None

    return BusinessRecommendation(
        recommendation_id="data_integrity_001",
        priority="medium",
        business_area="data_integrity",
        title="Review duplicate order identifiers",
        problem="Duplicate order IDs can inflate or distort revenue analysis.",
        evidence={
            "duplicate_order_ids": analysis.data_profile.duplicate_order_ids,
        },
        recommended_action=(
            "Distinguish true duplicate orders from valid multi-line order "
            "records or multi-line orders before executive reporting."
        ),
        expected_impact="Improves order-level revenue accuracy.",
        workflow_stage="order_management",
        owner_role="Revenue Operations Manager",
        implementation_difficulty="medium",
        follow_up_metric="duplicate_order_id_count",
        related_insight_ids=_insight_ids(analysis, "data_integrity"),
        related_chart_ids=["data_quality_score"],
    )


def _discount_workflow_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    summaries = analysis.manipulation_summary.discount_summary_by_product
    if len(summaries) < 2:
        return None

    ordered = sorted(
        summaries,
        key=lambda summary: (-summary.average_discount, summary.product),
    )
    top = ordered[0]
    second = ordered[1]
    if top.average_discount - second.average_discount < 0.05:
        return None

    return BusinessRecommendation(
        recommendation_id="discount_workflow_001",
        priority="medium",
        business_area="discounting",
        title="Review discount approval workflow",
        problem="One product relies materially more on discounting than peers.",
        evidence={
            "product": top.product,
            "average_discount": top.average_discount,
            "next_highest_average_discount": second.average_discount,
        },
        recommended_action=(
            "Add discount approval thresholds or conduct a pricing review for "
            "the product with elevated discounting."
        ),
        expected_impact="Improves margin discipline and pricing consistency.",
        workflow_stage="sales_approval",
        owner_role="Sales Operations Manager",
        implementation_difficulty="medium",
        follow_up_metric="average_discount_by_product",
        related_insight_ids=_insight_ids(analysis, "discount_concentration"),
        related_chart_ids=["discount_summary_by_product"],
    )


def _revenue_concentration_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    high_value_records = [
        record
        for record in analysis.preparation.records
        if record.is_high_value_order
    ]
    if not high_value_records:
        return None

    region_counts = _count_labels(
        [record.region for record in high_value_records]
    )
    product_counts = _count_labels(
        [record.product for record in high_value_records]
    )
    label, count, dimension = _top_concentration(region_counts, product_counts)
    if count / len(high_value_records) < 0.5:
        return None

    return BusinessRecommendation(
        recommendation_id="revenue_concentration_001",
        priority="medium",
        business_area="revenue_concentration",
        title="Review high-value order concentration",
        problem="High-value orders are concentrated in one segment.",
        evidence={
            "dimension": dimension,
            "label": label,
            "high_value_order_count": count,
        },
        recommended_action=(
            "Review account exposure, product focus strategy, and concentration "
            "risk for the dominant high-value segment."
        ),
        expected_impact="Balances growth focus with revenue concentration risk.",
        workflow_stage="sales_strategy",
        owner_role="Sales Director",
        implementation_difficulty="medium",
        follow_up_metric="high_value_order_concentration",
        related_insight_ids=_insight_ids(analysis, "business_concentration"),
        related_chart_ids=["revenue_by_region", "revenue_by_product"],
    )


def _anomaly_review_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    high_severity_count = sum(
        1 for anomaly in analysis.anomalies.anomalies if anomaly.severity == "high"
    )
    if high_severity_count == 0:
        return None

    return BusinessRecommendation(
        recommendation_id="anomaly_review_001",
        priority="high",
        business_area="risk_review",
        title="Review high-severity anomalies before reporting",
        problem="High-severity anomalies can materially distort reporting.",
        evidence={"high_severity_anomalies": high_severity_count},
        recommended_action=(
            "Review anomalous transactions with finance before final reporting."
        ),
        expected_impact="Reduces risk of inaccurate financial communication.",
        workflow_stage="revenue_audit",
        owner_role="Finance Analyst",
        implementation_difficulty="low",
        follow_up_metric="high_severity_anomaly_count",
        related_insight_ids=_insight_ids(analysis, "anomaly")
        + _insight_ids(analysis, "statistical_outliers"),
        related_chart_ids=["anomalies_by_severity"],
    )


def _security_review_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    if not analysis.security.human_review_required:
        return None

    return BusinessRecommendation(
        recommendation_id="security_review_001",
        priority="high",
        business_area="security",
        title="Complete security review before narrative generation",
        problem="Security scan requires human review before narrative generation.",
        evidence={
            "prompt_injection_detected": analysis.security.prompt_injection_detected,
            "human_review_required": analysis.security.human_review_required,
        },
        recommended_action=(
            "Require a human security review before using narrative generation "
            "or sharing affected records."
        ),
        expected_impact="Prevents unsafe or manipulated narrative output.",
        workflow_stage="data_review",
        owner_role="Security Reviewer",
        implementation_difficulty="low",
        follow_up_metric="security_review_status",
        related_insight_ids=_insight_ids(analysis, "security"),
        related_chart_ids=[],
    )


def _portfolio_focus_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    pareto_chart = _chart_by_id(analysis, "pareto_revenue_by_product")
    if pareto_chart is None or not pareto_chart.data:
        return None

    top_point = pareto_chart.data[0]
    if top_point.secondary_value is None or top_point.secondary_value < 50:
        return None

    return BusinessRecommendation(
        recommendation_id="portfolio_focus_001",
        priority="low",
        business_area="portfolio_focus",
        title="Align go-to-market focus with product revenue concentration",
        problem="Product revenue is concentrated enough to warrant portfolio review.",
        evidence={
            "top_product": top_point.label,
            "cumulative_share": top_point.secondary_value,
        },
        recommended_action=(
            "Focus resources on dominant products while monitoring concentration "
            "risk and diversification opportunities."
        ),
        expected_impact="Improves allocation of sales and marketing effort.",
        workflow_stage="go_to_market_planning",
        owner_role="Sales Strategy Lead",
        implementation_difficulty="medium",
        follow_up_metric="product_revenue_concentration",
        related_insight_ids=_insight_ids(analysis, "product"),
        related_chart_ids=["pareto_revenue_by_product"],
    )


def _revenue_trend_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    trend = analysis.trend_analysis.revenue_trend
    if trend.direction != "decreasing":
        return None

    return BusinessRecommendation(
        recommendation_id="revenue_trend_review_001",
        priority="high",
        business_area="revenue_performance",
        title="Review declining revenue trend",
        problem="Monthly revenue is declining across the observed period range.",
        evidence={
            "start_value": trend.start_value,
            "end_value": trend.end_value,
            "absolute_change": trend.absolute_change,
            "percent_change": trend.percent_change or 0.0,
        },
        recommended_action=(
            "Review pipeline conversion, recent account losses, and pricing "
            "changes behind the revenue decline."
        ),
        expected_impact="Helps isolate the cause of revenue deterioration.",
        workflow_stage="sales_performance_review",
        owner_role="Sales Director",
        implementation_difficulty="medium",
        follow_up_metric="monthly_revenue",
        related_insight_ids=_insight_ids(analysis, "trend_revenue"),
        related_chart_ids=["monthly_net_revenue_trend"],
    )


def _order_volume_trend_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    trend = analysis.trend_analysis.order_count_trend
    if trend.direction != "decreasing":
        return None

    return BusinessRecommendation(
        recommendation_id="order_volume_review_001",
        priority="medium",
        business_area="demand_generation",
        title="Investigate declining order volume",
        problem="Monthly order count is declining across the observed period range.",
        evidence={
            "start_value": trend.start_value,
            "end_value": trend.end_value,
            "absolute_change": trend.absolute_change,
            "percent_change": trend.percent_change or 0.0,
        },
        recommended_action=(
            "Review lead flow, conversion rates, and sales activity for the "
            "periods where order volume fell."
        ),
        expected_impact="Supports earlier detection of demand or pipeline issues.",
        workflow_stage="pipeline_generation",
        owner_role="Revenue Operations Manager",
        implementation_difficulty="medium",
        follow_up_metric="monthly_order_count",
        related_insight_ids=_insight_ids(analysis, "trend_order_volume"),
        related_chart_ids=["monthly_order_count_trend"],
    )


def _discount_trend_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    trend = analysis.trend_analysis.average_discount_trend
    if trend.direction != "increasing":
        return None
    if trend.percent_change is None or trend.percent_change < 10:
        return None

    return BusinessRecommendation(
        recommendation_id="discount_trend_review_001",
        priority="medium",
        business_area="pricing_discipline",
        title="Review increasing discount trend",
        problem="Average discounting is increasing materially over time.",
        evidence={
            "start_value": trend.start_value,
            "end_value": trend.end_value,
            "absolute_change": trend.absolute_change,
            "percent_change": trend.percent_change,
        },
        recommended_action=(
            "Review discount approval thresholds and identify products or reps "
            "driving higher discount rates."
        ),
        expected_impact="Improves margin discipline and forecast confidence.",
        workflow_stage="discount_approval",
        owner_role="Sales Operations Manager",
        implementation_difficulty="medium",
        follow_up_metric="average_discount",
        related_insight_ids=_insight_ids(analysis, "trend_discount"),
        related_chart_ids=["average_discount_trend"],
    )


def _forecast_readiness_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    forecast = analysis.forecast_analysis
    if forecast.readiness_status != "not_ready":
        return None

    return BusinessRecommendation(
        recommendation_id="forecast_readiness_001",
        priority="medium",
        business_area="forecasting_readiness",
        title="Collect more monthly history before planning forecasts",
        problem="Forecast readiness is not sufficient for planning use.",
        evidence={
            "readiness_status": forecast.readiness_status,
            "confidence_level": forecast.confidence_level,
        },
        recommended_action=(
            "Collect more monthly sales periods and resolve quality blockers "
            "before using forecasts for planning."
        ),
        expected_impact="Improves forecast reliability and planning confidence.",
        workflow_stage="forecasting_readiness",
        owner_role="Revenue Operations Manager",
        implementation_difficulty="medium",
        follow_up_metric="monthly_period_count",
        related_insight_ids=_insight_ids(analysis, "forecast_readiness"),
        related_chart_ids=[],
    )


def _baseline_forecast_review_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    forecast = analysis.forecast_analysis
    if forecast.readiness_status != "limited":
        return None

    return BusinessRecommendation(
        recommendation_id="baseline_forecast_review_001",
        priority="medium",
        business_area="planning",
        title="Use baseline forecasts only as directional planning signals",
        problem="Only limited monthly history is available for forecasting.",
        evidence={
            "readiness_status": forecast.readiness_status,
            "confidence_level": forecast.confidence_level,
        },
        recommended_action=(
            "Use baseline forecasts as directional signals and validate them "
            "against pipeline and market context."
        ),
        expected_impact="Reduces overconfidence in limited-history planning.",
        workflow_stage="sales_planning_review",
        owner_role="Sales Planning Lead",
        implementation_difficulty="low",
        follow_up_metric="forecast_confidence_level",
        related_insight_ids=_insight_ids(analysis, "forecast_readiness"),
        related_chart_ids=[
            "revenue_forecast_baseline",
            "order_count_forecast_baseline",
        ],
    )


def _forecast_revenue_risk_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    forecast = analysis.forecast_analysis.revenue_forecast
    if forecast is None:
        return None
    if forecast.selected_forecast_value >= forecast.last_period_forecast.forecast_value:
        return None

    return BusinessRecommendation(
        recommendation_id="forecast_revenue_risk_001",
        priority="medium",
        business_area="revenue_planning",
        title="Review baseline revenue forecast risk",
        problem="The selected revenue baseline is below the latest observed month.",
        evidence={
            "latest_observed_revenue": forecast.last_period_forecast.forecast_value,
            "selected_forecast_value": forecast.selected_forecast_value,
            "selected_method": forecast.selected_baseline_method,
        },
        recommended_action=(
            "Review pipeline coverage, recent period drivers, and conversion "
            "risk before finalizing the next planning cycle."
        ),
        expected_impact="Improves early revenue risk detection.",
        workflow_stage="sales_planning_review",
        owner_role="Sales Director",
        implementation_difficulty="medium",
        follow_up_metric="forecast_revenue_gap",
        related_insight_ids=_insight_ids(analysis, "forecast_revenue"),
        related_chart_ids=["revenue_forecast_baseline"],
    )


def _forecast_discount_pressure_recommendation(
    analysis: AnalysisResponse,
) -> BusinessRecommendation | None:
    forecast = analysis.forecast_analysis.average_discount_forecast
    if forecast is None:
        return None
    if forecast.selected_forecast_value <= forecast.last_period_forecast.forecast_value:
        return None

    return BusinessRecommendation(
        recommendation_id="forecast_discount_pressure_001",
        priority="medium",
        business_area="pricing_discipline",
        title="Review forecast discount pressure",
        problem="The selected average discount baseline is above the latest observed month.",
        evidence={
            "latest_observed_discount": forecast.last_period_forecast.forecast_value,
            "selected_forecast_value": forecast.selected_forecast_value,
            "selected_method": forecast.selected_baseline_method,
        },
        recommended_action=(
            "Review discount approval workflows and identify the causes of "
            "forecast discount pressure."
        ),
        expected_impact="Improves margin discipline in planning conversations.",
        workflow_stage="pricing_discipline",
        owner_role="Sales Operations Manager",
        implementation_difficulty="medium",
        follow_up_metric="forecast_average_discount",
        related_insight_ids=_insight_ids(analysis, "forecast_discount"),
        related_chart_ids=["average_discount_trend"],
    )


def _insight_ids(analysis: AnalysisResponse, insight_type: str) -> list[str]:
    return [
        insight.insight_id
        for insight in analysis.insights.insights
        if insight.insight_type == insight_type
    ]


def _chart_by_id(analysis: AnalysisResponse, chart_id: str):
    return next(
        (chart for chart in analysis.charts.charts if chart.chart_id == chart_id),
        None,
    )


def _count_labels(labels: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return counts


def _top_concentration(
    region_counts: dict[str, int],
    product_counts: dict[str, int],
) -> tuple[str, int, str]:
    candidates = [
        (label, count, "region") for label, count in region_counts.items()
    ] + [(label, count, "product") for label, count in product_counts.items()]
    return sorted(candidates, key=lambda item: (-item[1], item[2], item[0]))[0]
