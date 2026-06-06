from tests.test_markdown_report import _minimal_analysis_response

from insightops.anomalies.detector import SalesAnomaly
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


def test_clean_analysis_returns_empty_recommendation_plan() -> None:
    analysis = _minimal_analysis_response()
    analysis.quality_gate.status = "pass"
    analysis.quality_gate.confidence_level = "high"
    analysis.quality_gate.can_generate_reports = True
    analysis.quality_gate.can_generate_llm_narrative = True
    analysis.quality_gate.human_review_required = False
    analysis.quality_score.score = 100
    analysis.quality_score.grade = "excellent"

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
