def build_dataset_profile_code() -> str:
    return """
import csv
import sys
from pathlib import Path

dataset_path = Path(sys.argv[1]).resolve()
if not dataset_path.exists():
    raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

with dataset_path.open("r", encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle)
    rows = list(reader)
    columns = reader.fieldnames or []

print(f"Dataset rows: {len(rows)}")
print(f"Dataset columns: {len(columns)}")
if columns:
    print("Columns: " + ", ".join(columns))
else:
    print("Columns: none")
""".strip()
