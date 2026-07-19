-- ===========================================================================
-- 03_marts.sql — read layer
--
-- Analytics queries should not re-derive business logic. Anything that could
-- plausibly be defined two different ways (revenue, margin, "an active
-- customer") gets defined exactly once, here.
-- Idempotent (CREATE OR REPLACE).
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- The workhorse: one row per order line, fully denormalized.
-- Every downstream query starts here instead of writing its own 4-table join.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart.v_line_items AS
SELECT
    oi.order_item_id,
    o.order_id,
    o.order_date,
    o.ship_date,
    o.ship_mode,
    (o.ship_date - o.order_date)          AS fulfillment_days,
    DATE_TRUNC('month', o.order_date)::DATE AS order_month,

    c.customer_id,
    c.customer_name,
    c.segment,

    l.region,
    l.state,
    l.city,

    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,

    oi.quantity,
    oi.unit_price,
    oi.discount,
    oi.net_revenue,
    oi.profit,
    -- Gross = what the line would have earned at full price. The gap between
    -- gross and net is the cost of discounting, which q09 quantifies.
    (oi.quantity * oi.unit_price)         AS gross_revenue,
    (oi.quantity * oi.unit_price * oi.discount) AS discount_amount
FROM core.order_items oi
JOIN core.orders    o ON o.order_id    = oi.order_id
JOIN core.customers c ON c.customer_id = o.customer_id
JOIN core.locations l ON l.location_id = o.location_id
JOIN core.products  p ON p.product_id  = oi.product_id;

-- ---------------------------------------------------------------------------
-- Monthly revenue spine. Used by MoM growth and running totals.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart.v_monthly_revenue AS
SELECT
    order_month,
    COUNT(DISTINCT order_id)    AS orders,
    COUNT(DISTINCT customer_id) AS active_customers,
    SUM(quantity)               AS units_sold,
    SUM(net_revenue)            AS revenue,
    SUM(profit)                 AS profit
FROM mart.v_line_items
GROUP BY order_month;

-- ---------------------------------------------------------------------------
-- Customer-level rollup. "Lifetime value" defined once, so q01 and q08 can
-- never disagree about it.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart.v_customer_ltv AS
SELECT
    customer_id,
    customer_name,
    segment,
    MIN(order_date)          AS first_order_date,
    MAX(order_date)          AS last_order_date,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(net_revenue)         AS lifetime_value,
    SUM(profit)              AS lifetime_profit,
    SUM(net_revenue) / NULLIF(COUNT(DISTINCT order_id), 0) AS avg_order_value
FROM mart.v_line_items
GROUP BY customer_id, customer_name, segment;
