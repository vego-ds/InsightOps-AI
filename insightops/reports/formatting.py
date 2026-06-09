from insightops.api.contracts import AnalysisResponse


def format_evidence(evidence: dict[str, str | int | float | bool]) -> str:
    if not evidence:
        return "none"

    return ", ".join(
        f"{key}={format_evidence_value(value)}"
        for key, value in sorted(evidence.items())
    )


def format_evidence_value(value: str | int | float | bool) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def format_optional_float(value: float | None) -> str:
    if value is None:
        return "none"
    return f"{value:.2f}"


def format_optional_percent(value: float | None) -> str:
    if value is None:
        return "none"
    return f"{value:.2f}%"


def format_date_range(analysis: AnalysisResponse) -> str:
    if not analysis.data_profile.date_start or not analysis.data_profile.date_end:
        return "none"
    return (
        f"{analysis.data_profile.date_start.isoformat()} to "
        f"{analysis.data_profile.date_end.isoformat()}"
    )


def format_mapping(values: dict[str, int]) -> str:
    if not values:
        return "none"

    return ", ".join(f"{key}={value}" for key, value in sorted(values.items()))


def format_list(values: list[str]) -> str:
    if not values:
        return "none"

    return "; ".join(values)


def format_numeric_summary(summary) -> str:
    return (
        f"min={summary.minimum:.2f}, max={summary.maximum:.2f}, "
        f"mean={summary.mean:.2f}, median={summary.median:.2f}, "
        f"std_dev={summary.standard_deviation:.2f}"
    )


def format_transformation_items(analysis: AnalysisResponse) -> list[str]:
    if not analysis.transformation_log.entries:
        return ["No transformation steps."]

    return [
        (
            f"{entry.step_name}: {entry.description} "
            f"(records affected: {entry.records_affected})"
        )
        for entry in analysis.transformation_log.entries
    ]


def format_points(points) -> str:
    if not points:
        return "none"

    return ", ".join(
        f"{point.label}={format_evidence_value(point.value)}" for point in points
    )


def format_trend_points(analysis: AnalysisResponse) -> str:
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


def format_trend_summary(summary) -> str:
    return (
        f"start={summary.start_value:.2f}, end={summary.end_value:.2f}, "
        f"change={summary.absolute_change:.2f}, "
        f"percent_change={format_optional_percent(summary.percent_change)}, "
        f"direction={summary.direction}, "
        f"interpretation={summary.interpretation}"
    )


def format_metric_forecast(forecast) -> str:
    if forecast is None:
        return "none"

    return (
        f"next_period={forecast.next_period}, "
        f"selected_method={forecast.selected_baseline_method}, "
        f"selected_value={forecast.selected_forecast_value:.2f}, "
        f"confidence={forecast.confidence}"
    )


def format_discount_summary(analysis: AnalysisResponse) -> str:
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
