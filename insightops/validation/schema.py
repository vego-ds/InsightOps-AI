import csv
import re
from pathlib import Path
from pydantic import BaseModel

from insightops.io.csv_reader import CsvDecodeError, open_csv_text


class CsvSchemaError(Exception):
    pass


class CsvIncompatibleSchemaError(CsvSchemaError):
    pass


REQUIRED_SALES_COLUMNS = {
    "order_id",
    "order_date",
    "customer_id",
    "region",
    "product",
    "sales_rep",
    "quantity",
    "unit_price",
    "discount",
    "revenue",
}


class CsvSchemaInspection(BaseModel):
    original_headers: list[str]
    normalized_headers: list[str]
    detected_schema: str
    is_canonical: bool
    is_mappable: bool
    missing_required_columns: list[str]
    mapped_columns: dict[str, str]
    warnings: list[str]
    detected_encoding: str


def normalize_header(header: str) -> str:
    h = header.strip().lower()
    h = re.sub(r"[\s\-]+", "_", h)
    h = re.sub(r"[^\w]", "", h)
    h = re.sub(r"_+", "_", h)
    return h.strip("_")


def inspect_sales_csv_schema(path: Path) -> CsvSchemaInspection:
    try:
        with open_csv_text(path) as (f, encoding):
            reader = csv.DictReader(f)
            headers = reader.fieldnames
    except CsvDecodeError as e:
        raise e
    except Exception as e:
        raise CsvSchemaError(f"Failed to read CSV headers: {e}") from e

    if not headers or all(not h.strip() for h in headers):
        raise CsvSchemaError("CSV file must include a header row.")

    # Remove any None or empty header entries
    original_headers = [h for h in headers if h and h.strip()]
    normalized_headers = [normalize_header(h) for h in original_headers]

    # Map normalized header back to original header
    norm_to_orig = {normalize_header(h): h for h in original_headers}

    # Check canonical
    missing_required = sorted(list(REQUIRED_SALES_COLUMNS - set(normalized_headers)))
    is_canonical = len(missing_required) == 0

    init_warnings = []
    if encoding in ("cp1252", "iso-8859-1"):
        init_warnings.append(
            "CSV was decoded using Windows-1252. For best compatibility, export future files as CSV UTF-8."
        )

    if is_canonical:
        return CsvSchemaInspection(
            original_headers=original_headers,
            normalized_headers=normalized_headers,
            detected_schema="canonical",
            is_canonical=True,
            is_mappable=False,
            missing_required_columns=[],
            mapped_columns={},
            warnings=init_warnings,
            detected_encoding=encoding,
        )

    # Check if classic_sales_sample
    classic_required = {
        "ordernumber",
        "orderdate",
        "customername",
        "productline",
        "contactfirstname",
        "contactlastname",
        "quantityordered",
        "priceeach",
        "sales",
    }
    has_classic_required = classic_required.issubset(set(normalized_headers))
    has_region = "territory" in normalized_headers or "country" in normalized_headers

    if has_classic_required and has_region:
        mapped_columns = {
            "order_id": norm_to_orig["ordernumber"],
            "order_date": norm_to_orig["orderdate"],
            "customer_id": norm_to_orig["customername"],
            "product": norm_to_orig["productline"],
            "sales_rep": f"{norm_to_orig['contactfirstname']}, {norm_to_orig['contactlastname']}",
            "quantity": norm_to_orig["quantityordered"],
            "unit_price": norm_to_orig["priceeach"],
            "revenue": norm_to_orig["sales"],
            "discount": "0",  # Defaulted
        }

        warnings = list(init_warnings)
        warnings.append(
            "Discount was defaulted to 0 because the external schema does not provide it."
        )

        if "territory" in normalized_headers:
            mapped_columns["region"] = norm_to_orig["territory"]
        else:
            mapped_columns["region"] = norm_to_orig["country"]
            warnings.append(
                "Region uses COUNTRY fallback because TERRITORY is missing."
            )

        return CsvSchemaInspection(
            original_headers=original_headers,
            normalized_headers=normalized_headers,
            detected_schema="classic_sales_sample",
            is_canonical=False,
            is_mappable=True,
            missing_required_columns=[],
            mapped_columns=mapped_columns,
            warnings=warnings,
            detected_encoding=encoding,
        )

    # Incompatible schema
    return CsvSchemaInspection(
        original_headers=original_headers,
        normalized_headers=normalized_headers,
        detected_schema="unknown",
        is_canonical=False,
        is_mappable=False,
        missing_required_columns=missing_required,
        mapped_columns={},
        warnings=init_warnings,
        detected_encoding=encoding,
    )
