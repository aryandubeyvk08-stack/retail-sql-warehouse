-- ===========================================================================
-- Q10 — Two operational questions in one file.
--   A) How long do customers take to come back?
--   B) Is our shipping promise being met, and by which ship mode?
-- Demonstrates: LAG() over a partition, PERCENTILE_CONT ordered-set aggregates,
--               DISTINCT-on-a-derived-grain, interval arithmetic.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- Part A — gap between consecutive orders, per customer.
--
-- The DISTINCT in customer_orders matters: mart.v_line_items is at *line item*
-- grain, so a 5-line order would otherwise look like 5 orders on the same day
-- and produce a pile of fake 0-day gaps that drag the average to nonsense.
-- ---------------------------------------------------------------------------
WITH customer_orders AS (
    SELECT DISTINCT customer_id, order_id, order_date
    FROM mart.v_line_items
),
gaps AS (
    SELECT
        customer_id,
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date
    FROM customer_orders
),
intervals AS (
    SELECT customer_id, (order_date - prev_order_date) AS gap_days
    FROM gaps
    WHERE prev_order_date IS NOT NULL   -- a customer's first order has no gap
)
SELECT
    'Repeat purchase interval'                            AS metric,
    COUNT(*)                                              AS repeat_orders,
    COUNT(DISTINCT customer_id)                           AS repeat_customers,
    ROUND(AVG(gap_days), 1)                               AS avg_gap_days,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY gap_days) AS median_gap_days,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY gap_days) AS p90_gap_days,
    MIN(gap_days)                                         AS min_gap_days,
    MAX(gap_days)                                         AS max_gap_days
FROM intervals;


-- ---------------------------------------------------------------------------
-- Part B — order-to-ship lag by ship mode.
-- Median + p90 rather than mean only: fulfillment delays are right-skewed, so
-- the mean hides the tail that actually generates customer complaints.
-- ---------------------------------------------------------------------------
WITH shipped_orders AS (
    SELECT DISTINCT order_id, ship_mode, fulfillment_days
    FROM mart.v_line_items
    WHERE fulfillment_days IS NOT NULL
)
SELECT
    ship_mode,
    COUNT(*)                                                       AS orders,
    ROUND(AVG(fulfillment_days), 2)                                AS avg_days,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fulfillment_days) AS median_days,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY fulfillment_days) AS p90_days,
    MAX(fulfillment_days)                                          AS worst_days,
    COUNT(*) FILTER (WHERE fulfillment_days = 0)                   AS same_day_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fulfillment_days > 5) / COUNT(*), 1)
                                                                   AS pct_over_5_days
FROM shipped_orders
GROUP BY ship_mode
ORDER BY median_days;
