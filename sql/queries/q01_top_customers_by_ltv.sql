-- ===========================================================================
-- Q01 — Who are our 10 most valuable customers, and are they actually profitable?
-- Demonstrates: multi-table aggregation, ranking, guarding against the classic
--               "high revenue, negative profit" trap.
-- ===========================================================================
--
-- Business framing: revenue alone is a vanity metric. A customer who buys a lot
-- at 50% discount can be your #1 by revenue and still lose you money, so the
-- margin column below is the one that actually changes a decision.

SELECT
    customer_id,
    customer_name,
    segment,
    order_count,
    ROUND(lifetime_value, 2)   AS lifetime_value,
    ROUND(lifetime_profit, 2)  AS lifetime_profit,
    ROUND(100.0 * lifetime_profit / NULLIF(lifetime_value, 0), 1) AS margin_pct,
    ROUND(avg_order_value, 2)  AS avg_order_value,
    last_order_date
FROM mart.v_customer_ltv
ORDER BY lifetime_value DESC
LIMIT 10;
