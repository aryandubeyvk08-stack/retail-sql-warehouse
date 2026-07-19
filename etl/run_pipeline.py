"""Pipeline entry point.

    python -m etl.run_pipeline              # incremental: upsert into existing core
    python -m etl.run_pipeline --init       # (re)create schema, then load
    python -m etl.run_pipeline --csv other.csv

Exits non-zero if any data quality check FAILs, so this can be dropped into a
scheduler or CI job without further wrapping.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from .config import (
    SQL_DIR,
    ConfigError,
    get_database_url,
    get_engine,
    get_raw_csv_path,
    mask_url,
    use_utf8_console,
)
from .extract import load_raw, read_raw_csv
from .load import apply_sql_file, core_tables_exist, load_all
from .quality import run_checks, write_report
from .transform import transform

SCHEMA_FILES = ["01_schema.sql", "02_indexes.sql", "03_marts.sql"]


def _banner(step: str) -> None:
    print(f"\n[{step}]")


def main(argv: list[str] | None = None) -> int:
    use_utf8_console()
    parser = argparse.ArgumentParser(description="Retail data warehouse ETL")
    parser.add_argument("--csv", type=Path, default=None, help="override RAW_CSV_PATH")
    parser.add_argument(
        "--init",
        action="store_true",
        help="drop and recreate the core schema before loading (destructive)",
    )
    parser.add_argument("--skip-quality", action="store_true")
    args = parser.parse_args(argv)

    started = time.perf_counter()

    try:
        url = get_database_url()
    except ConfigError as exc:
        print(f"Configuration error:\n{exc}", file=sys.stderr)
        return 2

    print(f"Target: {mask_url(url)}")
    engine = get_engine()

    csv_path = args.csv or get_raw_csv_path()

    try:
        # -- Schema ---------------------------------------------------------
        needs_schema = args.init or not core_tables_exist(engine)
        if needs_schema:
            _banner("1/5 schema")
            if args.init:
                print("  --init given: core tables will be dropped and rebuilt")
            for name in SCHEMA_FILES:
                apply_sql_file(engine, SQL_DIR / name)
                print(f"  applied {name}")
        else:
            _banner("1/5 schema")
            print("  core tables already exist; refreshing indexes and views only")
            for name in SCHEMA_FILES[1:]:
                apply_sql_file(engine, SQL_DIR / name)
                print(f"  applied {name}")

        # -- Extract --------------------------------------------------------
        _banner("2/5 extract")
        print(f"  source: {csv_path}")
        raw_df = read_raw_csv(csv_path)
        raw_rows = load_raw(engine, raw_df, csv_path.name)
        print(f"  landed {raw_rows:,} rows in raw.superstore_orders")

        # -- Transform ------------------------------------------------------
        _banner("3/5 transform")
        result = transform(raw_df)
        for note in result.notes:
            print(f"  · {note}")

        # -- Load -----------------------------------------------------------
        _banner("4/5 load")
        counts = load_all(engine, result)
        for table, rows in counts.items():
            print(f"  core.{table:<12} {rows:>7,} rows upserted")

        # -- Quality --------------------------------------------------------
        if args.skip_quality:
            print("\n  (quality checks skipped)")
            failures = 0
        else:
            _banner("5/5 quality")
            checks = run_checks(engine, result)
            for check in checks:
                print(f"  {check.icon} {check.name}: {check.detail}")
            report_path = write_report(checks, result)
            print(f"\n  report written to {report_path}")
            failures = sum(1 for c in checks if c.status == "FAIL")

    except FileNotFoundError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 2
    except SQLAlchemyError as exc:
        print(f"\nDatabase error: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    elapsed = time.perf_counter() - started
    if failures:
        print(f"\nFAILED — {failures} quality check(s) did not pass ({elapsed:.1f}s)")
        return 1
    print(f"\nDone in {elapsed:.1f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
