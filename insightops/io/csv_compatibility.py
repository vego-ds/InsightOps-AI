import tempfile
from pathlib import Path
from pydantic import BaseModel

from insightops.validation.schema import (
    CsvIncompatibleSchemaError,
    inspect_sales_csv_schema,
)
from insightops.validation.schema_mapping import map_csv_to_canonical_schema


class PreparedCsvForAnalysis(BaseModel):
    analysis_path: Path
    original_headers: list[str]
    normalized_headers: list[str]
    detected_schema: str
    was_mapped: bool
    mapped_columns: dict[str, str]
    missing_required_columns: list[str]
    warnings: list[str]
    detected_encoding: str


def prepare_csv_for_analysis(source_path: Path) -> PreparedCsvForAnalysis:
    inspection = inspect_sales_csv_schema(source_path)

    if inspection.is_canonical:
        return PreparedCsvForAnalysis(
            analysis_path=source_path,
            original_headers=inspection.original_headers,
            normalized_headers=inspection.normalized_headers,
            detected_schema=inspection.detected_schema,
            was_mapped=False,
            mapped_columns={},
            missing_required_columns=[],
            warnings=inspection.warnings,
            detected_encoding=inspection.detected_encoding,
        )

    if inspection.is_mappable:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        temp_path = Path(temp_file.name)
        temp_file.close()

        try:
            result = map_csv_to_canonical_schema(source_path, inspection, temp_path)
            return PreparedCsvForAnalysis(
                analysis_path=temp_path,
                original_headers=inspection.original_headers,
                normalized_headers=inspection.normalized_headers,
                detected_schema=inspection.detected_schema,
                was_mapped=True,
                mapped_columns=result.mapped_columns,
                missing_required_columns=[],
                warnings=result.warnings,
                detected_encoding=inspection.detected_encoding,
            )
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise e

    # Incompatible schema
    missing_str = ", ".join(inspection.missing_required_columns)
    orig_str = ", ".join(inspection.original_headers)
    raise CsvIncompatibleSchemaError(
        f"CSV schema is not compatible with InsightOps-AI. Missing required columns: {missing_str}. Detected columns: {orig_str}"
    )
