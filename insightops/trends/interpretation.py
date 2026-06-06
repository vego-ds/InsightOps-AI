def format_percent_change(percent_change: float | None) -> str:
    if percent_change is None:
        return "not available"
    return f"{percent_change:.2f}%"


def direction_interpretation(
    metric: str,
    direction: str,
    percent_change: float | None,
) -> str:
    if direction == "insufficient_data":
        return f"{metric} needs at least two monthly periods for trend analysis."

    change_text = format_percent_change(percent_change)
    if direction == "flat":
        return f"{metric} is flat across the observed monthly period range."

    return f"{metric} is {direction} by {change_text} across the observed monthly period range."


def generate_trend_warnings(
    *,
    total_periods: int,
    revenue_direction: str,
    order_count_direction: str,
    discount_direction: str,
    discount_percent_change: float | None,
) -> list[str]:
    warnings: list[str] = []

    if total_periods < 2:
        warnings.append("At least two monthly periods are needed for trend analysis.")

    if revenue_direction == "decreasing":
        warnings.append("Revenue is decreasing across the observed period range.")

    if order_count_direction == "decreasing":
        warnings.append("Order volume is decreasing across the observed period range.")

    if (
        discount_direction == "increasing"
        and discount_percent_change is not None
        and discount_percent_change >= 10
    ):
        warnings.append("Average discount increased materially over time.")

    return warnings
