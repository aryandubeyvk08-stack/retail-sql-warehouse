"""Extract: read the raw CSV verbatim and land it in raw.superstore_orders.

Nothing is cleaned here. The whole point of the raw layer is that it accepts
the file exactly as it arrived, so that "how dirty was the source?" is a
question we can answer with SQL later instead of a question we destroyed on
the way in.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, text

from .config import get_chunk_size
from .frames import prepare_for_insert

# The public Superstore CSV ships under several header conventions. Map every
# variant onto one canonical snake_case name so downstream code sees one shape.
COLUMN_ALIASES: dict[str, str] = {
    "row id": "row_id",
    "rowid": "row_id",
    "order id": "order_id",
    "order date": "order_date",
    "ship date": "ship_date",
    "ship mode": "ship_mode",
    "customer id": "customer_id",
    "customer name": "customer_name",
    "segment": "segment",
    "country": "country",
    "country/region": "country",
    "city": "city",
    "state": "state",
    "state/province": "state",
    "postal code": "postal_code",
    "postalcode": "postal_code",
    "zip": "postal_code",
    "region": "region",
    "product id": "product_id",
    "category": "category",
    "sub-category": "sub_category",
    "sub category": "sub_category",
    "subcategory": "sub_category",
    "product name": "product_name",
    "sales": "sales",
    "quantity": "quantity",
    "discount": "discount",
    "profit": "profit",
}

RAW_COLUMNS = [
    "row_id", "order_id", "order_date", "ship_date", "ship_mode",
    "customer_id", "customer_name", "segment", "country", "city", "state",
    "postal_code", "region", "product_id", "category", "sub_category",
    "product_name", "sales", "quantity", "discount", "profit",
]

# The Kaggle file is Windows-1252, not UTF-8 — product names contain curly
# quotes and en-dashes that blow up a naive utf-8 read.
_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")


def _canonical(col: str) -> str:
    key = col.strip().lower()
    return COLUMN_ALIASES.get(key, key.replace(" ", "_").replace("-", "_"))


def read_raw_csv(path: Path) -> pd.DataFrame:
    """Read the CSV with every column as a string, trying several encodings."""
    if not path.exists():
        raise FileNotFoundError(
            f"Raw CSV not found at {path}\n"
            "  Download the Superstore dataset and save it there "
            "(see README, 'Getting the data')."
        )

    last_error: Exception | None = None
    for encoding in _ENCODINGS:
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding=encoding)
            print(f"  read {len(df):,} rows using encoding={encoding}")
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:  # pragma: no cover - only if the file is in some exotic encoding
        raise RuntimeError(f"Could not decode {path}: {last_error}")

    df.columns = [_canonical(c) for c in df.columns]

    missing = [c for c in RAW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing expected column(s): {missing}\n"
            f"  Found: {sorted(df.columns)}\n"
            "  This project targets the Kaggle 'Sample - Superstore' schema."
        )

    df = df[RAW_COLUMNS].copy()
    # Trailing/leading whitespace in the source is real and would otherwise
    # create two 'Corporate ' vs 'Corporate' segments.
    for col in df.columns:
        df[col] = df[col].astype("string").str.strip()
    return df


def load_raw(engine: Engine, df: pd.DataFrame, source_file: str) -> int:
    """Truncate and reload the raw landing table. Returns rows written."""
    staged = df.copy()
    staged["_source_file"] = source_file

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE raw.superstore_orders"))
        prepare_for_insert(staged).to_sql(
            "superstore_orders",
            conn,
            schema="raw",
            if_exists="append",
            index=False,
            chunksize=get_chunk_size(),
            method="multi",
        )
        count = conn.execute(
            text("SELECT COUNT(*) FROM raw.superstore_orders")
        ).scalar_one()
    return int(count)
