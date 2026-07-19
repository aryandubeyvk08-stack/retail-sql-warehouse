-- ===========================================================================
-- Q04 — Do customers come back? Monthly acquisition cohorts, tracked forward.
-- Demonstrates: CTE chaining, self-join on a derived dimension, anti-join,
--               date arithmetic to build a cohort matrix.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- Part A — full cohort retention matrix.
-- Each row: "of the N customers first acquired in month X, how many were still
-- buying M months later?" This is the version worth putting in the README.
-- ---------------------------------------------------------------------------
WITH first_purchase AS (
    SELECT customer_id, MIN(order_month) AS cohort_month
    FROM mart.v_line_items
    GROUP BY customer_id
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS customers_acquired
    FROM first_purchase
    GROUP BY cohort_month
),
activity AS (
    SELECT DISTINCT customer_id, order_month
    FROM mart.v_line_items
)
SELECT
    fp.cohort_month,
    cs.customers_acquired,
    -- Whole months elapsed between the cohort month and the activity month.
    (   (EXTRACT(YEAR  FROM a.order_month) - EXTRACT(YEAR  FROM fp.cohort_month)) * 12
      + (EXTRACT(MONTH FROM a.order_month) - EXTRACT(MONTH FROM fp.cohort_month))
    )::INT AS months_since_acquisition,
    COUNT(DISTINCT a.customer_id) AS customers_active,
    ROUND(100.0 * COUNT(DISTINCT a.customer_id) / cs.customers_acquired, 1)
        AS retention_pct
FROM first_purchase fp
JOIN activity    a  ON a.customer_id  = fp.customer_id
JOIN cohort_size cs ON cs.cohort_month = fp.cohort_month
GROUP BY fp.cohort_month, cs.customers_acquired, 3
ORDER BY fp.cohort_month, months_since_acquisition;


-- ---------------------------------------------------------------------------
-- Part B — the simple churn cut: bought in one month, gone the next.
-- Dates are parameterised as CTEs so you change them in one place.
--
-- The LEFT JOIN ... WHERE IS NULL is a deliberate choice over NOT IN: if the
-- subquery ever returns a NULL customer_id, NOT IN silently returns zero rows
-- and you report "no churn" — one of the most common SQL interview traps.
-- ---------------------------------------------------------------------------
WITH params AS (
    SELECT DATE '2017-01-01' AS month_1,
           DATE '2017-02-01' AS month_2
),
month1_buyers AS (
    SELECT DISTINCT o.customer_id
    FROM core.orders o, params p
    WHERE DATE_TRUNC('month', o.order_date) = p.month_1
),
month2_buyers AS (
    SELECT DISTINCT o.customer_id
    FROM core.orders o, params p
    WHERE DATE_TRUNC('month', o.order_date) = p.month_2
)
SELECT
    m1.customer_id,
    c.customer_name,
    c.segment,
    ROUND(ltv.lifetime_value, 2) AS lifetime_value
FROM month1_buyers m1
LEFT JOIN month2_buyers m2 ON m2.customer_id = m1.customer_id
JOIN core.customers      c  ON c.customer_id  = m1.customer_id
JOIN mart.v_customer_ltv ltv ON ltv.customer_id = m1.customer_id
WHERE m2.customer_id IS NULL
ORDER BY lifetime_value DESC;
