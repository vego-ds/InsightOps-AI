import csv
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

from insightops.validation.schema import CsvSchemaInspection, normalize_header
from insightops.io.csv_reader import open_csv_text


class CsvSchemaMappingResult(BaseModel):
    detected_schema: str
    output_path: Path
    mapped_columns: dict[str, str]
    defaulted_columns: dict[str, str]
    warnings: list[str]
    row_count: int


def _parse_and_format_date(date_str: str) -> str:
    date_str = date_str.strip()
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return date_str


def map_csv_to_canonical_schema(
    source_path: Path,
    inspection: CsvSchemaInspection,
    output_path: Path,
) -> CsvSchemaMappingResult:
    if inspection.detected_schema != "classic_sales_sample":
        raise ValueError(f"Unsupported schema mapping for {inspection.detected_schema}")

    # Map normalized header names back to original header names
    norm_to_orig = {normalize_header(h): h for h in inspection.original_headers}

    ordernumber_col = norm_to_orig["ordernumber"]
    orderdate_col = norm_to_orig["orderdate"]
    customername_col = norm_to_orig["customername"]
    productline_col = norm_to_orig["productline"]
    firstname_col = norm_to_orig["contactfirstname"]
    lastname_col = norm_to_orig["contactlastname"]
    quantityordered_col = norm_to_orig["quantityordered"]
    priceeach_col = norm_to_orig["priceeach"]
    sales_col = norm_to_orig["sales"]

    territory_col = norm_to_orig.get("territory")
    country_col = norm_to_orig.get("country")

    canonical_headers = [
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
    ]

    warnings = list(inspection.warnings)
    used_country_fallback = False

    row_count = 0
    with (
        open_csv_text(source_path) as (src_file, encoding),
        output_path.open("w", newline="", encoding="utf-8") as out_file,
    ):
        reader = csv.DictReader(src_file)
        writer = csv.DictWriter(out_file, fieldnames=canonical_headers)
        writer.writeheader()

        for row in reader:
            row_count += 1

            # region logic
            region_val = ""
            if territory_col:
                region_val = row.get(territory_col, "").strip()
            if not region_val and country_col:
                region_val = row.get(country_col, "").strip()
                used_country_fallback = True

            sales_rep_val = (
                f"{row.get(firstname_col, '').strip()} {row.get(lastname_col, '').strip()}"
            ).strip()

            mapped_row = {
                "order_id": row.get(ordernumber_col, "").strip(),
                "order_date": _parse_and_format_date(row.get(orderdate_col, "")),
                "customer_id": row.get(customername_col, "").strip(),
                "region": region_val,
                "product": row.get(productline_col, "").strip(),
                "sales_rep": sales_rep_val,
                "quantity": row.get(quantityordered_col, "").strip(),
                "unit_price": row.get(priceeach_col, "").strip(),
                "discount": "0",  # default
                "revenue": row.get(sales_col, "").strip(),
            }
            writer.writerow(mapped_row)

    if (used_country_fallback or not territory_col) and not any(
        "uses COUNTRY fallback" in w for w in warnings
    ):
        warnings.append(
            "Region uses COUNTRY fallback because TERRITORY is missing or empty in some rows."
        )

    return CsvSchemaMappingResult(
        detected_schema="classic_sales_sample",
        output_path=output_path,
        mapped_columns=inspection.mapped_columns,
        defaulted_columns={"discount": "0"},
        warnings=warnings,
        row_count=row_count,
    )
