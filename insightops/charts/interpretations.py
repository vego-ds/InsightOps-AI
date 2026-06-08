from insightops.profiling.quality_score import DataQualityScore


def revenue_share(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100, 2)


def top_category_interpretation(
    *,
    category_name: str,
    grouped_values: dict[str, float],
    metric_label: str,
) -> str:
    if not grouped_values:
        return f"No {metric_label} data is available by {category_name}."

    label, value = sorted(
        grouped_values.items(),
        key=lambda item: (-item[1], item[0]),
    )[0]
    share = revenue_share(value, sum(grouped_values.values()))
    return (
        f"{label} leads {metric_label} by {category_name} with "
        f"{value:.2f}, representing {share:.2f}% of the total."
    )


def trend_direction_interpretation(points: list[tuple[str, float]]) -> str:
    if len(points) < 2:
        return "Insufficient monthly data is available to determine a trend."

    first_label, first_value = points[0]
    last_label, last_value = points[-1]
    if last_value > first_value:
        direction = "increasing"
    elif last_value < first_value:
        direction = "decreasing"
    else:
        direction = "flat"

    return f"Monthly net revenue is {direction} from {first_label} to {last_label}."


def discount_concentration_interpretation(
    product_discounts: list[tuple[str, float]],
) -> str:
    if not product_discounts:
        return "No product discount data is available."

    product, average_discount = sorted(
        product_discounts,
        key=lambda item: (-item[1], item[0]),
    )[0]
    return f"{product} has the highest average discount at {average_discount:.2f}."


def anomaly_severity_interpretation(
    severity_counts: dict[str, int],
) -> str:
    high_count = severity_counts.get("high", 0)
    if not severity_counts:
        return "No sales anomalies were detected."
    return f"{high_count} high severity anomalies were detected."


def quality_score_interpretation(quality_score: DataQualityScore | None) -> str:
    if quality_score is None:
        return "No data quality score is available."
    return (
        f"The dataset quality score is {quality_score.score}/100 with "
        f"grade '{quality_score.grade}'."
    )


def pareto_concentration_interpretation(
    grouped_values: dict[str, float],
) -> str:
    if not grouped_values:
        return "No product revenue data is available for Pareto analysis."

    ordered = sorted(
        grouped_values.items(),
        key=lambda item: (-item[1], item[0]),
    )
    total = sum(value for _, value in ordered)
    top_label, top_value = ordered[0]
    top_share = revenue_share(top_value, total)

    cumulative_value = 0.0
    products_to_reach_80 = 0
    for _, value in ordered:
        cumulative_value += value
        products_to_reach_80 += 1
        if revenue_share(cumulative_value, total) >= 80:
            break

    return (
        f"{top_label} contributes {top_share:.2f}% of product revenue; "
        f"{products_to_reach_80} product(s) reach at least 80% cumulative "
        "revenue share."
    )
