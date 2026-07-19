-- ===========================================================================
-- Q07 — Cumulative revenue by region over time, plus each region's share.
-- Demonstrates: PARTITION BY + ORDER BY windows, explicit frame clauses
--               (ROWS UNBOUNDED PRECEDING), moving averages, ratio-to-parent.
-- ===========================================================================
--
-- The explicit frame matters. Postgres defaults to RANGE BETWEEN UNBOUNDED
-- PRECEDING AND CURRENT ROW, which on duplicate ORDER BY values sums the whole
-- peer group at once — so ties produce a running total that jumps. Stating
-- ROWS makes the behaviour explicit and stable.

WITH regional_monthly AS (
    SELECT
        region,
        order_month,
        SUM(net_revenue)         AS revenue,
        SUM(profit)              AS profit,
        COUNT(DISTINCT order_id) AS orders
    FROM mart.v_line_items
    GROUP BY region, order_month
)
SELECT
    region,
    order_month,
    ROUND(revenue, 2) AS revenue,
    orders,

    ROUND(SUM(revenue) OVER (PARTITION BY region ORDER BY order_month
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2)
        AS cumulative_revenue,

    ROUND(AVG(revenue) OVER (PARTITION BY region ORDER BY order_month
                             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)
        AS revenue_3mo_avg,

    -- This region's share of all revenue in the same month.
    ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY order_month), 2)
        AS pct_of_month,

    -- Rank among regions for this month — shows leadership changing hands.
    RANK() OVER (PARTITION BY order_month ORDER BY revenue DESC) AS rank_in_month
FROM regional_monthly
ORDER BY region, order_month;
