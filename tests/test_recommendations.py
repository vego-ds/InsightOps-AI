from tests.test_markdown_report import _minimal_analysis_response

from insightops.anomalies.detector import SalesAnomaly
from insightops.forecasting.baselines import ForecastPoint, MetricForecast
from insightops.recommendations.action_plan import generate_recommendation_plan


def test_low_quality_gate_produces_data_quality_recommendation() -> None:
    analysis = _minimal_analysis_response()
    analysis.quality_gate.status = "warning"
    analysis.quality_gate.confidence_level = "medium"
    analysis.quality_score.score = 70

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "data_quality_001")
    assert recommendation.business_area == "data_quality"
    assert recommendation.owner_role == "Data Operations Lead"


def test_missing_fields_produce_data_completeness_recommendation() -> None:
    analysis = _minimal_analysis_response()
    analysis.data_profile.missing_field_counts = {"region": 1}

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "data_completeness_001")
    assert recommendation.workflow_stage == "source_system_entry"


def test_duplicate_ids_produce_data_integrity_recommendation() -> None:
    analysis = _minimal_analysis_response()
    analysis.data_profile.duplicate_order_ids = 1

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "data_integrity_001")
    assert "multi-line orders" in recommendation.recommended_action


def test_high_discounts_produce_discount_workflow_recommendation() -> None:
    analysis = _minimal_analysis_response()
    analysis.manipulation_summary.discount_summary_by_product = [
        _discount_summary("Analytics Pro", 0.2),
        _discount_summary("Insights Basic", 0.05),
    ]

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "discount_workflow_001")
    assert recommendation.business_area == "discounting"
    assert "discount_summary_by_product" in recommendation.related_chart_ids


def test_high_severity_anomalies_produce_anomaly_review_recommendation() -> None:
    analysis = _minimal_analysis_response()
    analysis.anomalies.anomalies = [
        SalesAnomaly(
            anomaly_type="high_discount",
            severity="high",
            order_id="ORD-1",
            field="discount",
            value=0.5,
            message="Discount is unusually high.",
        )
    ]
    analysis.anomalies.total_anomalies = 1

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "anomaly_review_001")
    assert recommendation.priority == "high"
    assert recommendation.owner_role == "Finance Analyst"


def test_security_review_produces_security_recommendation() -> None:
    analysis = _minimal_analysis_response()
    analysis.security.human_review_required = True
    analysis.security.prompt_injection_detected = True

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "security_review_001")
    assert recommendation.priority == "high"
    assert recommendation.owner_role == "Security Reviewer"


def test_decreasing_revenue_trend_produces_revenue_review() -> None:
    analysis = _minimal_analysis_response()
    analysis.trend_analysis.revenue_trend.direction = "decreasing"
    analysis.trend_analysis.revenue_trend.start_value = 200.0
    analysis.trend_analysis.revenue_trend.end_value = 100.0
    analysis.trend_analysis.revenue_trend.absolute_change = -100.0
    analysis.trend_analysis.revenue_trend.percent_change = -50.0

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "revenue_trend_review_001")
    assert recommendation.business_area == "revenue_performance"
    assert "monthly_net_revenue_trend" in recommendation.related_chart_ids


def test_decreasing_order_count_trend_produces_volume_review() -> None:
    analysis = _minimal_analysis_response()
    analysis.trend_analysis.order_count_trend.direction = "decreasing"
    analysis.trend_analysis.order_count_trend.start_value = 5.0
    analysis.trend_analysis.order_count_trend.end_value = 3.0
    analysis.trend_analysis.order_count_trend.absolute_change = -2.0
    analysis.trend_analysis.order_count_trend.percent_change = -40.0

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "order_volume_review_001")
    assert recommendation.business_area == "demand_generation"
    assert "monthly_order_count_trend" in recommendation.related_chart_ids


def test_increasing_discount_trend_produces_discount_review() -> None:
    analysis = _minimal_analysis_response()
    analysis.trend_analysis.average_discount_trend.direction = "increasing"
    analysis.trend_analysis.average_discount_trend.start_value = 0.1
    analysis.trend_analysis.average_discount_trend.end_value = 0.2
    analysis.trend_analysis.average_discount_trend.absolute_change = 0.1
    analysis.trend_analysis.average_discount_trend.percent_change = 100.0

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "discount_trend_review_001")
    assert recommendation.business_area == "pricing_discipline"
    assert "average_discount_trend" in recommendation.related_chart_ids


