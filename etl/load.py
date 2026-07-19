"""Load: stage each frame, then MERGE it into core inside one transaction.

Why not `df.to_sql(..., if_exists="append")` straight into core, as the
tutorials do:

  * It is not idempotent. Run it twice and you either duplicate every row or
    crash on the primary key — so re-running a failed nightly load becomes a
    manual cleanup job.
  * It cannot update. Nothing handles a customer changing segment.
  * It has no transaction boundary across tables, so a failure halfway through
    leaves orders loaded and order_items missing, i.e. wrong numbers rather
    than an obvious error.

So: pandas writes to `stg`, SQL does INSERT ... ON CONFLICT DO UPDATE into
`core`, and the whole thing commits or rolls back as one unit.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Connection, Engine, text
from sqlalchemy.types import Date, Integer, Numeric, String

from .config import get_chunk_size
from .frames import prepare_for_insert
from .transform import TransformResult

# Explicit staging types. Letting pandas infer them means dates land as TEXT
# and the INSERT into a DATE column fails with a cast error on some drivers.
_DTYPES: dict[str, dict] = {
    "customers": {
        "customer_id": String(20),
        "customer_name": String(150),
        "segment": String(50),
    },
    "locations": {
        "country": String(100),
        "state": String(100),
        "city": String(100),
        "postal_code": String(20),
        "region": String(50),
    },
    "products": {
        "product_id": String(30),
        "product_name": String(300),
        "category": String(100),
        "sub_category": String(100),
        "list_price": Numeric(12, 2),
    },
    "orders": {
        "order_id": String(30),
        "customer_id": String(20),
        "location_id": Integer(),
        "order_date": Date(),
        "ship_date": Date(),
        "ship_mode": String(50),
    },
    "order_items": {
        "order_item_id": Integer(),
        "order_id": String(30),
        "product_id": String(30),
        "quantity": Integer(),
        "unit_price": Numeric(12, 4),
        "discount": Numeric(5, 4),
        "profit": Numeric(12, 2),
    },
    "stock": {
        "product_id": String(30),
        "current_stock": Integer(),
        "reorder_level": Integer(),
        "last_restock_date": Date(),
    },
}

_LOCATION_KEY = ["country", "state", "city", "postal_code"]
# Sentinel for merging on a nullable key: pandas treats NaN != NaN, so a merge
# on postal_code would drop every row with a missing zip. Postgres handles the
# same problem with UNIQUE NULLS NOT DISTINCT (see 01_schema.sql).
_NA_SENTINEL = "\x00__NULL__"


def _stage(conn: Connection, df: pd.DataFrame, table: str) -> None:
    prepare_for_insert(df).to_sql(
        f"stg_{table}",
        conn,
        schema="stg",
        if_exists="replace",
        index=False,
        chunksize=get_chunk_size(),
        method="multi",
        dtype=_DTYPES[table],
    )


def _merge(
    conn: Connection,
    df: pd.DataFrame,
    *,
    table: str,
    conflict_cols: list[str],
    update_cols: list[str],
) -> int:
    """Stage `df` then upsert it into core.<table>. Returns rows affected."""
    if df.empty:
        return 0
    _stage(conn, df, table)

    cols = ", ".join(f'"{c}"' for c in df.columns)
    if update_cols:
        assignments = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in update_cols)
        action = f"DO UPDATE SET {assignments}"
    else:
        action = "DO NOTHING"

    result = conn.execute(
        text(
            f"INSERT INTO core.{table} ({cols}) "
            f'SELECT {cols} FROM stg."stg_{table}" '
            f"ON CONFLICT ({', '.join(conflict_cols)}) {action}"
        )
    )
    return result.rowcount


def _resolve_location_ids(conn: Connection, orders: pd.DataFrame) -> pd.DataFrame:
    """Swap the four location columns on `orders` for the surrogate key."""
    existing = pd.read_sql(
        text(f"SELECT location_id, {', '.join(_LOCATION_KEY)} FROM core.locations"),
        conn,
    )

    left = orders.copy()
    right = existing.copy()
    for key in _LOCATION_KEY:
        left[key] = left[key].fillna(_NA_SENTINEL)
        right[key] = right[key].fillna(_NA_SENTINEL)

    merged = left.merge(right, on=_LOCATION_KEY, how="left", validate="many_to_one")

    unmatched = int(merged["location_id"].isna().sum())
    if unmatched:
        raise RuntimeError(
            f"{unmatched} order(s) could not be matched to a location. "
            "This means the locations dimension was built from a different "
            "row set than the orders — investigate transform.py before loading."
        )

    merged["location_id"] = merged["location_id"].astype("int64")
    return merged[
        ["order_id", "customer_id", "location_id", "order_date", "ship_date", "ship_mode"]
    ]


def load_all(engine: Engine, result: TransformResult) -> dict[str, int]:
    """Load every frame. One transaction: all of it lands, or none of it does."""
    counts: dict[str, int] = {}

    with engine.begin() as conn:
        # Dimensions first — orders and order_items have FKs pointing at them.
        counts["customers"] = _merge(
            conn, result.customers,
            table="customers",
            conflict_cols=["customer_id"],
            update_cols=["customer_name", "segment"],
        )
        counts["locations"] = _merge(
            conn, result.locations,
            table="locations",
            conflict_cols=_LOCATION_KEY,
            update_cols=["region"],
        )
        counts["products"] = _merge(
            conn, result.products,
            table="products",
            conflict_cols=["product_id"],
            update_cols=["product_name", "category", "sub_category", "list_price"],
        )

        orders = _resolve_location_ids(conn, result.orders)
        counts["orders"] = _merge(
            conn, orders,
            table="orders",
            conflict_cols=["order_id"],
            update_cols=["customer_id", "location_id", "order_date", "ship_date", "ship_mode"],
        )
        counts["order_items"] = _merge(
            conn, result.order_items,
            table="order_items",
            conflict_cols=["order_item_id"],
            # net_revenue is omitted deliberately: it is GENERATED ALWAYS, so
            # Postgres rejects any attempt to write it directly.
            update_cols=["order_id", "product_id", "quantity", "unit_price", "discount", "profit"],
        )
        counts["stock"] = _merge(
            conn, result.stock,
            table="stock",
            conflict_cols=["product_id"],
            update_cols=["current_stock", "reorder_level", "last_restock_date"],
        )

    return counts


def apply_sql_file(engine: Engine, path) -> None:
    """Execute a .sql file as a single script.

    Runs on the raw psycopg connection rather than through SQLAlchemy on
    purpose. psycopg 3 scans a statement for %-placeholders whenever it is
    given a parameter collection — including an empty one — so a literal '%'
    anywhere in the SQL raises:

        only '%s', '%b', '%t' are allowed as placeholders, got '%.'

    Our DDL contains '%' in comments ("ties to <0.01%") and our queries contain
    it in string literals ("'0% (full price)'"). Doubling every one to '%%'
    would fix the driver and break the same files in psql, DBeaver and pgAdmin.
    Passing no parameters at all skips the scan entirely and keeps the .sql
    files portable, which is what they are for.
    """
    sql = path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.connection.driver_connection.execute(sql)


def core_tables_exist(engine: Engine) -> bool:
    with engine.connect() as conn:
        return bool(
            conn.execute(
                text("SELECT to_regclass('core.order_items') IS NOT NULL")
            ).scalar_one()
        )
