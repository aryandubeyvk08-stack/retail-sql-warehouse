"""Execute every analytics query and write the results to a markdown report.

    python -m etl.run_queries              # all queries -> reports/query_results.md
    python -m etl.run_queries q02 q05      # only these
    python -m etl.run_queries --rows 50

Having the results committed as markdown means the README can show real
numbers, and a reviewer can see the output without a database of their own.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import QUERY_DIR, REPORT_DIR, ConfigError, get_engine, use_utf8_console

DEFAULT_ROW_LIMIT = 20


def split_statements(sql: str) -> list[str]:
    """Split a .sql file into individual statements.

    Naive on purpose: it splits on semicolons after stripping line comments.
    That is safe for this project because no query contains a semicolon inside
    a string literal — a real parser would be the right call if that changed.
    """
    without_comments = re.sub(r"--[^\n]*", "", sql)
    parts = [p.strip() for p in without_comments.split(";")]
    return [p for p in parts if p]


def first_comment_line(sql: str) -> str:
    """Pull the '-- Qxx — question' headline out of a query file for the report."""
    for line in sql.splitlines():
        stripped = line.strip()
        # Skip the ==== ruler lines: a headline has to contain actual words.
        if stripped.startswith("--") and any(ch.isalpha() for ch in stripped):
            return stripped.lstrip("-= ").strip()
    return ""


def to_markdown_table(df: pd.DataFrame) -> str:
    """Render a result set for a README a human will actually read.

    pandas' default turns 2175300.0 into '2.1753e+06', which is unreadable in a
    revenue column, and renders missing values as the bare string 'nan'.
    """
    return df.to_markdown(
        index=False,
        floatfmt=",.2f",
        intfmt=",",
        missingval="—",
    )


def main(argv: list[str] | None = None) -> int:
    use_utf8_console()
    parser = argparse.ArgumentParser(description="Run the analytics query suite")
    parser.add_argument("only", nargs="*", help="query prefixes, e.g. q02 q05")
    parser.add_argument("--rows", type=int, default=DEFAULT_ROW_LIMIT)
    args = parser.parse_args(argv)

    files = sorted(QUERY_DIR.glob("q*.sql"))
    if args.only:
        files = [f for f in files if any(f.name.startswith(p) for p in args.only)]
    if not files:
        print(f"No query files matched in {QUERY_DIR}", file=sys.stderr)
        return 2

    try:
        engine = get_engine()
    except ConfigError as exc:
        print(f"Configuration error:\n{exc}", file=sys.stderr)
        return 2

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORT_DIR / "query_results.md"

    lines = [
        "# Query Results",
        "",
        f"**Generated:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}  ",
        f"Showing up to {args.rows} rows per result set. "
        "Full SQL lives in [`sql/queries/`](../sql/queries).",
        "",
    ]
    failed = 0

    try:
        with engine.connect() as conn:
            for path in files:
                sql = path.read_text(encoding="utf-8")
                headline = first_comment_line(sql)
                print(f"→ {path.name}")
                lines += ["---", "", f"## `{path.name}`", "", f"*{headline}*", ""]

                for index, statement in enumerate(split_statements(sql), start=1):
                    try:
                        started = time.perf_counter()
                        df = pd.read_sql(text(statement), conn)
                        elapsed_ms = (time.perf_counter() - started) * 1000
                    except SQLAlchemyError as exc:
                        failed += 1
                        # A rolled-back transaction poisons the connection for
                        # every later query, so reset before continuing.
                        conn.rollback()
                        message = str(exc.orig if hasattr(exc, "orig") else exc)
                        print(f"   statement {index} FAILED: {message.splitlines()[0]}")
                        lines += [f"**Statement {index} failed:** `{message}`", ""]
                        continue

                    label = (
                        f"**Statement {index}** — " if index > 1 or len(split_statements(sql)) > 1 else ""
                    )
                    lines += [
                        f"{label}{len(df):,} row(s) in {elapsed_ms:.0f} ms",
                        "",
                        to_markdown_table(df.head(args.rows)),
                        "",
                    ]
                    if len(df) > args.rows:
                        lines += [f"*…{len(df) - args.rows:,} more rows omitted.*", ""]
                    print(f"   statement {index}: {len(df):,} rows, {elapsed_ms:.0f} ms")
    finally:
        engine.dispose()

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
