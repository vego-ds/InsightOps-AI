from pydantic import BaseModel, Field


class NarrativeSourceEvidence(BaseModel):
    summary: str
    insight_count: int
    recommended_action_count: int
    total_revenue: float
    total_orders: int
    total_anomalies: int
    invalid_rows: int
    human_review_required: bool


class ExecutiveNarrative(BaseModel):
    mode: str
    title: str
    narrative: str
    source_evidence: NarrativeSourceEvidence
    warnings: list[str] = Field(default_factory=list)
