from insightops.ingestion.csv_loader import load_sales_csv
from insightops.preparation.prepared_dataset import PreparedSalesDataset
from insightops.preparation.transformations import prepare_sales_records
from insightops.validation.models import SalesRecord


def test_prepare_sales_records_creates_derived_fields() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")

    dataset, transformation_log = prepare_sales_records(validation_report.records)

    assert isinstance(dataset, PreparedSalesDataset)
    assert dataset.total_records == 198

    record = dataset.records[0]
    assert record.gross_revenue == 1500.0
    assert record.discount_amount == 150.0
    assert record.net_revenue == 1350.0
    assert record.average_unit_revenue == 1350.0
    assert record.order_year == 2026
    assert record.order_month == 1
    assert record.order_quarter == 1
    assert record.is_discounted is True
    assert record.is_high_value_order is False
    assert record.revenue_reconciliation_difference == 0.0

    assert len(transformation_log.entries) == 2
    assert transformation_log.entries[0].step_name == "clean_sales_records"
    assert transformation_log.entries[1].step_name == "derive_sales_analytics_fields"


def test_prepare_sales_records_cleans_without_mutating_original() -> None:
    record = SalesRecord(
        order_id=" ORD-1 ",
        order_date="2026-01-01",
        customer_id=" CUST-1 ",
        region=" north america ",
        product=" analytics pro ",
        sales_rep=" ava singh ",
        quantity=1,
        unit_price=100.0,
        discount=0.1,
        revenue=90.0,
    )

    dataset, _ = prepare_sales_records([record])

    assert dataset.records[0].region == "North America"
    assert dataset.records[0].product == "Analytics Pro"
    assert dataset.records[0].sales_rep == "Ava Singh"
    assert record.region == "north america"


def test_prepare_sales_records_handles_empty_input() -> None:
    dataset, transformation_log = prepare_sales_records([])

    assert dataset.records == []
    assert dataset.total_records == 0
    assert len(transformation_log.entries) == 2
    assert transformation_log.entries[0].records_affected == 0
