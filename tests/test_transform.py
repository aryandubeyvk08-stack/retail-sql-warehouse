"""Tests for the transform layer — no database required.

The transform is where every silent-corruption bug lives (a bad date parse, a
dropped row, a mangled key), so it is the part worth testing hardest.

    pytest -q
"""

from __future__ import annotations

import pandas as pd
import pytest

from etl.extract import RAW_COLUMNS
from etl.transform import _detect_day_first, _to_numeric, transform


def make_raw(**overrides) -> pd.DataFrame:
    """One valid row, with any field overridable."""
    base = {
        "row_id": "1",
        "order_id": "US-2017-1000",
        "order_date": "11/08/2017",
        "ship_date": "11/12/2017",
        "ship_mode": "Standard Class",
        "customer_id": "AB-10015",
        "customer_name": "Aaron Bergman",
        "segment": "Consumer",
        "country": "United States",
        "city": "Seattle",
        "state": "Washington",
        "postal_code": "98103",
        "region": "West",
        "product_id": "TEC-PH-100001",
        "category": "Technology",
        "sub_category": "Phones",
        "product_name": "Phones Item 1",
        "sales": "100.00",
        "quantity": "2",
        "discount": "0.0",
        "profit": "30.00",
    }
    base.update(overrides)
    return pd.DataFrame([[base[c] for c in RAW_COLUMNS]], columns=RAW_COLUMNS).astype("string")


def make_raw_many(rows: list[dict]) -> pd.DataFrame:
    return pd.concat([make_raw(**row) for row in rows], ignore_index=True)


# ---------------------------------------------------------------------------
# Numeric coercion
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("100.00", 100.0),
        ("$1,234.56", 1234.56),
        ("  42 ", 42.0),
        ("(99.50)", -99.50),   # accounting-style negative
        ("", None),
        ("N/A", None),
    ],
)
def test_to_numeric_handles_dirty_values(raw, expected):
    result = _to_numeric(pd.Series([raw], dtype="string")).iloc[0]
    if expected is None:
        assert pd.isna(result)
    else:
        assert result == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Date format detection
# ---------------------------------------------------------------------------

def test_detects_day_first_when_day_exceeds_12():
    series = pd.Series(["13/07/2017", "01/02/2017"], dtype="string")
    assert _detect_day_first(series) is True


def test_detects_month_first_when_month_position_exceeds_12():
    series = pd.Series(["07/13/2017", "01/02/2017"], dtype="string")
    assert _detect_day_first(series) is False


def test_returns_none_when_genuinely_ambiguous():
    series = pd.Series(["01/02/2017", "03/04/2017"], dtype="string")
    assert _detect_day_first(series) is None


# ---------------------------------------------------------------------------
# Quarantine rules — every one of these must be rejected, not silently dropped
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "override, expected_reason",
    [
        ({"quantity": "0"}, "quantity <= 0 (return/void)"),
        ({"quantity": "-3"}, "quantity <= 0 (return/void)"),
        ({"customer_id": ""}, "missing customer_id"),
        ({"order_date": "not a date"}, "unparseable order_date"),
        ({"discount": "1.0"}, "discount outside [0, 1)"),
        ({"sales": "-5"}, "negative or missing sales"),
        ({"order_date": "11/08/2017", "ship_date": "01/01/2016"},
         "ship_date before order_date"),
    ],
)
def test_bad_rows_are_quarantined_with_a_reason(override, expected_reason):
    result = transform(make_raw(**override))
    assert len(result.order_items) == 0
    assert len(result.rejects) == 1
    assert result.rejects["reject_reason"].iloc[0] == expected_reason


def test_valid_row_survives():
    result = transform(make_raw())
    assert len(result.rejects) == 0
    assert len(result.order_items) == 1
    assert len(result.customers) == 1
    assert len(result.products) == 1
    assert len(result.orders) == 1


def test_nothing_is_lost_rows_in_equals_rows_out_plus_rejects():
    """The invariant that makes the pipeline auditable."""
    raw = make_raw_many([
        {"row_id": "1"},
        {"row_id": "2", "quantity": "0"},
        {"row_id": "3", "customer_id": ""},
        {"row_id": "4", "order_id": "US-2017-1001"},
    ])
    result = transform(raw)
    assert len(result.order_items) + len(result.rejects) == len(raw)


# ---------------------------------------------------------------------------
# Derived values
# ---------------------------------------------------------------------------

def test_unit_price_inverts_the_discount_so_revenue_ties_back_to_sales():
    # sales 160 = qty 4 x unit_price 50 x (1 - 0.20)
    result = transform(make_raw(quantity="4", discount="0.2", sales="160.00"))
    item = result.order_items.iloc[0]
    assert item["unit_price"] == pytest.approx(50.0)
    recomputed = item["quantity"] * item["unit_price"] * (1 - item["discount"])
    assert recomputed == pytest.approx(160.0)


def test_exact_duplicate_rows_are_collapsed():
    raw = pd.concat([make_raw(), make_raw()], ignore_index=True)
    result = transform(raw)
    assert len(result.order_items) == 1


def test_whitespace_in_dimension_values_does_not_split_the_dimension():
    raw = make_raw_many([
        {"row_id": "1", "segment": "Consumer"},
        {"row_id": "2", "segment": "Consumer", "order_id": "US-2017-1001"},
    ])
    raw.loc[1, "segment"] = "  Consumer  "
    # extract.read_raw_csv strips, so emulate that contract here.
    raw["segment"] = raw["segment"].str.strip()
    result = transform(raw)
    assert result.customers["segment"].nunique() == 1


def test_leading_zero_postal_codes_survive():
    result = transform(make_raw(postal_code="1234"))
    assert result.locations["postal_code"].iloc[0] == "01234"


def test_blank_postal_code_becomes_null_not_empty_string():
    result = transform(make_raw(postal_code=""))
    assert pd.isna(result.locations["postal_code"].iloc[0])


def test_one_order_with_many_lines_produces_one_order_row():
    raw = make_raw_many([
        {"row_id": "1", "product_id": "TEC-PH-100001"},
        {"row_id": "2", "product_id": "FUR-CH-100002"},
        {"row_id": "3", "product_id": "OFF-PA-100003"},
    ])
    result = transform(raw)
    assert len(result.orders) == 1
    assert len(result.order_items) == 3
    assert len(result.products) == 3


def test_every_product_gets_a_stock_row():
    raw = make_raw_many([
        {"row_id": "1", "product_id": "TEC-PH-100001"},
        {"row_id": "2", "product_id": "FUR-CH-100002"},
    ])
    result = transform(raw)
    assert set(result.stock["product_id"]) == set(result.products["product_id"])
    assert (result.stock["current_stock"] >= 0).all()


def test_stock_is_reproducible_across_runs():
    """A synthetic column that changes every run makes every report untrustworthy."""
    raw = make_raw()
    first = transform(raw).stock
    second = transform(raw).stock
    pd.testing.assert_frame_equal(first, second)
