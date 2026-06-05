from pydantic import BaseModel, Field

from insightops.validation.models import SalesRecord


class ValidationErrorDetail(BaseModel):
    row_number: int
    field: str
    message: str


class ValidationReport(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[ValidationErrorDetail] = Field(default_factory=list)
    records: list[SalesRecord] = Field(default_factory=list, exclude=True)
