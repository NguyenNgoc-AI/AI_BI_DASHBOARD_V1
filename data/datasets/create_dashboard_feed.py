"""
create_dashboard_feed.py

Helper script to extract and adapt the 50,000-row, 38-column gold synthetic dataset
into an ingestion-ready format (sample_dashboard_feed.csv) for the AI BI Dashboard Frontend.

Mapping:
- date     <- order_purchase_timestamp (formatted as YYYY-MM-DD)
- order_id <- order_id
- product  <- sub_category
- quantity <- quantity
- revenue  <- net_sales
- cost     <- cogs
"""

import csv
from pathlib import Path


def extract_dashboard_feed(
    input_file: Path | str,
    output_file: Path | str,
    limit: int | None = None
) -> int:
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found at {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows_written = 0
    with open(input_path, mode="r", encoding="utf-8-sig", newline="") as infile, \
         open(output_path, mode="w", encoding="utf-8", newline="") as outfile:

        reader = csv.DictReader(infile)
        fieldnames = ["date", "order_id", "product", "quantity", "revenue", "cost"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            raw_timestamp = row.get("order_purchase_timestamp", "").strip()
            date_part = raw_timestamp.split(" ")[0] if raw_timestamp else ""

            writer.writerow({
                "date": date_part,
                "order_id": row.get("order_id", "").strip(),
                "product": row.get("sub_category", row.get("product_id", "")).strip(),
                "quantity": row.get("quantity", "1").strip(),
                "revenue": row.get("net_sales", "0").strip(),
                "cost": row.get("cogs", "0").strip(),
            })
            rows_written += 1
            if limit and rows_written >= limit:
                break

    return rows_written


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    source = base_dir / "synthetic_ecommerce.csv"
    target = base_dir / "sample_dashboard_feed.csv"

    print(f"Extracting dashboard feed from {source}...")
    total = extract_dashboard_feed(source, target)
    print(f"Successfully generated {target} with {total:,} rows.")

