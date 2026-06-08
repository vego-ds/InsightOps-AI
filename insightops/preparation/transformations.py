from insightops.lineage.transformation_log import (
    TransformationLog,
    TransformationLogEntry,
    create_transformation_log,
)
from insightops.preparation.cleaner import clean_sales_record
from insightops.preparation.prepared_dataset import (
    PreparedSalesDataset,
    PreparedSalesRecord,
)
from insightops.validation.models import SalesRecord

DERIVED_FIELDS = [
    "gross_revenue",
    "discount_amount",
    "net_revenue",
    "average_unit_revenue",
    "order_year",
    "order_month",
    "order_quarter",
    "is_discounted",
    "is_high_value_order",
    "revenue_reconciliation_difference",
]

TEXT_FIELDS = [
    "order_id",
    "customer_id",
    "region",
    "product",
    "sales_rep",
]


def prepare_sales_records(
    records: list[SalesRecord],
) -> tuple[PreparedSalesDataset, TransformationLog]:
    cleaned_records = [clean_sales_record(record) for record in records]
    prepared_records = [_build_prepared_record(record) for record in cleaned_records]
    transformation_log = create_transformation_log(
        [
            TransformationLogEntry(
                step_name="clean_sales_records",
                description=(
                    "Trimmed text fields and standardized business text for "
                    "analysis-ready records."
                ),
                records_affected=len(records),
                fields_modified=TEXT_FIELDS,
            ),
            TransformationLogEntry(
                step_name="derive_sales_analytics_fields",
                description=(
                    "Created deterministic analytical fields for revenue, "
                    "calendar, discount, high-value, and reconciliation views."
                ),
                records_affected=len(records),
                fields_created=DERIVED_FIELDS,
            ),
        ]
    )

    return (
        PreparedSalesDataset(
            records=prepared_records,
            total_records=len(prepared_records),
        ),
        transformation_log,
    )


def _build_prepared_record(record: SalesRecord) -> PreparedSalesRecord:
    gross_revenue = round(record.quantity * record.unit_price, 2)
    discount_amount = round(gross_revenue * record.discount, 2)
    net_revenue = round(gross_revenue - discount_amount, 2)
    average_unit_revenue = (
        round(record.revenue / record.quantity, 2) if record.quantity > 0 else 0.0
    )

    return PreparedSalesRecord(
        order_id=record.order_id,
        order_date=record.order_date,
        customer_id=record.customer_id,
        region=record.region,
        product=record.product,
        sales_rep=record.sales_rep,
        quantity=record.quantity,
        unit_price=round(record.unit_price, 2),
        discount=record.discount,
        revenue=round(record.revenue, 2),
        gross_revenue=gross_revenue,
        discount_amount=discount_amount,
        net_revenue=net_revenue,
        average_unit_revenue=average_unit_revenue,
        order_year=record.order_date.year,
        order_month=record.order_date.month,
        order_quarter=((record.order_date.month - 1) // 3) + 1,
        is_discounted=record.discount > 0,
        is_high_value_order=record.revenue >= 5000,
        revenue_reconciliation_difference=round(record.revenue - net_revenue, 2),
    )
