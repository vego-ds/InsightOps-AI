from datetime import date
from statistics import mean, median, stdev

from pydantic import BaseModel, Field

from insightops.validation.models import SalesRecord
from insightops.validation.report import ValidationReport


class NumericSummary(BaseModel):
    minimum: float
    maximum: float
    mean: float
    median: float
    standard_deviation: float


class SalesDataProfile(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    date_start: date | None = None
    date_end: date | None = None
    unique_customers: int
    unique_regions: int
    unique_products: int
    unique_sales_reps: int
    duplicate_order_ids: int
    missing_field_counts: dict[str, int] = Field(default_factory=dict)
    revenue_summary: NumericSummary
    quantity_summary: NumericSummary
    discount_summary: NumericSummary
    unit_price_summary: NumericSummary


def build_sales_data_profile(
    validation_report: ValidationReport,
) -> SalesDataProfile:
    records = validation_report.records
    dates = [record.order_date for record in records]

    return SalesDataProfile(
        total_rows=validation_report.total_rows,
        valid_rows=validation_report.valid_rows,
        invalid_rows=validation_report.invalid_rows,
        date_start=min(dates) if dates else None,
        date_end=max(dates) if dates else None,
        unique_customers=_unique_count(records, "customer_id"),
        unique_regions=_unique_count(records, "region"),
        unique_products=_unique_count(records, "product"),
        unique_sales_reps=_unique_count(records, "sales_rep"),
        duplicate_order_ids=_duplicate_order_id_count(records),
        missing_field_counts=_missing_field_counts(validation_report),
        revenue_summary=_numeric_summary([record.revenue for record in records]),
        quantity_summary=_numeric_summary([record.quantity for record in records]),
        discount_summary=_numeric_summary([record.discount for record in records]),
        unit_price_summary=_numeric_summary(
            [record.unit_price for record in records]
        ),
    )


def _unique_count(records: list[SalesRecord], field_name: str) -> int:
    return len({getattr(record, field_name) for record in records})


def _duplicate_order_id_count(records: list[SalesRecord]) -> int:
    seen_order_ids: set[str] = set()
    duplicate_count = 0

    for record in records:
        if record.order_id in seen_order_ids:
            duplicate_count += 1
        else:
            seen_order_ids.add(record.order_id)

    return duplicate_count


def _missing_field_counts(
    validation_report: ValidationReport,
) -> dict[str, int]:
    missing_counts: dict[str, int] = {}

    for error in validation_report.errors:
        message = error.message.casefold()
        if "cannot be empty" in message or "field required" in message:
            missing_counts[error.field] = missing_counts.get(error.field, 0) + 1

    return missing_counts


def _numeric_summary(values: list[float | int]) -> NumericSummary:
    if not values:
        return NumericSummary(
            minimum=0.0,
            maximum=0.0,
            mean=0.0,
            median=0.0,
            standard_deviation=0.0,
        )

    numeric_values = [float(value) for value in values]

    return NumericSummary(
        minimum=round(min(numeric_values), 2),
        maximum=round(max(numeric_values), 2),
        mean=round(mean(numeric_values), 2),
        median=round(median(numeric_values), 2),
        standard_deviation=round(stdev(numeric_values), 2)
        if len(numeric_values) > 1
        else 0.0,
    )
