from datetime import date

from pydantic import BaseModel, Field


class PreparedSalesRecord(BaseModel):
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
    gross_revenue: float
    discount_amount: float
    net_revenue: float
    average_unit_revenue: float
    order_year: int
    order_month: int
    order_quarter: int
    is_discounted: bool
    is_high_value_order: bool
    revenue_reconciliation_difference: float


class PreparedSalesDataset(BaseModel):
    records: list[PreparedSalesRecord] = Field(default_factory=list)
    total_records: int
