from pydantic import BaseModel, Field

from insightops.security.prompt_injection import detect_prompt_injection
from insightops.validation.models import SalesRecord


class SecurityScanResult(BaseModel):
    prompt_injection_detected: bool
    flagged_fields: list[str] = Field(default_factory=list)
    human_review_required: bool


def scan_sales_records_for_security(
    records: list[SalesRecord],
) -> SecurityScanResult:
    flagged_fields: list[str] = []

    for row_number, record in enumerate(records, start=1):
        text_fields = {
            "order_id": record.order_id,
            "customer_id": record.customer_id,
            "region": record.region,
            "product": record.product,
            "sales_rep": record.sales_rep,
        }

        for field_name, field_value in text_fields.items():
            if detect_prompt_injection(field_value):
                flagged_fields.append(f"row_{row_number}.{field_name}")

    prompt_injection_detected = bool(flagged_fields)

    return SecurityScanResult(
        prompt_injection_detected=prompt_injection_detected,
        flagged_fields=flagged_fields,
        human_review_required=prompt_injection_detected,
    )
