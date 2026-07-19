"""Small DataFrame helpers shared by extract and load."""

from __future__ import annotations

import pandas as pd


def prepare_for_insert(df: pd.DataFrame) -> pd.DataFrame:
    """Convert pandas' nullable sentinels into plain `None`.

    pandas' nullable dtypes (`string`, `Int64`, `Float64`) use `pd.NA`, and the
    database driver has no adapter for it — a frame with a single missing value
    fails the whole INSERT with "can't adapt type NAType". Converting to object
    dtype first, then substituting `None`, gives the driver something it can map
    to SQL NULL.

    `np.nan` is handled by the same `notna` mask, so float columns are covered
    too.
    """
    if df.empty:
        return df.astype(object)
    return df.astype(object).where(pd.notna(df), None)
