from pydantic import BaseModel, Field

from insightops.preparation.prepared_dataset import PreparedSalesDataset
from insightops.trends.interpretation import (
    direction_interpretation,
    generate_trend_warnings,
)


class TrendDataPoint(BaseModel):
    period: str
    revenue: float
    order_count: int
    units_sold: int
    average_order_value: float
    average_discount: float


class MetricTrendSummary(BaseModel):
    metric: str
    start_value: float
    end_value: float
    absolute_change: float
    percent_change: float | None
    direction: str
    interpretation: str


class TimeSeriesTrendAnalysis(BaseModel):
    period_grain: str
    total_periods: int
    data: list[TrendDataPoint] = Field(default_factory=list)
    revenue_trend: MetricTrendSummary
    order_count_trend: MetricTrendSummary
    average_order_value_trend: MetricTrendSummary
    units_sold_trend: MetricTrendSummary
    average_discount_trend: MetricTrendSummary
    warnings: list[str] = Field(default_factory=list)


def analyze_time_series_trends(
    prepared_dataset: PreparedSalesDataset,
) -> TimeSeriesTrendAnalysis:
    data = _monthly_data(prepared_dataset)
    total_periods = len(data)

    revenue_trend = _metric_trend(
        "revenue",
        [point.revenue for point in data],
        total_periods,
    )
    order_count_trend = _metric_trend(
        "order_count",
        [float(point.order_count) for point in data],
        total_periods,
    )
    average_order_value_trend = _metric_trend(
        "average_order_value",
        [point.average_order_value for point in data],
        total_periods,
    )
    units_sold_trend = _metric_trend(
        "units_sold",
        [float(point.units_sold) for point in data],
        total_periods,
    )
    average_discount_trend = _metric_trend(
        "average_discount",
        [point.average_discount for point in data],
        total_periods,
    )

    return TimeSeriesTrendAnalysis(
        period_grain="month",
        total_periods=total_periods,
        data=data,
        revenue_trend=revenue_trend,
        order_count_trend=order_count_trend,
        average_order_value_trend=average_order_value_trend,
        units_sold_trend=units_sold_trend,
        average_discount_trend=average_discount_trend,
        warnings=generate_trend_warnings(
            total_periods=total_periods,
            revenue_direction=revenue_trend.direction,
            order_count_direction=order_count_trend.direction,
            discount_direction=average_discount_trend.direction,
            discount_percent_change=average_discount_trend.percent_change,
        ),
    )


def _monthly_data(
    prepared_dataset: PreparedSalesDataset,
) -> list[TrendDataPoint]:
    grouped: dict[str, list] = {}
    for record in prepared_dataset.records:
        period = f"{record.order_year:04d}-{record.order_month:02d}"
        grouped.setdefault(period, []).append(record)

    data: list[TrendDataPoint] = []
    for period, records in sorted(grouped.items()):
        revenue = round(sum(record.net_revenue for record in records), 2)
        order_count = len(records)
        units_sold = sum(record.quantity for record in records)
        average_order_value = (
            round(revenue / order_count, 2) if order_count > 0 else 0.0
        )
        average_discount = (
            round(
                sum(record.discount for record in records) / order_count,
                2,
            )
            if order_count > 0
            else 0.0
        )
        data.append(
            TrendDataPoint(
                period=period,
                revenue=revenue,
                order_count=order_count,
                units_sold=units_sold,
                average_order_value=average_order_value,
                average_discount=average_discount,
            )
        )

    return data


def _metric_trend(
    metric: str,
    values: list[float],
    total_periods: int,
) -> MetricTrendSummary:
    start_value = round(values[0], 2) if values else 0.0
    end_value = round(values[-1], 2) if values else 0.0
    absolute_change = round(end_value - start_value, 2)
    percent_change = (
        round((absolute_change / start_value) * 100, 2) if start_value != 0 else None
    )
    direction = _trend_direction(total_periods, absolute_change, percent_change)

    return MetricTrendSummary(
        metric=metric,
        start_value=start_value,
        end_value=end_value,
        absolute_change=absolute_change,
        percent_change=percent_change,
        direction=direction,
        interpretation=direction_interpretation(
            metric,
            direction,
            percent_change,
        ),
    )


def _trend_direction(
    total_periods: int,
    absolute_change: float,
    percent_change: float | None,
) -> str:
    if total_periods < 2:
        return "insufficient_data"

    if percent_change is None:
        if absolute_change == 0:
            return "flat"
        return "increasing" if absolute_change > 0 else "decreasing"

    if abs(percent_change) < 1:
        return "flat"

    return "increasing" if percent_change > 0 else "decreasing"
