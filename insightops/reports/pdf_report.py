from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from insightops.api.contracts import AnalysisResponse
from insightops.reports.artifacts import ReportArtifact
from insightops.reports.formatting import (
    format_date_range,
    format_discount_summary,
    format_list,
    format_mapping,
    format_metric_forecast,
    format_numeric_summary,
    format_optional_float,
    format_points,
    format_transformation_items,
)


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

    _add_heading(story, styles, "Executive Summary")
    _add_paragraph(story, styles, analysis.insights.summary)

    _add_heading(story, styles, "Decision Readiness")
    _add_bullets(
        story,
        styles,
        [
            f"Quality Gate Status: {analysis.quality_gate.status.upper()}",
            f"Analysis Confidence Level: {analysis.quality_gate.confidence_level.upper()}",
            f"Forecast Readiness Status: {analysis.forecast_analysis.readiness_status.upper()}",
            f"Human Auditor Oversight Required: {analysis.quality_gate.human_review_required}",
        ],
    )

    _add_heading(story, styles, "KPI Snapshot")
    _add_bullets(
        story,
        styles,
        [
            f"Total Net Sales Revenue: ${analysis.kpis.total_revenue:,.2f}",
            f"Total Valid Orders: {analysis.kpis.total_orders}",
            f"Total Units Sold: {analysis.kpis.total_units_sold}",
            f"Average Order Value (AOV): ${analysis.kpis.average_order_value:,.2f}",
        ],
    )

    _add_heading(story, styles, "Top Findings")
    top_insights = analysis.insights.insights[:3]
    if top_insights:
        for insight in top_insights:
            _add_paragraph(story, styles, insight.title, style_name="Heading3")
            _add_bullets(
                story,
                styles,
                [
                    f"Message: {insight.message}",
                    f"Severity: {insight.severity}",
                ],
            )
    else:
        _add_bullets(story, styles, ["No critical findings generated."])

    _add_heading(story, styles, "Top Business Actions")
    top_actions = analysis.insights.recommended_actions[:3]
    _add_bullets(
        story,
        styles,
        top_actions or ["No recommended actions."],
    )

    _add_heading(story, styles, "Primary Visual Evidence")
    primary_ids = [
        "revenue_by_region",
        "revenue_by_product",
        "revenue_by_sales_rep",
        "pareto_revenue_by_product",
        "data_quality_score",
    ]
    primary_charts = [
        c for c in (analysis.charts.charts or []) if c.chart_id in primary_ids
    ]
    if primary_charts:
        for chart in primary_charts:
            _add_paragraph(story, styles, chart.title, style_name="Heading3")
            actions = chart.recommended_actions
            single_action = (
                actions[0]
                if (actions and len(actions) > 0)
                else "Use this visual as supporting evidence for the related business recommendation."
            )
            _add_bullets(
                story,
                styles,
                [
                    f"Business Question: {chart.business_question}",
                    f"Concise Finding: {chart.interpretation}",
                    f"Recommended Next Action: {single_action}",
                ],
            )
    else:
        _add_bullets(story, styles, ["No primary visual evidence charts generated."])

    _add_heading(story, styles, "Forecast Readiness")
    total_periods = analysis.trend_analysis.total_periods
    readiness_status = analysis.forecast_analysis.readiness_status
    if total_periods < 2 or readiness_status == "not_ready":
        _add_paragraph(
            story,
            styles,
            f"Warning: Historical data is insufficient for reliable trend and forecast projections. Total periods: {total_periods} (minimum 2 periods required). Forecast readiness status: {readiness_status.upper()}.",
        )
    else:
        _add_bullets(
            story,
            styles,
            [
                f"Historical Monthly Periods: {total_periods}",
                f"Forecast Grain: {analysis.trend_analysis.period_grain}",
                f"Forecast Confidence Level: {analysis.forecast_analysis.confidence_level.upper()}",
                f"Next Period Projected: {analysis.forecast_analysis.next_period or 'none'}",
                f"Revenue Forecast: {format_metric_forecast(analysis.forecast_analysis.revenue_forecast)}",
            ],
        )

    _add_heading(story, styles, "Data Quality and Limitations")
    _add_bullets(
        story,
        styles,
        [
            f"Total rows: {analysis.validation.total_rows}",
            f"Valid rows: {analysis.validation.valid_rows}",
            f"Invalid rows: {analysis.validation.invalid_rows}",
            f"Duplicate order IDs: {analysis.data_profile.duplicate_order_ids}",
            f"Missing fields: {format_mapping(analysis.data_profile.missing_field_counts)}",
        ],
    )

    # TECHNICAL APPENDIX
    _add_heading(story, styles, "Technical Appendix")

    _add_heading(story, styles, "Source Metadata", level=3)
    _add_bullets(
        story,
        styles,
        [
            f"Source type: {analysis.source_metadata.source_type}",
            f"File name: {analysis.source_metadata.file_name}",
            f"File size bytes: {analysis.source_metadata.file_size_bytes}",
            f"Collection method: {analysis.source_metadata.collection_method}",
            f"Record count: {analysis.source_metadata.record_count}",
            f"Notes: {analysis.source_metadata.notes or 'none'}",
        ],
    )

    _add_heading(story, styles, "Validation Details", level=3)
    _add_bullets(
        story,
        styles,
        [
            f"Total rows: {analysis.validation.total_rows}",
            f"Valid rows: {analysis.validation.valid_rows}",
            f"Invalid rows: {analysis.validation.invalid_rows}",
        ],
    )

    _add_heading(story, styles, "Data Profile Details", level=3)
    _add_bullets(
        story,
        styles,
        [
            f"Date range: {format_date_range(analysis)}",
            f"Unique customers: {analysis.data_profile.unique_customers}",
            f"Unique regions: {analysis.data_profile.unique_regions}",
            f"Unique products: {analysis.data_profile.unique_products}",
            f"Unique sales reps: {analysis.data_profile.unique_sales_reps}",
            f"Duplicate order IDs: {analysis.data_profile.duplicate_order_ids}",
            f"Missing fields: {format_mapping(analysis.data_profile.missing_field_counts)}",
            f"Revenue summary: {format_numeric_summary(analysis.data_profile.revenue_summary)}",
            f"Quantity summary: {format_numeric_summary(analysis.data_profile.quantity_summary)}",
            f"Discount summary: {format_numeric_summary(analysis.data_profile.discount_summary)}",
            f"Unit price summary: {format_numeric_summary(analysis.data_profile.unit_price_summary)}",
        ],
    )

    _add_heading(story, styles, "Quality Score Details", level=3)
    _add_bullets(
        story,
        styles,
        [
            f"Score: {analysis.quality_score.score}",
            f"Grade: {analysis.quality_score.grade}",
            f"Issues: {format_list(analysis.quality_score.issues)}",
            f"Recommendations: {format_list(analysis.quality_score.recommendations)}",
        ],
    )

    _add_heading(story, styles, "Transformation Lineage", level=3)
    _add_bullets(story, styles, format_transformation_items(analysis))

    _add_heading(story, styles, "Manipulation Summary", level=3)
    _add_bullets(
        story,
        styles,
        [
            f"Monthly revenue: {format_points(analysis.manipulation_summary.monthly_revenue)}",
            f"Ranked regions: {format_points(analysis.manipulation_summary.ranked_regions)}",
            f"Ranked products: {format_points(analysis.manipulation_summary.ranked_products)}",
            f"Ranked sales reps: {format_points(analysis.manipulation_summary.ranked_sales_reps)}",
            f"Discount summary by product: {format_discount_summary(analysis)}",
        ],
    )

    _add_heading(story, styles, "Anomalies", level=3)
    anomaly_items = [f"Total anomalies: {analysis.anomalies.total_anomalies}"]
    if analysis.anomalies.anomalies:
        anomaly_items.extend(
            (
                f"{anomaly.anomaly_type} | severity={anomaly.severity} | "
                f"order_id={anomaly.order_id} | field={anomaly.field} | "
                f"value={anomaly.value} | method={anomaly.method or 'rule'} | "
                f"threshold={format_optional_float(anomaly.threshold)} | "
                f"comparison={anomaly.comparison or 'none'} | "
                f"{anomaly.message}"
            )
            for anomaly in analysis.anomalies.anomalies
        )
    else:
        anomaly_items.append("No anomalies detected.")
    _add_bullets(story, styles, anomaly_items)

    _add_heading(story, styles, "Audit Events", level=3)
    if analysis.audit_events:
        _add_bullets(
            story,
            styles,
            [f"{event.event_type}: {event.message}" for event in analysis.audit_events],
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
