from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from insightops.api.contracts import AnalysisResponse
from insightops.reports.artifacts import ReportArtifact


def generate_executive_pdf_report(
    analysis: AnalysisResponse,
    output_dir: str,
    report_id: str = "executive_sales_report",
) -> ReportArtifact:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_name = f"{report_id}.pdf"
    file_path = output_path / file_name

    document = SimpleDocTemplate(str(file_path), pagesize=letter)
    document.build(_build_report_story(analysis))

    return ReportArtifact(
        report_id=report_id,
        title="Executive Sales Report",
        file_path=str(file_path),
        file_name=file_name,
        format="pdf",
    )


def _build_report_story(analysis: AnalysisResponse) -> list:
    styles = getSampleStyleSheet()
    story: list = []

    _add_heading(story, styles, "Executive Sales Report", level=1)
    _add_heading(story, styles, "Summary")
    _add_paragraph(story, styles, analysis.insights.summary)

    _add_heading(story, styles, "Data Quality")
    _add_bullets(
        story,
        styles,
        [
            f"Total rows: {analysis.validation.total_rows}",
            f"Valid rows: {analysis.validation.valid_rows}",
            f"Invalid rows: {analysis.validation.invalid_rows}",
        ],
    )

    _add_heading(story, styles, "Data Profile")
    _add_bullets(
        story,
        styles,
        [
            f"Date range: {_format_date_range(analysis)}",
            f"Unique customers: {analysis.data_profile.unique_customers}",
            f"Unique regions: {analysis.data_profile.unique_regions}",
            f"Unique products: {analysis.data_profile.unique_products}",
            f"Unique sales reps: {analysis.data_profile.unique_sales_reps}",
            f"Duplicate order IDs: {analysis.data_profile.duplicate_order_ids}",
            (
                "Missing fields: "
                f"{_format_mapping(analysis.data_profile.missing_field_counts)}"
            ),
            (
                "Revenue summary: "
                f"{_format_numeric_summary(analysis.data_profile.revenue_summary)}"
            ),
            (
                "Quantity summary: "
                f"{_format_numeric_summary(analysis.data_profile.quantity_summary)}"
            ),
            (
                "Discount summary: "
                f"{_format_numeric_summary(analysis.data_profile.discount_summary)}"
            ),
            (
                "Unit price summary: "
                f"{_format_numeric_summary(analysis.data_profile.unit_price_summary)}"
            ),
        ],
    )

    _add_heading(story, styles, "Quality Score")
    _add_bullets(
        story,
        styles,
        [
            f"Score: {analysis.quality_score.score}",
            f"Grade: {analysis.quality_score.grade}",
            f"Issues: {_format_list(analysis.quality_score.issues)}",
            (
                "Recommendations: "
                f"{_format_list(analysis.quality_score.recommendations)}"
            ),
        ],
    )

    _add_heading(story, styles, "Security")
    security_items = [
        (
            "prompt_injection_detected: "
            f"{analysis.security.prompt_injection_detected}"
        ),
        f"human_review_required: {analysis.security.human_review_required}",
    ]
    if analysis.security.flagged_fields:
        security_items.append(
            "flagged fields: " + ", ".join(analysis.security.flagged_fields)
        )
    _add_bullets(story, styles, security_items)

    _add_heading(story, styles, "KPI Summary")
    _add_bullets(
        story,
        styles,
        [
            f"Total revenue: ${analysis.kpis.total_revenue:.2f}",
            f"Total orders: {analysis.kpis.total_orders}",
            f"Total units sold: {analysis.kpis.total_units_sold}",
            (
                "Average order value: "
                f"${analysis.kpis.average_order_value:.2f}"
            ),
        ],
    )

    _add_heading(story, styles, "Anomalies")
    anomaly_items = [f"Total anomalies: {analysis.anomalies.total_anomalies}"]
    if analysis.anomalies.anomalies:
        anomaly_items.extend(
            (
                f"{anomaly.anomaly_type} | severity={anomaly.severity} | "
                f"order_id={anomaly.order_id} | field={anomaly.field} | "
                f"value={anomaly.value} | {anomaly.message}"
            )
            for anomaly in analysis.anomalies.anomalies
        )
    else:
        anomaly_items.append("No anomalies detected.")
    _add_bullets(story, styles, anomaly_items)

    _add_heading(story, styles, "Executive Insights")
    if analysis.insights.insights:
        for insight in analysis.insights.insights:
            _add_paragraph(story, styles, insight.title, style_name="Heading3")
            _add_bullets(
                story,
                styles,
                [
                    f"Severity: {insight.severity}",
                    f"Message: {insight.message}",
                    f"Evidence: {_format_evidence(insight.evidence)}",
                ],
            )
    else:
        _add_bullets(story, styles, ["No executive insights generated."])

    _add_heading(story, styles, "Recommended Actions")
    _add_bullets(
        story,
        styles,
        analysis.insights.recommended_actions or ["No recommended actions."],
    )

    _add_heading(story, styles, "Audit Events")
    if analysis.audit_events:
        _add_bullets(
            story,
            styles,
            [
                f"{event.event_type}: {event.message}"
                for event in analysis.audit_events
            ],
        )
    else:
        _add_bullets(story, styles, ["No audit events."])

    return story


def _add_heading(
    story: list,
    styles,
    text: str,
    *,
    level: int = 2,
) -> None:
    style_name = "Title" if level == 1 else "Heading2"
    _add_paragraph(story, styles, text, style_name=style_name)


def _add_paragraph(
    story: list,
    styles,
    text: str,
    *,
    style_name: str = "BodyText",
) -> None:
    story.append(Paragraph(text, styles[style_name]))
    story.append(Spacer(1, 8))


def _add_bullets(story: list, styles, items: list[str]) -> None:
    for item in items:
        _add_paragraph(story, styles, f"- {item}")


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
