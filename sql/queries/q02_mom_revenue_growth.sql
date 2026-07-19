-- ===========================================================================
-- Q02 — How is revenue trending month over month, and how much of that is
--       just seasonality rather than real growth?
-- Demonstrates: LAG() window function, CTEs, safe division, year-over-year
--               comparison via a 12-period offset.
-- ===========================================================================
--
-- Why both MoM and YoY: retail is strongly seasonal (Superstore peaks every
-- Q4). A -30% MoM in January looks alarming until you see it is +15% YoY.
-- Reporting MoM alone is how people talk themselves into a fake crisis.

WITH monthly AS (
    SELECT order_month, revenue, orders, active_customers
    FROM mart.v_monthly_revenue
)
SELECT
    order_month,
    ROUND(revenue, 2) AS revenue,
    orders,
    active_customers,

    ROUND(LAG(revenue, 1) OVER w, 2) AS prev_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue, 1) OVER w)
              / NULLIF(LAG(revenue, 1) OVER w, 0)
    , 2) AS mom_growth_pct,

    -- 12 rows back = same month last year, because the spine has no gaps.
    ROUND(
        100.0 * (revenue - LAG(revenue, 12) OVER w)
              / NULLIF(LAG(revenue, 12) OVER w, 0)
    , 2) AS yoy_growth_pct,

    -- 3-month moving average smooths the seasonal noise out of the trend line.
    ROUND(AVG(revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)
        AS revenue_3mo_avg
FROM monthly
WINDOW w AS (ORDER BY order_month)
ORDER BY order_month;
