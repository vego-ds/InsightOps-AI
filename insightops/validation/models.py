from datetime import date
from typing import Any

from pydantic import BaseModel, field_validator


class SalesRecord(BaseModel):
    order_id: str
    order_date: date
    customer_id: str
    region: str
    product: str
    sales_rep: str
    quantity: int
    unit_price: float
    discount: float
    revenue: float

    @field_validator(
        "order_id",
        "customer_id",
        "region",
        "product",
        "sales_rep",
        mode="before",
    )
    @classmethod
    def string_fields_cannot_be_empty(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")

        trimmed = value.strip()
        if not trimmed:
            raise ValueError("cannot be empty")

        return trimmed

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than 0")
        return value

    @field_validator("unit_price", "revenue")
    @classmethod
    def money_fields_cannot_be_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("must be greater than or equal to 0")
        return value

    @field_validator("discount")
    @classmethod
    def discount_must_be_between_zero_and_one(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("must be between 0 and 1")
        return value
