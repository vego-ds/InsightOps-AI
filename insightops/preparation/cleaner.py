from insightops.validation.models import SalesRecord


def clean_sales_record(record: SalesRecord) -> SalesRecord:
    return SalesRecord(
        order_id=_normalize_identifier(record.order_id),
        order_date=record.order_date,
        customer_id=_normalize_identifier(record.customer_id),
        region=_normalize_business_text(record.region),
        product=_normalize_business_text(record.product),
        sales_rep=_normalize_business_text(record.sales_rep),
        quantity=record.quantity,
        unit_price=record.unit_price,
        discount=record.discount,
        revenue=record.revenue,
    )


def _normalize_identifier(value: str) -> str:
    return value.strip()


def _normalize_business_text(value: str) -> str:
    return " ".join(value.strip().split()).title()
