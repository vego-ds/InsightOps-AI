import csv
from pathlib import Path

from pydantic import ValidationError

from insightops.validation.models import SalesRecord
from insightops.validation.report import ValidationErrorDetail, ValidationReport


def load_sales_csv(path: str) -> ValidationReport:
    records: list[SalesRecord] = []
    errors: list[ValidationErrorDetail] = []
    total_rows = 0
    invalid_row_numbers: set[int] = set()

    with Path(path).open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        for row_number, row in enumerate(reader, start=2):
            total_rows += 1

            try:
                records.append(SalesRecord.model_validate(row))
            except ValidationError as error:
                invalid_row_numbers.add(row_number)
                errors.extend(
                    ValidationErrorDetail(
                        row_number=row_number,
                        field=str(detail["loc"][0]),
                        message=str(detail["msg"]),
                    )
                    for detail in error.errors()
                )

    invalid_rows = len(invalid_row_numbers)

    return ValidationReport(
        total_rows=total_rows,
        valid_rows=len(records),
        invalid_rows=invalid_rows,
        errors=errors,
        records=records,
    )
