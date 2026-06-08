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
        "## Executive Summary",
        "",
        analysis.insights.summary,
        "",
        "## Decision Readiness",
        "",
        f"- Quality Gate Status: {analysis.quality_gate.status.upper()}",
        f"- Analysis Confidence Level: {analysis.quality_gate.confidence_level.upper()}",
        f"- Forecast Readiness Status: {analysis.forecast_analysis.readiness_status.upper()}",
        f"- Human Auditor Oversight Required: {analysis.quality_gate.human_review_required}",
        "",
        "## KPI Snapshot",
        "",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| Total Net Sales Revenue | ${analysis.kpis.total_revenue:,.2f} |",
        f"| Total Valid Orders | {analysis.kpis.total_orders} |",
        f"| Total Units Sold | {analysis.kpis.total_units_sold} |",
        f"| Average Order Value (AOV) | ${analysis.kpis.average_order_value:,.2f} |",
        "",
        "## Top Findings",
        "",
    ]

    top_insights = analysis.insights.insights[:3]
    if top_insights:
        for insight in top_insights:
            lines.append(f"### {insight.title}")
            lines.append(f"- Message: {insight.message}")
            lines.append(f"- Severity: {insight.severity}")
            lines.append("")
    else:
        lines.append("- No critical findings generated.")
        lines.append("")

    lines.append("## Top Business Actions")
    lines.append("")
    top_actions = analysis.insights.recommended_actions[:3]
    if top_actions:
        for action in top_actions:
            lines.append(f"- {action}")
        lines.append("")
    else:
        lines.append("- No recommended actions.")
        lines.append("")

    lines.append("## Primary Visual Evidence")
    lines.append("")
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
            lines.append(f"### {chart.title}")
            lines.append(f"- Business Question: {chart.business_question}")
            lines.append(f"- Concise Finding: {chart.interpretation}")
            actions = chart.recommended_actions
            single_action = (
                actions[0]
                if (actions and len(actions) > 0)
                else "Use this visual as supporting evidence for the related business recommendation."
            )
            lines.append(f"- Recommended Next Action: {single_action}")
            lines.append("")
    else:
        lines.append("- No primary visual evidence charts generated.")
        lines.append("")

    lines.append("## Forecast Readiness")
    lines.append("")
    total_periods = analysis.trend_analysis.total_periods
    readiness_status = analysis.forecast_analysis.readiness_status
    if total_periods < 2 or readiness_status == "not_ready":
        lines.append(
            f"**Warning**: Historical data is insufficient for reliable trend and forecast projections. Total periods: {total_periods} (minimum 2 periods required). Forecast readiness status: {readiness_status.upper()}."
        )
        lines.append("")
    else:
        lines.append(f"- Historical Monthly Periods: {total_periods}")
        lines.append(f"- Forecast Grain: {analysis.trend_analysis.period_grain}")
        lines.append(
            f"- Forecast Confidence Level: {analysis.forecast_analysis.confidence_level.upper()}"
        )
        lines.append(
            f"- Next Period Projected: {analysis.forecast_analysis.next_period or 'none'}"
        )
        if analysis.forecast_analysis.revenue_forecast:
            lines.append(
                f"- Revenue Forecast: {_format_metric_forecast(analysis.forecast_analysis.revenue_forecast)}"
            )
        lines.append("")

    lines.append("## Data Quality and Limitations")
    lines.append("")
    lines.append(f"- Total rows: {analysis.validation.total_rows}")
    lines.append(f"- Valid rows: {analysis.validation.valid_rows}")
    lines.append(f"- Invalid rows: {analysis.validation.invalid_rows}")
    lines.append(f"- Duplicate order IDs: {analysis.data_profile.duplicate_order_ids}")
    lines.append(
        f"- Missing fields: {_format_mapping(analysis.data_profile.missing_field_counts)}"
    )
    lines.append("")

    # TECHNICAL APPENDIX
    lines.extend(
        [
            "---",
            "## Technical Appendix",
            "",
            "### Source Metadata",
            "",
            f"- Source type: {analysis.source_metadata.source_type}",
            f"- File name: {analysis.source_metadata.file_name}",
            f"- File size bytes: {analysis.source_metadata.file_size_bytes}",
            f"- Collection method: {analysis.source_metadata.collection_method}",
            f"- Record count: {analysis.source_metadata.record_count}",
            f"- Notes: {analysis.source_metadata.notes or 'none'}",
            "",
            "### Validation Details",
            "",
            f"- Total rows: {analysis.validation.total_rows}",
            f"- Valid rows: {analysis.validation.valid_rows}",
            f"- Invalid rows: {analysis.validation.invalid_rows}",
            "",
            "### Data Profile Details",
            "",
            f"- Date range: {_format_date_range(analysis)}",
            f"- Unique customers: {analysis.data_profile.unique_customers}",
            f"- Unique regions: {analysis.data_profile.unique_regions}",
            f"- Unique products: {analysis.data_profile.unique_products}",
            f"- Unique sales reps: {analysis.data_profile.unique_sales_reps}",
            f"- Duplicate order IDs: {analysis.data_profile.duplicate_order_ids}",
            f"- Missing fields: {_format_mapping(analysis.data_profile.missing_field_counts)}",
            f"- Revenue summary: {_format_numeric_summary(analysis.data_profile.revenue_summary)}",
            f"- Quantity summary: {_format_numeric_summary(analysis.data_profile.quantity_summary)}",
            f"- Discount summary: {_format_numeric_summary(analysis.data_profile.discount_summary)}",
            f"- Unit price summary: {_format_numeric_summary(analysis.data_profile.unit_price_summary)}",
            "",
            "### Quality Score Details",
            "",
            f"- Score: {analysis.quality_score.score}",
            f"- Grade: {analysis.quality_score.grade}",
            f"- Issues: {_format_list(analysis.quality_score.issues)}",
            f"- Recommendations: {_format_list(analysis.quality_score.recommendations)}",
            "",
            "### Transformation Lineage",
            "",
            *_format_transformation_lines(analysis),
            "",
            "### Manipulation Summary",
            "",
            f"- Monthly revenue: {_format_points(analysis.manipulation_summary.monthly_revenue)}",
            f"- Ranked regions: {_format_points(analysis.manipulation_summary.ranked_regions)}",
            f"- Ranked products: {_format_points(analysis.manipulation_summary.ranked_products)}",
            f"- Ranked sales reps: {_format_points(analysis.manipulation_summary.ranked_sales_reps)}",
            f"- Discount summary by product: {_format_discount_summary(analysis)}",
            "",
        ]
    )

    lines.extend(
        [
            "### Anomalies",
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
                f"value={anomaly.value} | "
                f"method={anomaly.method or 'rule'} | "
                f"threshold={_format_optional_float(anomaly.threshold)} | "
                f"comparison={anomaly.comparison or 'none'} | "
                f"{anomaly.message}"
            )
    else:
        lines.append("- No anomalies detected.")
    lines.append("")

    lines.extend(["### Audit Events", ""])
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


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return "none"
    return f"{value:.2f}"


def _format_optional_percent(value: float | None) -> str:
    if value is None:
        return "none"
    return f"{value:.2f}%"


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

    return ", ".join(f"{key}={value}" for key, value in sorted(values.items()))


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


def _format_transformation_lines(analysis: AnalysisResponse) -> list[str]:
    if not analysis.transformation_log.entries:
        return ["- No transformation steps."]

    return [
        (
            f"- {entry.step_name}: {entry.description} "
            f"(records affected: {entry.records_affected})"
        )
        for entry in analysis.transformation_log.entries
    ]


def _format_points(points) -> str:
    if not points:
        return "none"

    return ", ".join(
        f"{point.label}={_format_evidence_value(point.value)}" for point in points
    )


def _format_trend_points(analysis: AnalysisResponse) -> str:
    if not analysis.trend_analysis.data:
        return "none"

    return "; ".join(
        (
            f"{point.period}: revenue=${point.revenue:.2f}, "
            f"orders={point.order_count}, units={point.units_sold}, "
            f"aov=${point.average_order_value:.2f}, "
            f"avg_discount={point.average_discount:.2f}"
        )
        for point in analysis.trend_analysis.data
    )


def _format_trend_summary(summary) -> str:
    return (
        f"start={summary.start_value:.2f}, end={summary.end_value:.2f}, "
        f"change={summary.absolute_change:.2f}, "
        f"percent_change={_format_optional_percent(summary.percent_change)}, "
        f"direction={summary.direction}, "
        f"interpretation={summary.interpretation}"
    )


def _format_metric_forecast(forecast) -> str:
    if forecast is None:
        return "none"

    return (
        f"next_period={forecast.next_period}, "
        f"selected_method={forecast.selected_baseline_method}, "
        f"selected_value={forecast.selected_forecast_value:.2f}, "
        f"confidence={forecast.confidence}"
    )


def _format_discount_summary(analysis: AnalysisResponse) -> str:
    if not analysis.manipulation_summary.discount_summary_by_product:
        return "none"

    return "; ".join(
        (
            f"{item.product}: average_discount={item.average_discount:.2f}, "
            f"discounted_orders={item.discounted_order_count}, "
            f"total_orders={item.total_orders}"
        )
        for item in analysis.manipulation_summary.discount_summary_by_product
    )
