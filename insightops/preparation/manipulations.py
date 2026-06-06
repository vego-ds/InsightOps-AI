from pydantic import BaseModel, Field

from insightops.preparation.prepared_dataset import (
    PreparedSalesDataset,
    PreparedSalesRecord,
)


class ManipulationDataPoint(BaseModel):
    label: str
    value: float | int


class ProductDiscountSummary(BaseModel):
    product: str
    average_discount: float
    discounted_order_count: int
    total_orders: int


class ManipulationSummary(BaseModel):
    monthly_revenue: list[ManipulationDataPoint] = Field(default_factory=list)
    ranked_regions: list[ManipulationDataPoint] = Field(default_factory=list)
    ranked_products: list[ManipulationDataPoint] = Field(default_factory=list)
    ranked_sales_reps: list[ManipulationDataPoint] = Field(default_factory=list)
    discount_summary_by_product: list[ProductDiscountSummary] = Field(
        default_factory=list
    )


def build_manipulation_summary(
    prepared_dataset: PreparedSalesDataset,
) -> ManipulationSummary:
    records = prepared_dataset.records
    return ManipulationSummary(
        monthly_revenue=_monthly_revenue(records),
        ranked_regions=_rank_grouped_revenue(records, "region"),
        ranked_products=_rank_grouped_revenue(records, "product"),
        ranked_sales_reps=_rank_grouped_revenue(records, "sales_rep"),
        discount_summary_by_product=_discount_summary_by_product(records),
    )


def _monthly_revenue(
    records: list[PreparedSalesRecord],
) -> list[ManipulationDataPoint]:
    grouped: dict[str, float] = {}
    for record in records:
        label = f"{record.order_year:04d}-{record.order_month:02d}"
        grouped[label] = grouped.get(label, 0.0) + record.net_revenue

    return [
        ManipulationDataPoint(label=label, value=round(value, 2))
        for label, value in sorted(grouped.items())
    ]


def _rank_grouped_revenue(
    records: list[PreparedSalesRecord],
    field_name: str,
) -> list[ManipulationDataPoint]:
    grouped: dict[str, float] = {}
    for record in records:
        label = getattr(record, field_name)
        grouped[label] = grouped.get(label, 0.0) + record.net_revenue

    return [
        ManipulationDataPoint(label=label, value=round(value, 2))
        for label, value in sorted(
            grouped.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def _discount_summary_by_product(
    records: list[PreparedSalesRecord],
) -> list[ProductDiscountSummary]:
    grouped: dict[str, list[float]] = {}
    discounted_counts: dict[str, int] = {}

    for record in records:
        grouped.setdefault(record.product, []).append(record.discount)
        if record.is_discounted:
            discounted_counts[record.product] = (
                discounted_counts.get(record.product, 0) + 1
            )

    summaries = [
        ProductDiscountSummary(
            product=product,
            average_discount=round(sum(discounts) / len(discounts), 2),
            discounted_order_count=discounted_counts.get(product, 0),
            total_orders=len(discounts),
        )
        for product, discounts in grouped.items()
    ]

    return sorted(
        summaries,
        key=lambda summary: (-summary.average_discount, summary.product),
    )
