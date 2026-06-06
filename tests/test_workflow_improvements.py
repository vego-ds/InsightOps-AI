from insightops.recommendations.action_plan import (
    BusinessRecommendation,
    RecommendationPlan,
)
from insightops.recommendations.workflow_improvements import (
    WorkflowImprovementPlan,
    generate_workflow_improvement_plan,
)


def test_workflow_improvements_are_generated_from_recommendations() -> None:
    recommendation = BusinessRecommendation(
        recommendation_id="data_quality_001",
        priority="medium",
        business_area="data_quality",
        title="Improve data quality",
        problem="Data quality issue.",
        evidence={"quality_score": 70},
        recommended_action="Clean data before reporting.",
        expected_impact="Better reporting confidence.",
        workflow_stage="data_intake",
        owner_role="Data Operations Lead",
        implementation_difficulty="medium",
        follow_up_metric="quality_score",
    )

    plan = generate_workflow_improvement_plan(
        RecommendationPlan(
            total_recommendations=1,
            recommendations=[recommendation],
        )
    )

    assert isinstance(plan, WorkflowImprovementPlan)
    assert plan.total_workflows == 1
    assert plan.workflows[0].workflow_id == "data_quality_001_workflow"
    assert plan.workflows[0].workflow_name == "Data Intake"
    assert plan.workflows[0].related_recommendation_ids == ["data_quality_001"]


def test_empty_recommendation_plan_returns_empty_workflow_plan() -> None:
    plan = generate_workflow_improvement_plan(
        RecommendationPlan(total_recommendations=0, recommendations=[])
    )

    assert plan.total_workflows == 0
    assert plan.workflows == []
