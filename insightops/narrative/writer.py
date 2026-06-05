from insightops.api.contracts import AnalysisResponse
from insightops.narrative.contracts import (
    ExecutiveNarrative,
    NarrativeSourceEvidence,
)


def generate_deterministic_narrative(
    analysis: AnalysisResponse,
) -> ExecutiveNarrative:
    evidence = _build_source_evidence(analysis)
    warnings = _build_warnings(analysis)
    actions = analysis.insights.recommended_actions
    action_text = (
        " Recommended actions: " + "; ".join(actions) + "."
        if actions
        else " No recommended actions were generated."
    )

    narrative = (
        f"{analysis.insights.summary} "
        f"Revenue totaled ${analysis.kpis.total_revenue:.2f} across "
        f"{analysis.kpis.total_orders} orders. "
        f"The validation step found {analysis.validation.invalid_rows} "
        f"invalid rows out of {analysis.validation.total_rows}. "
        f"Anomaly detection found {analysis.anomalies.total_anomalies} "
        f"anomalies. "
        f"Human security review required: "
        f"{analysis.security.human_review_required}."
        f"{action_text}"
    )

    return ExecutiveNarrative(
        mode="deterministic",
        title="Executive Sales Narrative",
        narrative=narrative,
        source_evidence=evidence,
        warnings=warnings,
    )


def _build_source_evidence(
    analysis: AnalysisResponse,
) -> NarrativeSourceEvidence:
    return NarrativeSourceEvidence(
        summary=analysis.insights.summary,
        insight_count=len(analysis.insights.insights),
        recommended_action_count=len(analysis.insights.recommended_actions),
        total_revenue=analysis.kpis.total_revenue,
        total_orders=analysis.kpis.total_orders,
        total_anomalies=analysis.anomalies.total_anomalies,
        invalid_rows=analysis.validation.invalid_rows,
        human_review_required=analysis.security.human_review_required,
    )


def _build_warnings(analysis: AnalysisResponse) -> list[str]:
    warnings: list[str] = []

    if analysis.validation.invalid_rows > 0:
        warnings.append("Invalid sales rows require review.")

    if analysis.security.human_review_required:
        warnings.append("Security scan requires human review.")

    if analysis.anomalies.total_anomalies > 0:
        warnings.append("Sales anomalies require investigation.")

    return warnings
