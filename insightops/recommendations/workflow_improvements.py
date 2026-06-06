from pydantic import BaseModel, Field

from insightops.recommendations.action_plan import RecommendationPlan


class WorkflowImprovement(BaseModel):
    workflow_id: str
    workflow_name: str
    current_issue: str
    proposed_change: str
    expected_benefit: str
    owner_role: str
    follow_up_metric: str
    related_recommendation_ids: list[str] = Field(default_factory=list)


class WorkflowImprovementPlan(BaseModel):
    total_workflows: int
    workflows: list[WorkflowImprovement] = Field(default_factory=list)


def generate_workflow_improvement_plan(
    recommendation_plan: RecommendationPlan,
) -> WorkflowImprovementPlan:
    workflows = [
        _workflow_from_recommendation(recommendation)
        for recommendation in recommendation_plan.recommendations
    ]

    return WorkflowImprovementPlan(
        total_workflows=len(workflows),
        workflows=workflows,
    )


def _workflow_from_recommendation(recommendation) -> WorkflowImprovement:
    return WorkflowImprovement(
        workflow_id=f"{recommendation.recommendation_id}_workflow",
        workflow_name=_workflow_name(recommendation.workflow_stage),
        current_issue=recommendation.problem,
        proposed_change=recommendation.recommended_action,
        expected_benefit=recommendation.expected_impact,
        owner_role=recommendation.owner_role,
        follow_up_metric=recommendation.follow_up_metric,
        related_recommendation_ids=[recommendation.recommendation_id],
    )


def _workflow_name(workflow_stage: str) -> str:
    return workflow_stage.replace("_", " ").title()
