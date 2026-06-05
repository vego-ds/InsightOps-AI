from collections import defaultdict

from pydantic import BaseModel, Field

from insightops.validation.models import SalesRecord


class SalesKPIResult(BaseModel):
    total_revenue: float
    total_orders: int
    total_units_sold: int
    average_order_value: float
    revenue_by_region: dict[str, float] = Field(default_factory=dict)
    revenue_by_product: dict[str, float] = Field(default_factory=dict)
    revenue_by_sales_rep: dict[str, float] = Field(default_factory=dict)


def compute_sales_kpis(records: list[SalesRecord]) -> SalesKPIResult:
    if not records:
        return SalesKPIResult(
            total_revenue=0.0,
            total_orders=0,
            total_units_sold=0,
            average_order_value=0.0,
        )

    total_revenue = sum(record.revenue for record in records)
    total_orders = len(records)
    total_units_sold = sum(record.quantity for record in records)

    revenue_by_region: defaultdict[str, float] = defaultdict(float)
    revenue_by_product: defaultdict[str, float] = defaultdict(float)
    revenue_by_sales_rep: defaultdict[str, float] = defaultdict(float)

    for record in records:
        revenue_by_region[record.region] += record.revenue
        revenue_by_product[record.product] += record.revenue
        revenue_by_sales_rep[record.sales_rep] += record.revenue

    return SalesKPIResult(
        total_revenue=round(total_revenue, 2),
        total_orders=total_orders,
        total_units_sold=total_units_sold,
        average_order_value=round(total_revenue / total_orders, 2),
        revenue_by_region=_round_grouped_revenue(revenue_by_region),
        revenue_by_product=_round_grouped_revenue(revenue_by_product),
        revenue_by_sales_rep=_round_grouped_revenue(revenue_by_sales_rep),
    )


def _round_grouped_revenue(grouped_revenue: dict[str, float]) -> dict[str, float]:
    return {
        group_name: round(revenue, 2)
        for group_name, revenue in grouped_revenue.items()
    }
