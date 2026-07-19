"""Streamlit dashboard over the warehouse.

Every chart reads a `mart` view — the same views the SQL queries use — so the
dashboard and the query suite can never tell different stories. Nothing here
re-derives revenue.

    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl.config import ConfigError, get_engine  # noqa: E402

st.set_page_config(page_title="Retail Warehouse", page_icon="🏬", layout="wide")


@st.cache_resource
def engine():
    return get_engine()


@st.cache_data(ttl=600)
def query(sql: str) -> pd.DataFrame:
    # text() is not optional here. Handed a plain string, pandas routes through
    # exec_driver_sql, and psycopg 3 then reads the '%' in literals like
    # '0% (full price)' as a parameter placeholder and refuses the statement.
    # text() lets SQLAlchemy escape it for the dialect.
    return pd.read_sql(text(sql), engine())


st.title("🏬 Retail Sales Data Warehouse")
st.caption("Cloud PostgreSQL · every figure sourced from the `mart` views")

try:
    monthly = query("SELECT * FROM mart.v_monthly_revenue ORDER BY order_month")
except ConfigError as exc:
    st.error(f"Configuration problem:\n\n{exc}")
    st.stop()
except Exception as exc:  # noqa: BLE001 - surface any connection error to the user
    st.error(
        f"Could not reach the database.\n\n`{exc}`\n\n"
        "Check `DATABASE_URL` in `.env`, and that `python -m etl.run_pipeline --init` "
        "has been run at least once."
    )
    st.stop()

if monthly.empty:
    st.warning("The warehouse is empty. Run `python -m etl.run_pipeline --init` first.")
    st.stop()

# --- KPI row ---------------------------------------------------------------
totals = query(
    """
    SELECT SUM(net_revenue) AS revenue,
           SUM(profit)      AS profit,
           COUNT(DISTINCT order_id)    AS orders,
           COUNT(DISTINCT customer_id) AS customers
    FROM mart.v_line_items
    """
).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${totals['revenue']:,.0f}")
c2.metric(
    "Profit",
    f"${totals['profit']:,.0f}",
    f"{100 * totals['profit'] / totals['revenue']:.1f}% margin",
)
# :,.0f rather than :,   — .iloc[0] on a mixed-dtype row upcasts the integer
# counts to float, so a plain :, renders "5,009.0".
c3.metric("Orders", f"{totals['orders']:,.0f}")
c4.metric("Customers", f"{totals['customers']:,.0f}")

st.divider()

# --- Trend + category ------------------------------------------------------
left, right = st.columns([3, 2])

with left:
    st.subheader("Revenue trend")
    monthly["3-month average"] = monthly["revenue"].rolling(3).mean()
    fig = px.line(
        monthly,
        x="order_month",
        y=["revenue", "3-month average"],
        labels={"order_month": "", "value": "Revenue", "variable": ""},
    )
    fig.update_layout(hovermode="x unified", legend_title_text="")
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Category mix")
    categories = query(
        """
        SELECT category,
               SUM(net_revenue) AS revenue,
               SUM(profit)      AS profit
        FROM mart.v_line_items
        GROUP BY category
        ORDER BY revenue DESC
        """
    )
    st.plotly_chart(
        px.pie(categories, names="category", values="revenue", hole=0.45),
        width="stretch",
    )

# --- Discount cliff --------------------------------------------------------
st.subheader("Where discounting stops paying")
st.caption(
    "Margin by discount band. The point of the chart is the cliff, not the slope."
)
discount = query(
    """
    SELECT CASE
               WHEN discount = 0     THEN '0%'
               WHEN discount <= 0.10 THEN '01-10%'
               WHEN discount <= 0.20 THEN '11-20%'
               WHEN discount <= 0.30 THEN '21-30%'
               WHEN discount <= 0.50 THEN '31-50%'
               ELSE                       '50%+'
           END AS discount_band,
           MIN(discount)                                          AS sort_key,
           SUM(net_revenue)                                       AS revenue,
           SUM(profit)                                            AS profit,
           ROUND(100.0 * SUM(profit) / NULLIF(SUM(net_revenue), 0), 2) AS margin_pct
    FROM mart.v_line_items
    GROUP BY 1
    ORDER BY sort_key
    """
)
fig = px.bar(
    discount,
    x="discount_band",
    y="margin_pct",
    color="margin_pct",
    color_continuous_scale=["#c0392b", "#f39c12", "#27ae60"],
    labels={"discount_band": "Discount band", "margin_pct": "Margin %"},
)
fig.add_hline(y=0, line_dash="dash", line_color="grey")
st.plotly_chart(fig, width="stretch")

# --- Tables ----------------------------------------------------------------
tab_customers, tab_stock, tab_regions = st.tabs(
    ["Top customers", "Stock risk", "Regions"]
)

with tab_customers:
    st.dataframe(
        query(
            """
            SELECT customer_name, segment, order_count,
                   ROUND(lifetime_value, 2)  AS lifetime_value,
                   ROUND(lifetime_profit, 2) AS lifetime_profit,
                   last_order_date
            FROM mart.v_customer_ltv
            ORDER BY lifetime_value DESC
            LIMIT 25
            """
        ),
        width="stretch",
        hide_index=True,
    )

with tab_stock:
    st.caption(
        "Inventory is **synthetic** — Superstore has no stock column. "
        "Generated deterministically by the ETL so this table is stable across runs."
    )
    st.dataframe(
        query(Path(__file__).parents[1].joinpath(
            "sql/queries/q05_days_of_stock.sql").read_text(encoding="utf-8")),
        width="stretch",
        hide_index=True,
    )

with tab_regions:
    st.dataframe(
        query(
            """
            SELECT region,
                   COUNT(DISTINCT order_id)    AS orders,
                   COUNT(DISTINCT customer_id) AS customers,
                   ROUND(SUM(net_revenue), 2)  AS revenue,
                   ROUND(SUM(profit), 2)       AS profit,
                   ROUND(100.0 * SUM(profit) / NULLIF(SUM(net_revenue), 0), 1) AS margin_pct
            FROM mart.v_line_items
            GROUP BY region
            ORDER BY revenue DESC
            """
        ),
        width="stretch",
        hide_index=True,
    )
