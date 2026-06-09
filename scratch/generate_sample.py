import csv
from datetime import date

regions = ["North", "West", "South", "East", "Midwest"]
products = [
    "Analytics Pro",
    "Insights Basic",
    "Automation Suite",
    "Data Flow",
    "Security Hub",
    "Governance Engine",
    "Predictor API",
    "Reporter Tool",
    "Integration Bus",
]
sales_reps = [
    "Ava Singh",
    "Noah Chen",
    "Mia Patel",
    "Liam Jones",
    "Sophia Lee",
    "Oliver Brown",
    "Emma Wilson",
    "Lucas Garcia",
    "Isabella Martinez",
    "Ethan Davis",
]

rows = []
order_id_counter = 1000

# We want 198 valid rows distributed across 12 months in 2026.
# 11 months * 16 rows = 176
# 1 month * 22 rows = 22
# Total valid rows = 198

for month in range(1, 13):
    num_records = 16
    if month == 12:
        num_records = 22

    for i in range(num_records):
        order_id_counter += 1
        order_id = f"ORD-{order_id_counter}"

        order_date = date(2026, month, 1 + (i % 28))
        customer_id = f"CUST-{(100 + i * month) % 200}"
        region = regions[(i + month) % len(regions)]
        product = products[(i * month) % len(products)]
        sales_rep = sales_reps[(i + month) % len(sales_reps)]

        # Product pricing
        if product == "Analytics Pro":
            unit_price = 1500.00
        elif product == "Automation Suite":
            unit_price = 1000.00
        elif product == "Security Hub":
            unit_price = 800.00
        else:
            unit_price = 300.00

        # Quantity model with trend
        quantity = 1 + (i % 3) + (month // 4)

        # Discount model
        discount = 0.0
        if i % 5 == 0:
            discount = 0.10
        elif i % 7 == 0:
            discount = 0.20

        # Specific outliers
        if month == 6 and i == 2:
            discount = 0.50

        if month == 10 and i == 5:
            quantity = 15
            unit_price = 3000.00

        revenue = round(quantity * unit_price * (1 - discount), 2)

        rows.append(
            {
                "order_id": order_id,
                "order_date": order_date.isoformat(),
                "customer_id": customer_id,
                "region": region,
                "product": product,
                "sales_rep": sales_rep,
                "quantity": str(quantity),
                "unit_price": f"{unit_price:.2f}",
                "discount": f"{discount:.2f}",
                "revenue": f"{revenue:.2f}",
            }
        )

# Let's introduce exactly one duplicate order ID pair inside the valid list.
# ORD-1101 will duplicate ORD-1100
rows[101]["order_id"] = "ORD-1100"

# Now let's add exactly 2 invalid rows (brings total to 200 rows).
# 1. Missing order_id (invalid row)
rows.append(
    {
        "order_id": "",
        "order_date": "2026-01-15",
        "customer_id": "CUST-999",
        "region": "North",
        "product": "Analytics Pro",
        "sales_rep": "Ava Singh",
        "quantity": "2",
        "unit_price": "1200.00",
        "discount": "0.10",
        "revenue": "2160.00",
    }
)
# 2. Missing region (invalid row)
rows.append(
    {
        "order_id": "ORD-2002",
        "order_date": "2026-03-15",
        "customer_id": "CUST-998",
        "region": "",
        "product": "Automation Suite",
        "sales_rep": "Mia Patel",
        "quantity": "3",
        "unit_price": "800.00",
        "discount": "0.15",
        "revenue": "2040.00",
    }
)

fieldnames = [
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

with open("data/sample/sales_sample.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(
    "Generated deterministic dataset with 200 rows: 198 valid, 2 invalid, 1 duplicate, 2 missing fields."
)
