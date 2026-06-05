from pathlib import Path

from insightops.ingestion.csv_loader import load_sales_csv
from insightops.validation.models import SalesRecord


def test_sample_sales_csv_loads_with_validation_report() -> None:
    sample_path = Path("data/sample/sales_sample.csv")

    report = load_sales_csv(str(sample_path))

    assert report.total_rows == 5
    assert report.valid_rows == 3
    assert report.invalid_rows == 2
    assert report.errors
    assert report.records
    assert isinstance(report.records[0], SalesRecord)
