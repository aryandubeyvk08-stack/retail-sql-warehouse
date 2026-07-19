-- ===========================================================================
-- Q06 — Top 3 revenue-generating products *within each* category.
-- Demonstrates: DENSE_RANK() with PARTITION BY, filtering on a window result
--               (which requires a CTE — you cannot use a window function in
--               WHERE, a detail interviewers like to poke at).
-- ===========================================================================
--
-- DENSE_RANK over ROW_NUMBER: on an exact revenue tie, ROW_NUMBER picks a
-- winner arbitrarily and non-deterministically between runs. DENSE_RANK keeps
-- both, which is the honest answer.

WITH product_perf AS (
    SELECT
        category,
        product_id,
        product_name,
        SUM(quantity)    AS units_sold,
        SUM(net_revenue) AS revenue,
        SUM(profit)      AS profit
    FROM mart.v_line_items
    GROUP BY category, product_id, product_name
),
ranked AS (
    SELECT
        *,
        DENSE_RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS revenue_rank,
        DENSE_RANK() OVER (PARTITION BY category ORDER BY profit  DESC) AS profit_rank,
        ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY category), 2)
            AS pct_of_category
    FROM product_perf
)
SELECT
    category,
    revenue_rank,
    product_name,
    units_sold,
    ROUND(revenue, 2) AS revenue,
    ROUND(profit, 2)  AS profit,
    pct_of_category,
    profit_rank,
    -- Best-sellers that rank far worse on profit are the discount-driven
    -- "busy but unprofitable" SKUs worth flagging to merchandising.
    CASE WHEN profit_rank - revenue_rank >= 5 THEN 'REVENUE WITHOUT MARGIN' END AS flag
FROM ranked
WHERE revenue_rank <= 3
ORDER BY category, revenue_rank;
