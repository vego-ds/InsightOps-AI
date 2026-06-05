from pathlib import Path

from insightops.api.contracts import AnalysisResponse
from insightops.reports.artifacts import ReportArtifact


def generate_executive_markdown_report(
    analysis: AnalysisResponse,
    output_dir: str,
    report_id: str = "executive_sales_report",
) -> ReportArtifact:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_name = f"{report_id}.md"
    file_path = output_path / file_name
    file_path.write_text(_build_report_markdown(analysis), encoding="utf-8")

    return ReportArtifact(
        report_id=report_id,
        title="Executive Sales Report",
        file_path=str(file_path),
        file_name=file_name,
        format="markdown",
    )


def _build_report_markdown(analysis: AnalysisResponse) -> str:
    lines = [
        "# Executive Sales Report",
        "",
        "## Summary",
        "",
        analysis.insights.summary,
        "",
        "## Data Quality",
        "",
        f"- Total rows: {analysis.validation.total_rows}",
        f"- Valid rows: {analysis.validation.valid_rows}",
        f"- Invalid rows: {analysis.validation.invalid_rows}",
        "",
        "## Security",
        "",
        (
            "- prompt_injection_detected: "
            f"{analysis.security.prompt_injection_detected}"
        ),
        f"- human_review_required: {analysis.security.human_review_required}",
    ]

    if analysis.security.flagged_fields:
        lines.append(
            "- flagged fields: " + ", ".join(analysis.security.flagged_fields)
        )

    lines.extend(
        [
            "",
            "## KPI Summary",
            "",
            f"- Total revenue: ${analysis.kpis.total_revenue:.2f}",
            f"- Total orders: {analysis.kpis.total_orders}",
            f"- Total units sold: {analysis.kpis.total_units_sold}",
            (
                "- Average order value: "
                f"${analysis.kpis.average_order_value:.2f}"
            ),
            "",
            "## Anomalies",
            "",
            f"- Total anomalies: {analysis.anomalies.total_anomalies}",
        ]
    )

    if analysis.anomalies.anomalies:
        for anomaly in analysis.anomalies.anomalies:
            lines.append(
                "- "
                f"{anomaly.anomaly_type} | severity={anomaly.severity} | "
                f"order_id={anomaly.order_id} | field={anomaly.field} | "
                f"value={anomaly.value} | {anomaly.message}"
            )
    else:
        lines.append("- No anomalies detected.")

    lines.extend(["", "## Executive Insights", ""])

    if analysis.insights.insights:
        for insight in analysis.insights.insights:
            lines.append(f"### {insight.title}")
            lines.append("")
            lines.append(f"- Severity: {insight.severity}")
            lines.append(f"- Message: {insight.message}")
            lines.append(f"- Evidence: {_format_evidence(insight.evidence)}")
            lines.append("")
    else:
        lines.append("- No executive insights generated.")
        lines.append("")

    lines.extend(["## Recommended Actions", ""])

    if analysis.insights.recommended_actions:
        for action in analysis.insights.recommended_actions:
            lines.append(f"- {action}")
    else:
        lines.append("- No recommended actions.")

    lines.extend(["", "## Audit Events", ""])

    if analysis.audit_events:
        for event in analysis.audit_events:
            lines.append(f"- {event.event_type}: {event.message}")
    else:
        lines.append("- No audit events.")

    lines.append("")
    return "\n".join(lines)


def _format_evidence(evidence: dict[str, str | int | float | bool]) -> str:
    if not evidence:
        return "none"

    return ", ".join(
        f"{key}={_format_evidence_value(value)}"
        for key, value in sorted(evidence.items())
    )


def _format_evidence_value(value: str | int | float | bool) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)