def test_forecast_not_ready_produces_readiness_recommendation() -> None:
    analysis = _minimal_analysis_response()
    analysis.forecast_analysis.readiness_status = "not_ready"
    analysis.forecast_analysis.confidence_level = "low"

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "forecast_readiness_001")
    assert recommendation.business_area == "forecasting_readiness"
    assert recommendation.workflow_stage == "forecasting_readiness"


def test_limited_forecast_produces_baseline_review_recommendation() -> None:
    analysis = _minimal_analysis_response()
    analysis.forecast_analysis.readiness_status = "limited"
    analysis.forecast_analysis.confidence_level = "low"

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "baseline_forecast_review_001")
    assert recommendation.business_area == "planning"
    assert "revenue_forecast_baseline" in recommendation.related_chart_ids


def test_declining_revenue_forecast_produces_risk_recommendation() -> None:
    analysis = _minimal_analysis_response()
    forecast = _metric_forecast("revenue", selected_value=150.0, latest_value=200.0)
    analysis.forecast_analysis.revenue_forecast = forecast
    forecast.last_period_forecast.forecast_value = 200.0
    forecast.selected_forecast_value = 150.0

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(plan, "forecast_revenue_risk_001")
    assert recommendation.business_area == "revenue_planning"
    assert "revenue_forecast_baseline" in recommendation.related_chart_ids


def test_increasing_discount_forecast_produces_pressure_recommendation() -> None:
    analysis = _minimal_analysis_response()
    forecast = _metric_forecast(
        "average_discount",
        selected_value=0.2,
        latest_value=0.1,
    )
    analysis.forecast_analysis.average_discount_forecast = forecast
    forecast.last_period_forecast.forecast_value = 0.1
    forecast.selected_forecast_value = 0.2

    plan = generate_recommendation_plan(analysis)

    recommendation = _recommendation_by_id(
        plan,
        "forecast_discount_pressure_001",
    )
    assert recommendation.business_area == "pricing_discipline"
    assert recommendation.workflow_stage == "pricing_discipline"


def test_clean_analysis_returns_empty_recommendation_plan() -> None:
    analysis = _minimal_analysis_response()
    analysis.quality_gate.status = "pass"
    analysis.quality_gate.confidence_level = "high"
    analysis.quality_gate.can_generate_reports = True
    analysis.quality_gate.can_generate_llm_narrative = True
    analysis.quality_gate.human_review_required = False
    analysis.quality_score.score = 100
    analysis.quality_score.grade = "excellent"
    analysis.forecast_analysis.readiness_status = "ready"
    analysis.forecast_analysis.confidence_level = "medium"

    plan = generate_recommendation_plan(analysis)

    assert plan.total_recommendations == 0
    assert plan.recommendations == []


def test_recommendation_ids_are_deterministic_and_unique() -> None:
    analysis = _minimal_analysis_response()
    analysis.quality_gate.status = "warning"
    analysis.data_profile.missing_field_counts = {"region": 1}
    analysis.security.human_review_required = True

    plan = generate_recommendation_plan(analysis)
    recommendation_ids = [
        recommendation.recommendation_id
        for recommendation in plan.recommendations
    ]

    assert recommendation_ids == sorted(recommendation_ids)
    assert len(recommendation_ids) == len(set(recommendation_ids))


def _recommendation_by_id(plan, recommendation_id: str):
    return next(
        recommendation
        for recommendation in plan.recommendations
        if recommendation.recommendation_id == recommendation_id
    )


def _discount_summary(product: str, average_discount: float):
    from insightops.preparation.manipulations import ProductDiscountSummary

    return ProductDiscountSummary(
        product=product,
        average_discount=average_discount,
        discounted_order_count=1,
        total_orders=1,
    )


def _metric_forecast(
    metric: str,
    *,
    selected_value: float,
    latest_value: float,
) -> MetricForecast:
    latest = ForecastPoint(
        period="2026-02",
        metric=metric,
        forecast_value=latest_value,
        method="last_period",
        confidence="low",
        explanation="Uses latest value.",
    )
    selected = ForecastPoint(
        period="2026-02",
        metric=metric,
        forecast_value=selected_value,
        method="moving_average",
        confidence="low",
        explanation="Uses baseline average.",
    )
    return MetricForecast(
        metric=metric,
        next_period="2026-02",
        last_period_forecast=latest,
        moving_average_forecast=selected,
        trend_projection_forecast=selected,
        selected_baseline_method="moving_average",
        selected_forecast_value=selected_value,
        confidence="low",
        warnings=[],
    )
