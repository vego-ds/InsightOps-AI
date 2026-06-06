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
        "## Data Profile",
        "",
        f"- Date range: {_format_date_range(analysis)}",
        f"- Unique customers: {analysis.data_profile.unique_customers}",
        f"- Unique regions: {analysis.data_profile.unique_regions}",
        f"- Unique products: {analysis.data_profile.unique_products}",
        f"- Unique sales reps: {analysis.data_profile.unique_sales_reps}",
        f"- Duplicate order IDs: {analysis.data_profile.duplicate_order_ids}",
        (
            "- Missing fields: "
            f"{_format_mapping(analysis.data_profile.missing_field_counts)}"
        ),
        (
            "- Revenue summary: "
            f"{_format_numeric_summary(analysis.data_profile.revenue_summary)}"
        ),
        (
            "- Quantity summary: "
            f"{_format_numeric_summary(analysis.data_profile.quantity_summary)}"
        ),
        (
            "- Discount summary: "
            f"{_format_numeric_summary(analysis.data_profile.discount_summary)}"
        ),
        (
            "- Unit price summary: "
            f"{_format_numeric_summary(analysis.data_profile.unit_price_summary)}"
        ),
        "",
        "## Quality Score",
        "",
        f"- Score: {analysis.quality_score.score}",
        f"- Grade: {analysis.quality_score.grade}",
        f"- Issues: {_format_list(analysis.quality_score.issues)}",
        (
            "- Recommendations: "
            f"{_format_list(analysis.quality_score.recommendations)}"
        ),
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


def _format_date_range(analysis: AnalysisResponse) -> str:
    if not analysis.data_profile.date_start or not analysis.data_profile.date_end:
        return "none"
    return (
        f"{analysis.data_profile.date_start.isoformat()} to "
        f"{analysis.data_profile.date_end.isoformat()}"
    )


def _format_mapping(values: dict[str, int]) -> str:
    if not values:
        return "none"

    return ", ".join(
        f"{key}={value}" for key, value in sorted(values.items())
    )


def _format_list(values: list[str]) -> str:
    if not values:
        return "none"

    return "; ".join(values)


def _format_numeric_summary(summary) -> str:
    return (
        f"min={summary.minimum:.2f}, max={summary.maximum:.2f}, "
        f"mean={summary.mean:.2f}, median={summary.median:.2f}, "
        f"std_dev={summary.standard_deviation:.2f}"
    )
