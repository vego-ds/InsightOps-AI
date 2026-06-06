from pydantic import BaseModel, Field

from insightops.profiling.data_profile import SalesDataProfile
from insightops.profiling.quality_score import DataQualityScore
from insightops.security.policy import SecurityScanResult
from insightops.validation.report import ValidationReport


class QualityGateResult(BaseModel):
    status: str
    confidence_level: str
    can_generate_kpis: bool
    can_generate_charts: bool
    can_generate_reports: bool
    can_generate_llm_narrative: bool
    human_review_required: bool
    reasons: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)


def evaluate_quality_gate(
    validation_report: ValidationReport,
    data_profile: SalesDataProfile,
    quality_score: DataQualityScore,
    security: SecurityScanResult,
) -> QualityGateResult:
    reasons: list[str] = []
    required_actions: list[str] = []
    status = "pass"
    confidence_level = "high"
    can_generate_kpis = True
    can_generate_charts = True
    can_generate_reports = True
    can_generate_llm_narrative = True
    human_review_required = False

    if validation_report.valid_rows == 0:
        status = "blocked"
        confidence_level = "low"
        can_generate_kpis = False
        can_generate_charts = False
        can_generate_reports = False
        can_generate_llm_narrative = False
        human_review_required = True
        reasons.append("No valid rows are available for analysis.")
        required_actions.append(
            "Provide at least one valid sales record before analysis."
        )

    if quality_score.score < 50:
        status = "blocked"
        confidence_level = "low"
        can_generate_reports = False
        can_generate_llm_narrative = False
        human_review_required = True
        reasons.append(
            f"Quality score {quality_score.score} is below the blocking threshold."
        )
        required_actions.append(
            "Improve data quality score before executive reporting."
        )

    if status != "blocked" and quality_score.grade == "fair":
        status = "warning"
        confidence_level = "medium"
        can_generate_llm_narrative = False
        reasons.append("Quality grade is fair, reducing analysis confidence.")
        required_actions.append(
            "Review quality score issues before executive decisions."
        )

    if validation_report.invalid_rows > 0:
        if status == "pass":
            status = "warning"
            confidence_level = "medium"
        reasons.append(f"{validation_report.invalid_rows} invalid rows detected.")
        required_actions.append("Review invalid rows before executive reporting.")

    if data_profile.duplicate_order_ids > 0:
        if status == "pass":
            status = "warning"
            confidence_level = "medium"
        reasons.append(
            f"{data_profile.duplicate_order_ids} duplicate order IDs detected."
        )
        required_actions.append(
            "Review duplicate order IDs before executive decisions."
        )

    missing_field_total = sum(data_profile.missing_field_counts.values())
    if missing_field_total > 0:
        if status == "pass":
            status = "warning"
            confidence_level = "medium"
        reasons.append(f"{missing_field_total} missing required field values detected.")
        required_actions.append("Correct missing values at the source.")

    if security.prompt_injection_detected:
        can_generate_llm_narrative = False
        human_review_required = True
        reasons.append("Prompt injection style text was detected.")
        required_actions.append("Complete human security review for flagged records.")

    if security.human_review_required:
        can_generate_llm_narrative = False
        human_review_required = True
        reasons.append("Human review is required by the security scan.")
        required_actions.append("Resolve security review before using LLM narrative.")

    if status == "pass" and not reasons:
        reasons.append("Data quality gate passed with high confidence.")

    return QualityGateResult(
        status=status,
        confidence_level=confidence_level,
        can_generate_kpis=can_generate_kpis,
        can_generate_charts=can_generate_charts,
        can_generate_reports=can_generate_reports,
        can_generate_llm_narrative=can_generate_llm_narrative,
        human_review_required=human_review_required,
        reasons=_deduplicate(reasons),
        required_actions=_deduplicate(required_actions),
    )


def _deduplicate(values: list[str]) -> list[str]:
    deduplicated: list[str] = []
    for value in values:
        if value not in deduplicated:
            deduplicated.append(value)
    return deduplicated
