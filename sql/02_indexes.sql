-- ===========================================================================
-- 02_indexes.sql — indexes chosen from the actual query workload
--
-- Postgres already indexes every PRIMARY KEY and UNIQUE constraint. It does
-- NOT index foreign keys — and every analytics query here joins on them, so
-- without these you get a sequential scan of order_items per join.
-- Idempotent.
-- ===========================================================================

-- Foreign-key joins (used by essentially every query)
CREATE INDEX IF NOT EXISTS idx_orders_customer       ON core.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_location       ON core.orders(location_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order     ON core.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product   ON core.order_items(product_id);

-- Time filters and DATE_TRUNC('month', order_date) grouping (q02, q04, q07)
CREATE INDEX IF NOT EXISTS idx_orders_order_date     ON core.orders(order_date);

-- Composite for the common "this customer's orders, newest first" access path
-- used by RFM (q08) and repeat-purchase gap analysis (q10).
CREATE INDEX IF NOT EXISTS idx_orders_cust_date      ON core.orders(customer_id, order_date DESC);

-- Category rollups (q03, q06) filter/group on products.category
CREATE INDEX IF NOT EXISTS idx_products_category     ON core.products(category, sub_category);

ANALYZE core.customers;
ANALYZE core.locations;
ANALYZE core.products;
ANALYZE core.orders;
ANALYZE core.order_items;
ANALYZE core.stock;
