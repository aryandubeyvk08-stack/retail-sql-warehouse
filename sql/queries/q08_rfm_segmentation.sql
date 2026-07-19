-- ===========================================================================
-- Q08 — RFM customer segmentation (Recency, Frequency, Monetary).
-- Demonstrates: NTILE() for quintile scoring, layered CTEs, multi-condition
--               CASE segmentation — the standard retail-analytics deliverable.
-- ===========================================================================
--
-- Score direction is the easy thing to get backwards: for Recency, *smaller*
-- days-since-last-order is better, so the NTILE is ordered DESC to make
-- quintile 5 the most recent buyers. F and M order ASC so 5 is the biggest.
-- All three then read the same way — 5 is always good.
--
-- Anchored to MAX(order_date), not CURRENT_DATE, for the same reason as Q05:
-- on a 2017 snapshot every customer would otherwise score as "lapsed".

WITH asof AS (
    SELECT MAX(order_date) AS today FROM core.orders
),
rfm_base AS (
    SELECT
        ltv.customer_id,
        ltv.customer_name,
        ltv.segment,
        (asof.today - ltv.last_order_date) AS recency_days,
        ltv.order_count                    AS frequency,
        ltv.lifetime_value                 AS monetary
    FROM mart.v_customer_ltv ltv
    CROSS JOIN asof
),
scored AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,  -- 5 = bought most recently
        NTILE(5) OVER (ORDER BY frequency    ASC ) AS f_score,  -- 5 = buys most often
        NTILE(5) OVER (ORDER BY monetary     ASC ) AS m_score   -- 5 = spends most
    FROM rfm_base
)
SELECT
    customer_id,
    customer_name,
    segment,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary,
    r_score, f_score, m_score,
    (r_score::TEXT || f_score::TEXT || m_score::TEXT) AS rfm_cell,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 3                  THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2                  THEN 'New / Promising'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'At Risk — High Value'
        WHEN r_score <= 2 AND f_score <= 2                  THEN 'Lost'
        WHEN r_score = 3                                    THEN 'Needs Attention'
        ELSE 'Others'
    END AS rfm_segment
FROM scored
ORDER BY monetary DESC;
