"""Transform: turn one flat, dirty CSV into six clean, normalized frames.

Design rule followed throughout: never silently drop a row. Anything that
cannot be loaded is moved to `rejects` with a reason string, counted, and
reported. A pipeline that quietly discards 3% of revenue is worse than one
that fails, because nobody notices.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Reproducibility: the inventory snapshot is synthetic, so it must at least be
# the *same* synthetic data on every run or the days-of-stock report changes
# every time you refresh and nobody can trust it.
STOCK_SEED = 42
RECENT_WINDOW_DAYS = 28


@dataclass
class TransformResult:
    customers: pd.DataFrame
    locations: pd.DataFrame
    products: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame
    stock: pd.DataFrame
    rejects: pd.DataFrame
    notes: list[str] = field(default_factory=list)
    source_rows: int = 0        # rows read from the CSV
    duplicates_dropped: int = 0 # exact duplicates + duplicate primary keys


# ---------------------------------------------------------------------------
# Type coercion helpers
# ---------------------------------------------------------------------------

_DATE_FORMATS_MONTH_FIRST = ["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"]
_DATE_FORMATS_DAY_FIRST = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]


def _detect_day_first(series: pd.Series) -> bool | None:
    """Decide d/m/Y vs m/d/Y from the data itself.

    A value like 13/07/2017 can only be day-first, because there is no month 13.
    If neither component ever exceeds 12 the file is genuinely ambiguous and we
    return None — the caller then defaults to month-first (US convention, which
    is what the Superstore export uses) and says so in the report rather than
    pretending it knew.
    """
    parts = series.dropna().astype(str).str.extract(r"^\s*(\d{1,2})[/-](\d{1,2})[/-]")
    if parts.empty or parts.isna().all().all():
        return None
    first = pd.to_numeric(parts[0], errors="coerce")
    second = pd.to_numeric(parts[1], errors="coerce")
    first_over_12 = bool((first > 12).any())
    second_over_12 = bool((second > 12).any())
    if first_over_12 and not second_over_12:
        return True
    if second_over_12 and not first_over_12:
        return False
    return None


def _parse_dates(series: pd.Series, day_first: bool | None) -> pd.Series:
    """Try each plausible format, keep whichever parses the most values."""
    formats = _DATE_FORMATS_DAY_FIRST if day_first else _DATE_FORMATS_MONTH_FIRST
    best = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for fmt in formats:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        # Fill only the gaps — this is what makes a file with *mixed* formats
        # (a genuinely common export bug) load fully instead of half-failing.
        best = best.fillna(parsed)
    if best.isna().any():
        fallback = pd.to_datetime(
            series, errors="coerce", dayfirst=bool(day_first), format="mixed"
        )
        best = best.fillna(fallback)
    return best


def _to_numeric(series: pd.Series) -> pd.Series:
    """Strip currency symbols, thousands separators and stray spaces."""
    cleaned = (
        series.astype("string")
        .str.replace(r"[$₹,\s]", "", regex=True)
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)  # (123.45) => -123.45
        .replace({"": None, "-": None, "NA": None, "N/A": None, "null": None})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _mode_or_first(series: pd.Series):
    """Pick the most common non-null value; ties resolve to the first seen."""
    modes = series.dropna().mode()
    if len(modes):
        return modes.iloc[0]
    return None


# ---------------------------------------------------------------------------
# Main transform
# ---------------------------------------------------------------------------


def transform(raw: pd.DataFrame) -> TransformResult:
    notes: list[str] = []
    df = raw.copy()
    original_rows = len(df)

    # -- 1. Exact duplicate rows -------------------------------------------
    duplicates_dropped = 0
    before = len(df)
    df = df.drop_duplicates()
    if before != len(df):
        duplicates_dropped += before - len(df)
        notes.append(f"Dropped {before - len(df):,} exact duplicate rows.")

    # -- 2. Type coercion ---------------------------------------------------
    day_first = _detect_day_first(df["order_date"])
    if day_first is None:
        notes.append(
            "Date format is ambiguous (no day > 12 anywhere); assuming "
            "MM/DD/YYYY, the US convention the Superstore export uses."
        )
    else:
        notes.append(f"Detected date format: {'DD/MM/YYYY' if day_first else 'MM/DD/YYYY'}.")

    df["order_date"] = _parse_dates(df["order_date"], day_first)
    df["ship_date"] = _parse_dates(df["ship_date"], day_first)

    for col in ("sales", "quantity", "discount", "profit", "row_id"):
        df[col] = _to_numeric(df[col])

    # Postal code stays TEXT on purpose: it is an identifier, not a number.
    # Casting it to int silently eats the leading zero off every New England
    # zip code (01234 -> 1234), which then never joins to anything.
    df["postal_code"] = (
        df["postal_code"].astype("string").replace({"": None}).str.zfill(5)
    )
    blank_zip = int(df["postal_code"].isna().sum())
    if blank_zip:
        notes.append(f"{blank_zip:,} rows have no postal code (kept as NULL).")

    # -- 3. Quarantine unloadable rows -------------------------------------
    reasons = pd.Series("", index=df.index, dtype="object")

    def flag(mask: pd.Series, reason: str) -> None:
        hit = mask.fillna(False)
        reasons[hit & (reasons == "")] = reason

    flag(df["order_id"].isna() | (df["order_id"] == ""), "missing order_id")
    flag(df["customer_id"].isna() | (df["customer_id"] == ""), "missing customer_id")
    flag(df["product_id"].isna() | (df["product_id"] == ""), "missing product_id")
    flag(df["row_id"].isna(), "missing/invalid row_id")
    flag(df["order_date"].isna(), "unparseable order_date")
    flag(df["quantity"].isna() | (df["quantity"] <= 0), "quantity <= 0 (return/void)")
    flag(df["sales"].isna() | (df["sales"] < 0), "negative or missing sales")
    flag(
        df["discount"].isna() | (df["discount"] < 0) | (df["discount"] >= 1),
        "discount outside [0, 1)",
    )
    flag(
        df["ship_date"].notna() & (df["ship_date"] < df["order_date"]),
        "ship_date before order_date",
    )

    rejects = df[reasons != ""].copy()
    rejects["reject_reason"] = reasons[reasons != ""]
    df = df[reasons == ""].copy()

    if len(rejects):
        breakdown = rejects["reject_reason"].value_counts().to_dict()
        notes.append(
            f"Quarantined {len(rejects):,} of {original_rows:,} rows "
            f"({100 * len(rejects) / original_rows:.2f}%): {breakdown}"
        )
    else:
        notes.append("No rows quarantined — every source row passed validation.")

    # -- 4. Derive unit price ----------------------------------------------
    # Superstore gives `Sales` = the net amount actually billed, i.e. already
    # discount-adjusted. To store a price on the line item we invert that:
    #   sales = qty * unit_price * (1 - discount)
    df["unit_price"] = df["sales"] / (df["quantity"] * (1 - df["discount"]))
    df["unit_price"] = df["unit_price"].round(4)
    df["row_id"] = df["row_id"].astype("int64")
    df["quantity"] = df["quantity"].astype("int64")

    # -- 5. Dimensions ------------------------------------------------------
    customers = (
        df.groupby("customer_id", as_index=False)
        .agg(customer_name=("customer_name", _mode_or_first),
             segment=("segment", _mode_or_first))
    )
    conflicting = (
        df.groupby("customer_id")["customer_name"].nunique().pipe(lambda s: int((s > 1).sum()))
    )
    if conflicting:
        notes.append(
            f"{conflicting} customer_id(s) map to more than one name; kept the "
            "most frequent spelling."
        )

    locations = (
        df[["country", "state", "city", "postal_code", "region"]]
        .drop_duplicates(subset=["country", "state", "city", "postal_code"])
        .reset_index(drop=True)
    )

    products = (
        df.groupby("product_id", as_index=False)
        .agg(
            product_name=("product_name", _mode_or_first),
            category=("category", _mode_or_first),
            sub_category=("sub_category", _mode_or_first),
            list_price=("unit_price", "median"),
        )
    )
    products["list_price"] = products["list_price"].round(2)
    dupe_names = df.groupby("product_id")["product_name"].nunique()
    if int((dupe_names > 1).sum()):
        notes.append(
            f"{int((dupe_names > 1).sum())} product_id(s) appear under multiple "
            "names in the source (a known Superstore defect); kept the most "
            "frequent name."
        )

    # -- 6. Facts -----------------------------------------------------------
    # An order_id can appear on many lines; every line must agree on the order
    # header. Where the source disagrees, majority wins — and we say so.
    orders = (
        df.groupby("order_id", as_index=False)
        .agg(
            customer_id=("customer_id", _mode_or_first),
            order_date=("order_date", "min"),
            ship_date=("ship_date", "max"),
            ship_mode=("ship_mode", _mode_or_first),
            country=("country", _mode_or_first),
            state=("state", _mode_or_first),
            city=("city", _mode_or_first),
            postal_code=("postal_code", _mode_or_first),
        )
    )
    orders["order_date"] = orders["order_date"].dt.date
    orders["ship_date"] = orders["ship_date"].dt.date

    order_items = df[
        ["row_id", "order_id", "product_id", "quantity", "unit_price", "discount", "profit"]
    ].rename(columns={"row_id": "order_item_id"}).copy()
    order_items["discount"] = order_items["discount"].round(4)
    order_items["profit"] = order_items["profit"].round(2)

    before = len(order_items)
    order_items = order_items.drop_duplicates(subset=["order_item_id"], keep="first")
    if before != len(order_items):
        duplicates_dropped += before - len(order_items)
        notes.append(
            f"{before - len(order_items):,} duplicate row_id(s) collapsed — "
            "row_id is the primary key of order_items."
        )

    stock = _synthesize_stock(df, products, notes)

    return TransformResult(
        customers=customers,
        locations=locations,
        products=products,
        orders=orders,
        order_items=order_items,
        stock=stock,
        rejects=rejects,
        notes=notes,
        source_rows=original_rows,
        duplicates_dropped=duplicates_dropped,
    )


def _synthesize_stock(
    df: pd.DataFrame, products: pd.DataFrame, notes: list[str]
) -> pd.DataFrame:
    """Invent a plausible current-inventory snapshot.

    Superstore has no stock column, and Q05 (days-of-stock-remaining) needs one.
    Rather than fake it uniformly, cover is scaled to each SKU's own recent
    sales rate so the resulting URGENT/MONITOR/OK split is actually interesting
    instead of every product landing in the same bucket.

    This is clearly labelled as simulated in the README, the table comment and
    here — a synthetic column presented as real is the fastest way to lose an
    interviewer's trust.
    """
    columns = ["product_id", "current_stock", "reorder_level", "last_restock_date"]
    if products.empty or df.empty:
        # Every source row was quarantined. Return the right *shape* rather
        # than crashing — the load step must still be able to run and report
        # zero rows, which is a meaningful result, not an exception.
        notes.append("No valid rows survived validation; stock snapshot is empty.")
        return pd.DataFrame(columns=columns)

    rng = np.random.default_rng(STOCK_SEED)

    as_of = df["order_date"].max()
    window_start = as_of - pd.Timedelta(days=RECENT_WINDOW_DAYS)
    recent = df[df["order_date"] > window_start]

    daily = (
        recent.groupby("product_id")["quantity"].sum() / RECENT_WINDOW_DAYS
    ).rename("avg_daily_sales")

    stock = products[["product_id"]].merge(
        daily, left_on="product_id", right_index=True, how="left"
    )
    stock["avg_daily_sales"] = stock["avg_daily_sales"].fillna(0.0)

    # Days of cover drawn from 1..30; multiplied by the SKU's own sales rate.
    cover_days = rng.uniform(1.0, 30.0, size=len(stock))
    stock["current_stock"] = np.where(
        stock["avg_daily_sales"] > 0,
        np.ceil(stock["avg_daily_sales"] * cover_days),
        rng.integers(0, 40, size=len(stock)),
    ).astype("int64")
    stock["reorder_level"] = np.ceil(stock["avg_daily_sales"] * 7).astype("int64")
    stock["last_restock_date"] = [
        (as_of - pd.Timedelta(days=int(d))).date()
        for d in rng.integers(0, 25, size=len(stock))
    ]

    notes.append(
        f"Synthesised inventory for {len(stock):,} products "
        f"(seed={STOCK_SEED}, as-of {as_of.date()}). NOT source data."
    )
    return stock[columns]
