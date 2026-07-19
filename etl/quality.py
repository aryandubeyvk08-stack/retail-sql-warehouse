"""Data quality checks, run after every load.

The point is not to prove the data is perfect — it isn't. The point is that
every number in this warehouse is either verified or explicitly flagged, so
nobody builds a decision on a silently broken join.

Checks are graded:
  PASS — as expected
  WARN — a real property of the source data, documented rather than hidden
  FAIL — the pipeline is wrong; the load should not be trusted
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import Engine, text

from .config import REPORT_DIR
from .transform import TransformResult

# SUM(net_revenue) is derived from a rounded unit_price, so it will never match
# SUM(sales) to the cent. 0.01% is tight enough to catch a real bug (a dropped
# join, a discount applied twice) and loose enough to ignore rounding.
REVENUE_TOLERANCE_PCT = 0.01


@dataclass
class Check:
    name: str
    status: str
    detail: str

    @property
    def icon(self) -> str:
        return {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(self.status, "•")


def _scalar(conn, sql: str):
    return conn.execute(text(sql)).scalar()


def run_checks(engine: Engine, result: TransformResult | None = None) -> list[Check]:
    checks: list[Check] = []

    with engine.connect() as conn:
        # -- Volume ---------------------------------------------------------
        raw_rows = _scalar(conn, "SELECT COUNT(*) FROM raw.superstore_orders")
        items = _scalar(conn, "SELECT COUNT(*) FROM core.order_items")
        orders = _scalar(conn, "SELECT COUNT(*) FROM core.orders")
        customers = _scalar(conn, "SELECT COUNT(*) FROM core.customers")
        products = _scalar(conn, "SELECT COUNT(*) FROM core.products")
        locations = _scalar(conn, "SELECT COUNT(*) FROM core.locations")

        # Every source row must end up in exactly one bucket: loaded,
        # quarantined, or dropped as a duplicate. Anything else means the
        # pipeline lost data, which is the one failure nobody notices on their
        # own — so it is asserted exactly, not within a tolerance.
        rejected = len(result.rejects) if result is not None else 0
        deduped = result.duplicates_dropped if result is not None else 0
        accounted = items + rejected + deduped
        checks.append(
            Check(
                "Row count reconciliation",
                "PASS" if result is None or accounted == raw_rows else "FAIL",
                f"raw={raw_rows:,} = loaded {items:,} + quarantined {rejected:,} "
                f"+ deduplicated {deduped:,} → {accounted:,}"
                + ("" if accounted == raw_rows else f"  ({raw_rows - accounted:+,} UNACCOUNTED)"),
            )
        )
        checks.append(
            Check(
                "Dimension cardinality",
                "PASS",
                f"{customers:,} customers · {products:,} products · "
                f"{locations:,} locations · {orders:,} orders · {items:,} line items",
            )
        )

        # -- Revenue reconciliation raw → core ------------------------------
        # Joins each loaded line back to its original raw row and compares the
        # source Sales figure against the DB-generated net_revenue.
        drift = _scalar(
            conn,
            """
            SELECT ABS(SUM(r.sales::numeric) - SUM(oi.net_revenue))
                   / NULLIF(SUM(r.sales::numeric), 0) * 100
            FROM raw.superstore_orders r
            JOIN core.order_items oi ON oi.order_item_id = r.row_id::int
            WHERE r.sales ~ '^-?[0-9]+(\\.[0-9]+)?$'
              AND r.row_id ~ '^[0-9]+$'
            """,
        )
        drift_pct = float(drift or 0)
        checks.append(
            Check(
                "Revenue ties back to source",
                "PASS" if drift_pct <= REVENUE_TOLERANCE_PCT else "FAIL",
                f"SUM(net_revenue) differs from SUM(raw.sales) by {drift_pct:.6f}% "
                f"(tolerance {REVENUE_TOLERANCE_PCT}%)",
            )
        )

        # -- Referential integrity ------------------------------------------
        # Foreign keys already enforce this; running it anyway catches the case
        # where someone loads with constraints dropped "just for speed".
        orphan_items = _scalar(
            conn,
            """
            SELECT COUNT(*) FROM core.order_items oi
            LEFT JOIN core.orders o ON o.order_id = oi.order_id
            WHERE o.order_id IS NULL
            """,
        )
        orphan_orders = _scalar(
            conn,
            """
            SELECT COUNT(*) FROM core.orders o
            LEFT JOIN core.customers c ON c.customer_id = o.customer_id
            WHERE c.customer_id IS NULL
            """,
        )
        checks.append(
            Check(
                "No orphan foreign keys",
                "PASS" if orphan_items == 0 and orphan_orders == 0 else "FAIL",
                f"{orphan_items} line items without an order, "
                f"{orphan_orders} orders without a customer",
            )
        )

        # -- Business rules --------------------------------------------------
        bad_dates = _scalar(
            conn, "SELECT COUNT(*) FROM core.orders WHERE ship_date < order_date"
        )
        checks.append(
            Check(
                "ship_date >= order_date",
                "PASS" if bad_dates == 0 else "FAIL",
                f"{bad_dates} order(s) ship before they are placed",
            )
        )

        bad_qty = _scalar(
            conn, "SELECT COUNT(*) FROM core.order_items WHERE quantity <= 0"
        )
        checks.append(
            Check(
                "quantity > 0 on every line",
                "PASS" if bad_qty == 0 else "FAIL",
                f"{bad_qty} line item(s) with non-positive quantity",
            )
        )

        # -- Known imperfections, surfaced not buried ------------------------
        null_zip = _scalar(
            conn, "SELECT COUNT(*) FROM core.locations WHERE postal_code IS NULL"
        )
        checks.append(
            Check(
                "Postal code completeness",
                "PASS" if null_zip == 0 else "WARN",
                f"{null_zip} location(s) have no postal code in the source "
                "(kept as NULL rather than guessed)",
            )
        )

        loss_pct = _scalar(
            conn,
            """
            SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE profit < 0) / COUNT(*), 2)
            FROM core.order_items
            """,
        )
        checks.append(
            Check(
                "Loss-making line items",
                "WARN" if float(loss_pct or 0) > 0 else "PASS",
                f"{loss_pct}% of line items were sold at a loss — real, and the "
                "subject of query q09",
            )
        )

        span = conn.execute(
            text("SELECT MIN(order_date), MAX(order_date) FROM core.orders")
        ).one()
        checks.append(
            Check(
                "Date coverage",
                "PASS" if span[0] is not None else "FAIL",
                f"orders span {span[0]} → {span[1]}",
            )
        )

        missing_stock = _scalar(
            conn,
            """
            SELECT COUNT(*) FROM core.products p
            LEFT JOIN core.stock s ON s.product_id = p.product_id
            WHERE s.product_id IS NULL
            """,
        )
        checks.append(
            Check(
                "Every product has a stock row",
                "PASS" if missing_stock == 0 else "WARN",
                f"{missing_stock} product(s) missing from core.stock "
                "(q05 would silently omit them)",
            )
        )

    return checks


def write_report(
    checks: list[Check], result: TransformResult | None = None
) -> "object":
    """Write reports/data_quality_report.md and return its path."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / "data_quality_report.md"

    failures = sum(1 for c in checks if c.status == "FAIL")
    warnings = sum(1 for c in checks if c.status == "WARN")
    verdict = "FAILED" if failures else ("PASSED WITH WARNINGS" if warnings else "PASSED")

    lines = [
        "# Data Quality Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}  ",
        f"**Verdict:** {verdict} — {len(checks) - failures - warnings} passed, "
        f"{warnings} warnings, {failures} failures",
        "",
        "## Checks",
        "",
        "| | Check | Result |",
        "|---|---|---|",
    ]
    for check in checks:
        lines.append(f"| {check.icon} | {check.name} | {check.detail} |")

    if result is not None and result.notes:
        lines += ["", "## Transform notes", ""]
        lines += [f"- {note}" for note in result.notes]

    if result is not None and len(result.rejects):
        lines += ["", "## Quarantined rows", "", "| Reason | Rows |", "|---|---:|"]
        for reason, count in result.rejects["reject_reason"].value_counts().items():
            lines.append(f"| {reason} | {count:,} |")
        lines += [
            "",
            "Quarantined rows are excluded from `core` but remain queryable in "
            "`raw.superstore_orders`, so nothing is ever lost.",
        ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
