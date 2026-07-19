-- ===========================================================================
-- Q05 — Which products run out first? Days-of-stock-remaining triage.
-- Demonstrates: CTEs, CASE-based bucketing, NULLIF division guard, joining a
--               fact-derived rate against a current-state snapshot.
-- Ties this warehouse back to the Smart Restock Alert System project.
-- ===========================================================================
--
-- IMPORTANT — why this does not use CURRENT_DATE:
-- The Superstore dataset ends in 2017. `WHERE order_date >= CURRENT_DATE - 7`
-- would match nothing and the query would silently return an empty result,
-- which reads like "no products at risk" rather than "your filter is broken".
-- Anchoring to MAX(order_date) makes the query correct on any historical
-- snapshot. Swap `asof` for CURRENT_DATE the day this runs on live data.
--
-- 28-day window rather than 7: Superstore sales are sparse per SKU, so a
-- 7-day rate is mostly zeros and division noise.

WITH asof AS (
    SELECT MAX(order_date) AS today FROM core.orders
),
recent_sales AS (
    SELECT
        li.product_id,
        SUM(li.quantity)        AS units_28d,
        SUM(li.quantity) / 28.0 AS avg_daily_sales
    FROM mart.v_line_items li
    CROSS JOIN asof
    WHERE li.order_date > asof.today - INTERVAL '28 days'
    GROUP BY li.product_id
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    s.current_stock,
    s.reorder_level,
    rs.units_28d,
    ROUND(rs.avg_daily_sales, 2) AS avg_daily_sales,
    ROUND(s.current_stock / NULLIF(rs.avg_daily_sales, 0), 1) AS days_of_stock_remaining,
    CASE
        WHEN rs.avg_daily_sales IS NULL OR rs.avg_daily_sales = 0 THEN 'NO RECENT SALES'
        WHEN s.current_stock / rs.avg_daily_sales <  3 THEN 'URGENT'
        WHEN s.current_stock / rs.avg_daily_sales <  7 THEN 'MONITOR'
        ELSE 'OK'
    END AS status,
    s.last_restock_date
FROM core.products p
JOIN core.stock s        ON s.product_id  = p.product_id
-- LEFT JOIN, not JOIN: a product with zero recent sales is a *different*
-- problem (dead stock), not a row to hide from the report.
LEFT JOIN recent_sales rs ON rs.product_id = p.product_id
ORDER BY
    CASE
        WHEN rs.avg_daily_sales IS NULL OR rs.avg_daily_sales = 0 THEN 2
        WHEN s.current_stock / rs.avg_daily_sales < 7 THEN 0
        ELSE 1
    END,
    days_of_stock_remaining NULLS LAST
LIMIT 40;
