"""Generate a small, deliberately dirty Superstore-shaped CSV.

Two uses:
  1. Anyone can run the full pipeline without a Kaggle account.
  2. The transform tests need input where every failure mode is guaranteed
     present — real data happens to be clean in places you need dirty.

    python -m tests.generate_sample_csv --rows 2000 --out data/raw/sample_superstore.csv

This file is SYNTHETIC. The README says so, and so does this docstring, because
a generated CSV quietly passed off as the Kaggle dataset is the sort of thing
that unravels badly in an interview.
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

HEADER = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID",
    "Customer Name", "Segment", "Country", "City", "State", "Postal Code",
    "Region", "Product ID", "Category", "Sub-Category", "Product Name",
    "Sales", "Quantity", "Discount", "Profit",
]

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]
CITIES = [
    ("New York City", "New York", "10024", "East"),
    ("Los Angeles", "California", "90036", "West"),
    ("Seattle", "Washington", "98103", "West"),
    ("Chicago", "Illinois", "60653", "Central"),
    ("Houston", "Texas", "77095", "Central"),
    ("Philadelphia", "Pennsylvania", "19140", "East"),
    ("Burlington", "Vermont", "", "East"),          # genuinely blank zip
    ("Atlanta", "Georgia", "30318", "South"),
    ("Miami", "Florida", "33180", "South"),
]
CATEGORIES = {
    "Furniture": ["Bookcases", "Chairs", "Tables", "Furnishings"],
    "Office Supplies": ["Binders", "Paper", "Storage", "Art", "Appliances"],
    "Technology": ["Phones", "Machines", "Accessories", "Copiers"],
}
FIRST = ["Aaron", "Claire", "Darrin", "Eugene", "Gene", "Harold", "Karen",
         "Laura", "Nathan", "Patrick", "Sandra", "Tracy"]
LAST = ["Bergman", "Gute", "Hoffman", "Jones", "Kelly", "Moore", "Nguyen",
        "Patel", "Reed", "Smith", "Walker", "Zhu"]


def build_rows(n_rows: int, seed: int) -> list[list[str]]:
    rng = random.Random(seed)

    customers = []
    for i in range(max(8, n_rows // 25)):
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        initials = "".join(part[0] for part in name.split())
        customers.append((f"{initials}-{10000 + i * 7}", name, rng.choice(SEGMENTS)))

    products = []
    for category, subs in CATEGORIES.items():
        for sub in subs:
            for i in range(4):
                prefix = category[:3].upper()
                pid = f"{prefix}-{sub[:2].upper()}-{100000 + len(products)}"
                products.append(
                    (pid, f"{sub} Item {i + 1}", category, sub, round(rng.uniform(8, 900), 2))
                )

    start = date(2015, 1, 3)
    rows: list[list[str]] = []
    row_id = 1
    order_seq = 1000

    while len(rows) < n_rows:
        cust_id, cust_name, segment = rng.choice(customers)
        city, state, postal, region = rng.choice(CITIES)
        order_date = start + timedelta(days=rng.randint(0, 1090))
        ship_date = order_date + timedelta(days=rng.randint(0, 7))
        order_id = f"US-{order_date.year}-{order_seq}"
        order_seq += 1
        ship_mode = rng.choice(SHIP_MODES)

        for _ in range(rng.randint(1, 4)):
            if len(rows) >= n_rows:
                break
            pid, pname, category, sub, list_price = rng.choice(products)
            qty = rng.randint(1, 9)
            discount = rng.choice([0, 0, 0, 0.1, 0.2, 0.2, 0.3, 0.4, 0.5, 0.7])
            sales = round(qty * list_price * (1 - discount), 4)
            # Margin collapses as discount rises — the pattern q09 is designed
            # to find. Deliberate, so the query has something true to detect.
            margin = 0.32 - discount * 1.15 + rng.uniform(-0.05, 0.05)
            profit = round(sales * margin, 4)

            rows.append([
                str(row_id), order_id,
                order_date.strftime("%m/%d/%Y"), ship_date.strftime("%m/%d/%Y"),
                ship_mode, cust_id, cust_name, segment,
                "United States", city, state, postal, region,
                pid, category, sub, pname,
                f"{sales}", str(qty), str(discount), f"{profit}",
            ])
            row_id += 1

    _inject_dirt(rows, rng)
    return rows


def _inject_dirt(rows: list[list[str]], rng: random.Random) -> None:
    """Add the specific defects the pipeline claims to handle.

    Each one maps to a branch in etl/transform.py. If a defect is not
    represented here, the code path that handles it is untested.
    """
    n = len(rows)
    if n < 20:
        return

    # Exact duplicate rows (dedup path)
    for _ in range(max(1, n // 100)):
        rows.append(list(rows[rng.randrange(n)]))

    # Whitespace and casing noise (strip path)
    for _ in range(max(1, n // 50)):
        row = rows[rng.randrange(n)]
        row[7] = f"  {row[7]}  "          # Segment
        row[6] = row[6].upper()           # Customer Name

    # Zero / negative quantity — real "return" rows, must be quarantined
    for _ in range(max(1, n // 150)):
        rows[rng.randrange(n)][18] = rng.choice(["0", "-2"])

    # Currency formatting in a numeric column (numeric coercion path)
    for _ in range(max(1, n // 80)):
        row = rows[rng.randrange(n)]
        row[17] = f"${float(row[17]):,.2f}"

    # Unparseable date (date quarantine path)
    for _ in range(max(1, n // 200)):
        rows[rng.randrange(n)][2] = "not a date"

    # Ship date before order date (business-rule quarantine path)
    for _ in range(max(1, n // 200)):
        row = rows[rng.randrange(n)]
        row[3] = "01/01/2014"

    # Missing customer id (required-key quarantine path)
    for _ in range(max(1, n // 250)):
        rows[rng.randrange(n)][5] = ""

    rng.shuffle(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--out", type=Path, default=Path("data/raw/sample_superstore.csv")
    )
    args = parser.parse_args(argv)

    rows = build_rows(args.rows, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print(f"Wrote {len(rows):,} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
