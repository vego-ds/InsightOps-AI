from pathlib import Path

from insightops.ingestion.csv_loader import load_sales_csv
from insightops.profiling.data_profile import build_sales_data_profile


def test_sales_data_profile_includes_row_counts() -> None:
    profile = _sample_profile()

    assert profile.total_rows == 5
    assert profile.valid_rows == 3
    assert profile.invalid_rows == 2


def test_sales_data_profile_includes_date_range() -> None:
    profile = _sample_profile()

    assert profile.date_start.isoformat() == "2026-01-05"
    assert profile.date_end.isoformat() == "2026-01-07"


def test_sales_data_profile_includes_unique_entity_counts() -> None:
    profile = _sample_profile()

    assert profile.unique_customers == 3
    assert profile.unique_regions == 3
    assert profile.unique_products == 3
    assert profile.unique_sales_reps == 3


def test_sales_data_profile_includes_missing_field_counts() -> None:
    profile = _sample_profile()

    assert profile.missing_field_counts["order_id"] == 1
    assert profile.missing_field_counts["region"] == 1


def test_sales_data_profile_includes_numeric_summaries() -> None:
    profile = _sample_profile()

    assert profile.revenue_summary.minimum == 500.0
    assert profile.revenue_summary.maximum == 2160.0
    assert profile.revenue_summary.mean == 1566.67
    assert profile.revenue_summary.median == 2040.0
    assert profile.quantity_summary.maximum == 3.0
    assert profile.discount_summary.maximum == 0.15
    assert profile.unit_price_summary.minimum == 500.0


def test_sales_data_profile_detects_duplicate_order_ids() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    validation_report.records[1].order_id = validation_report.records[0].order_id

    profile = build_sales_data_profile(validation_report)

    assert profile.duplicate_order_ids == 1


def _sample_profile():
    validation_report = load_sales_csv(str(Path("data/sample/sales_sample.csv")))
    return build_sales_data_profile(validation_report)
