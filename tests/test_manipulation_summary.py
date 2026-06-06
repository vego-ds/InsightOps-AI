from insightops.ingestion.csv_loader import load_sales_csv
from insightops.preparation.manipulations import (
    ManipulationSummary,
    build_manipulation_summary,
)
from insightops.preparation.prepared_dataset import PreparedSalesDataset
from insightops.preparation.transformations import prepare_sales_records


def test_manipulation_summary_ranks_revenue_groups() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    dataset, _ = prepare_sales_records(validation_report.records)

    summary = build_manipulation_summary(dataset)

    assert isinstance(summary, ManipulationSummary)
    assert summary.monthly_revenue[0].label == "2026-01"
    assert summary.monthly_revenue[0].value == 4700.0
    assert summary.ranked_regions[0].label == "North"
    assert summary.ranked_products[0].label == "Analytics Pro"
    assert summary.ranked_sales_reps[0].label == "Ava Singh"


def test_discount_summary_by_product_is_deterministic() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    dataset, _ = prepare_sales_records(validation_report.records)

    summary = build_manipulation_summary(dataset)

    assert summary.discount_summary_by_product[0].product == "Automation Suite"
    assert summary.discount_summary_by_product[0].average_discount == 0.15
    assert summary.discount_summary_by_product[0].discounted_order_count == 1
    assert summary.discount_summary_by_product[0].total_orders == 1


def test_manipulation_summary_handles_empty_dataset() -> None:
    summary = build_manipulation_summary(
        PreparedSalesDataset(records=[], total_records=0)
    )

    assert summary.monthly_revenue == []
    assert summary.ranked_regions == []
    assert summary.ranked_products == []
    assert summary.ranked_sales_reps == []
    assert summary.discount_summary_by_product == []
