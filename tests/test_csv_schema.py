import tempfile
from pathlib import Path
import pytest
import csv


from insightops.validation.schema import (
    normalize_header,
    inspect_sales_csv_schema,
    CsvDecodeError,
    CsvSchemaError,
)
from insightops.validation.schema_mapping import map_csv_to_canonical_schema


def test_normalize_header() -> None:
    assert normalize_header("Order ID") == "order_id"
    assert normalize_header("ORDERNUMBER") == "ordernumber"
    assert normalize_header("Quantity Ordered") == "quantity_ordered"
    assert normalize_header("PRICEEACH") == "priceeach"
    assert normalize_header("Order Date") == "order_date"
    assert normalize_header("  ORDER - - NUMBER  ") == "order_number"


def test_canonical_headers_pass() -> None:
    # Create temp file with canonical headers
    with tempfile.NamedTemporaryFile(
        mode="w", newline="", suffix=".csv", delete=False
    ) as f:
        f.write(
            "order_id,order_date,customer_id,region,product,sales_rep,quantity,unit_price,discount,revenue\n"
        )
        f.write("1,2023-01-01,CUST1,North,ProdA,RepA,10,5.0,0.1,45.0\n")
    path = Path(f.name)
    try:
        inspection = inspect_sales_csv_schema(path)
        assert inspection.is_canonical is True
        assert inspection.detected_schema == "canonical"
        assert inspection.is_mappable is False
        assert len(inspection.missing_required_columns) == 0
    finally:
        path.unlink(missing_ok=True)


def test_missing_headers_raise_controlled_error() -> None:
    # Empty file
    with tempfile.NamedTemporaryFile(
        mode="w", newline="", suffix=".csv", delete=False
    ) as f:
        pass
    path = Path(f.name)
    try:
        with pytest.raises(CsvSchemaError, match="CSV file must include a header row."):
            inspect_sales_csv_schema(path)
    finally:
        path.unlink(missing_ok=True)

    # Empty headers
    with tempfile.NamedTemporaryFile(
        mode="w", newline="", suffix=".csv", delete=False
    ) as f:
        f.write(",,,\n")
    path = Path(f.name)
    try:
        with pytest.raises(CsvSchemaError, match="CSV file must include a header row."):
            inspect_sales_csv_schema(path)
    finally:
        path.unlink(missing_ok=True)


def test_missing_required_columns() -> None:
    # Missing order_id and revenue
    with tempfile.NamedTemporaryFile(
        mode="w", newline="", suffix=".csv", delete=False
    ) as f:
        f.write(
            "order_date,customer_id,region,product,sales_rep,quantity,unit_price,discount\n"
        )
        f.write("2023-01-01,CUST1,North,ProdA,RepA,10,5.0,0.1\n")
    path = Path(f.name)
    try:
        inspection = inspect_sales_csv_schema(path)
        assert inspection.is_canonical is False
        assert inspection.detected_schema == "unknown"
        assert "order_id" in inspection.missing_required_columns
        assert "revenue" in inspection.missing_required_columns
    finally:
        path.unlink(missing_ok=True)


def test_non_utf8_raises_controlled_decode_error() -> None:
    # Write using unreadable null bytes to trigger CsvDecodeError
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        f.write(b"order_id,order_date\n\x00\x00\x00\x00\n")
    path = Path(f.name)
    try:
        with pytest.raises(CsvDecodeError):
            inspect_sales_csv_schema(path)
    finally:
        path.unlink(missing_ok=True)


def test_classic_sales_sample_detection_and_mapping() -> None:
    headers = "ORDERNUMBER,ORDERDATE,CUSTOMERNAME,TERRITORY,PRODUCTLINE,CONTACTFIRSTNAME,CONTACTLASTNAME,QUANTITYORDERED,PRICEEACH,SALES\n"
    row = (
        "10107,2/24/2003 0:00,Land of Toys Inc.,APAC,Motorcycles,Yu,Kwai,30,95.7,2871\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", newline="", suffix=".csv", delete=False
    ) as f:
        f.write(headers)
        f.write(row)
    path = Path(f.name)
    out_path = Path(f.name + "_canonical.csv")
    try:
        inspection = inspect_sales_csv_schema(path)
        assert inspection.is_canonical is False
        assert inspection.is_mappable is True
        assert inspection.detected_schema == "classic_sales_sample"
        assert len(inspection.missing_required_columns) == 0

        # Run mapping
        result = map_csv_to_canonical_schema(path, inspection, out_path)
        assert result.detected_schema == "classic_sales_sample"
        assert result.row_count == 1
        assert "discount" in result.defaulted_columns
        assert result.defaulted_columns["discount"] == "0"
        assert any("Discount was defaulted to 0" in w for w in result.warnings)

        # Inspect the generated canonical CSV
        canonical_inspection = inspect_sales_csv_schema(out_path)
        assert canonical_inspection.is_canonical is True

        # Read output file contents
        import csv

        with out_path.open(encoding="utf-8") as out_f:
            reader = csv.DictReader(out_f)
            mapped_rows = list(reader)
            assert len(mapped_rows) == 1
            r = mapped_rows[0]
            assert r["order_id"] == "10107"
            assert r["order_date"] == "2003-02-24"
            assert r["customer_id"] == "Land of Toys Inc."
            assert r["region"] == "APAC"
            assert r["product"] == "Motorcycles"
            assert r["sales_rep"] == "Yu Kwai"
            assert r["quantity"] == "30"
            assert r["unit_price"] == "95.7"
            assert r["discount"] == "0"
            assert r["revenue"] == "2871"
    finally:
        path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)


def test_country_fallback_maps_to_region() -> None:
    # Use COUNTRY instead of TERRITORY
    headers = "ORDERNUMBER,ORDERDATE,CUSTOMERNAME,COUNTRY,PRODUCTLINE,CONTACTFIRSTNAME,CONTACTLASTNAME,QUANTITYORDERED,PRICEEACH,SALES\n"
    row = "10107,2/24/2003 0:00,Land of Toys Inc.,France,Motorcycles,Yu,Kwai,30,95.7,2871\n"
    with tempfile.NamedTemporaryFile(
        mode="w", newline="", suffix=".csv", delete=False
    ) as f:
        f.write(headers)
        f.write(row)
    path = Path(f.name)
    out_path = Path(f.name + "_canonical.csv")
    try:
        inspection = inspect_sales_csv_schema(path)
        assert inspection.is_mappable is True
        assert inspection.detected_schema == "classic_sales_sample"

        result = map_csv_to_canonical_schema(path, inspection, out_path)
        assert any("COUNTRY fallback" in w for w in result.warnings)

        with out_path.open(encoding="utf-8") as out_f:
            reader = csv.DictReader(out_f)
            mapped_rows = list(reader)
            assert mapped_rows[0]["region"] == "France"
    finally:
        path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)
