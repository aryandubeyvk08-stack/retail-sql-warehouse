-- ===========================================================================
-- 01_schema.sql — Retail Sales Data Warehouse
-- Target: PostgreSQL 15+ (Supabase / AWS RDS)
--
-- Three schemas, three responsibilities:
--   raw   : landing zone. Everything is TEXT so a bad value can never abort a
--           load. This is what lets us *measure* dirtiness instead of crashing
--           on it.
--   stg   : scratch space. The ETL writes cleaned frames here, then MERGEs into
--           core in a single transaction. Truncated on every run.
--   core  : normalized, constrained, trustworthy. Constraints here are the
--           contract — if data violates them, the ETL is wrong, not the DB.
--   mart  : read-optimized views for analytics. One definition of "revenue",
--           reused by every query.
--
-- Idempotent: safe to run repeatedly.
-- ===========================================================================

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;

-- ---------------------------------------------------------------------------
-- RAW LAYER
-- ---------------------------------------------------------------------------
-- Deliberately all-TEXT and constraint-free. The source CSV has mixed date
-- formats, blank postal codes and stray whitespace; typing this table would
-- mean the pipeline fails before we can even report what is wrong with it.
DROP TABLE IF EXISTS raw.superstore_orders;
CREATE TABLE raw.superstore_orders (
    row_id         TEXT,
    order_id       TEXT,
    order_date     TEXT,
    ship_date      TEXT,
    ship_mode      TEXT,
    customer_id    TEXT,
    customer_name  TEXT,
    segment        TEXT,
    country        TEXT,
    city           TEXT,
    state          TEXT,
    postal_code    TEXT,
    region         TEXT,
    product_id     TEXT,
    category       TEXT,
    sub_category   TEXT,
    product_name   TEXT,
    sales          TEXT,
    quantity       TEXT,
    discount       TEXT,
    profit         TEXT,
    -- Lineage columns: which file did this row come from, and when.
    _source_file   TEXT,
    _loaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE raw.superstore_orders IS
    'Untyped landing table. One row per CSV line, verbatim. Never queried by analytics.';

-- ---------------------------------------------------------------------------
-- CORE LAYER — normalized dimensions
-- ---------------------------------------------------------------------------

-- NOTE: customer_id is VARCHAR, not INT. Superstore IDs look like "CG-12520".
-- Forcing them to INT would either fail outright or silently mangle the key.
DROP TABLE IF EXISTS core.order_items CASCADE;
DROP TABLE IF EXISTS core.stock       CASCADE;
DROP TABLE IF EXISTS core.orders      CASCADE;
DROP TABLE IF EXISTS core.products    CASCADE;
DROP TABLE IF EXISTS core.locations   CASCADE;
DROP TABLE IF EXISTS core.customers   CASCADE;

CREATE TABLE core.customers (
    customer_id   VARCHAR(20)  PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    segment       VARCHAR(50)  NOT NULL
);

-- Geography is an attribute of *where an order shipped*, not of the customer:
-- the same customer appears in multiple cities across the dataset. Hanging
-- `region` off customers (as a flat CSV tempts you to) would silently pick one
-- city per customer and quietly corrupt every regional revenue number.
CREATE TABLE core.locations (
    location_id  SERIAL       PRIMARY KEY,
    country      VARCHAR(100) NOT NULL,
    state        VARCHAR(100) NOT NULL,
    city         VARCHAR(100) NOT NULL,
    postal_code  VARCHAR(20),               -- nullable: genuinely missing in source
    region       VARCHAR(50)  NOT NULL,

    -- NULLS NOT DISTINCT (PostgreSQL 15+) is the whole reason this works.
    -- By default UNIQUE treats every NULL as distinct, so a city with a missing
    -- postal code would insert a brand-new duplicate location row on every ETL
    -- run — and ON CONFLICT would never fire. This makes NULL == NULL for
    -- uniqueness, which is what we actually mean here.
    CONSTRAINT uq_locations UNIQUE NULLS NOT DISTINCT (country, state, city, postal_code)
);

CREATE TABLE core.products (
    product_id   VARCHAR(30)  PRIMARY KEY,
    product_name VARCHAR(300) NOT NULL,
    category     VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100) NOT NULL,
    -- Representative list price (median observed unit price). Actual price paid
    -- lives on the line item — see core.order_items.unit_price.
    list_price   NUMERIC(12,2) CHECK (list_price >= 0)
);

-- ---------------------------------------------------------------------------
-- CORE LAYER — facts
-- ---------------------------------------------------------------------------

CREATE TABLE core.orders (
    order_id    VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL REFERENCES core.customers(customer_id),
    location_id INT         NOT NULL REFERENCES core.locations(location_id),
    order_date  DATE        NOT NULL,
    ship_date   DATE,
    ship_mode   VARCHAR(50),
    CONSTRAINT ck_ship_after_order CHECK (ship_date IS NULL OR ship_date >= order_date)
);

CREATE TABLE core.order_items (
    order_item_id INT         PRIMARY KEY,   -- source Row ID; stable + natural
    order_id      VARCHAR(30) NOT NULL REFERENCES core.orders(order_id) ON DELETE CASCADE,
    product_id    VARCHAR(30) NOT NULL REFERENCES core.products(product_id),
    quantity      INT           NOT NULL CHECK (quantity > 0),
    -- 4 decimal places, not 2: unit_price is *derived* by dividing sales by
    -- quantity, so rounding it to cents makes SUM(net_revenue) drift away from
    -- SUM(sales) in the source. At 4dp the reconciliation check ties to <0.01%.
    unit_price    NUMERIC(12,4) NOT NULL CHECK (unit_price >= 0),
    discount      NUMERIC(5,4)  NOT NULL DEFAULT 0 CHECK (discount >= 0 AND discount < 1),
    profit        NUMERIC(12,2),

    -- ---------------------------------------------------------------------
    -- THE single definition of line revenue, computed by the database.
    --
    -- Why a generated column instead of repeating the arithmetic in every
    -- query: the moment one query applies the discount and another forgets to,
    -- your "top customers" report and your "category split" report stop adding
    -- up to the same total — and you find out in the meeting, not in review.
    -- ---------------------------------------------------------------------
    net_revenue   NUMERIC(14,4)
        GENERATED ALWAYS AS (quantity * unit_price * (1 - discount)) STORED
);

-- Current inventory position. Not part of the Superstore CSV — synthesised by
-- the ETL so the days-of-stock query has something to run against, and to keep
-- the portfolio story consistent with the Smart Restock Alert project.
CREATE TABLE core.stock (
    product_id        VARCHAR(30) PRIMARY KEY REFERENCES core.products(product_id) ON DELETE CASCADE,
    current_stock     INT NOT NULL CHECK (current_stock >= 0),
    reorder_level     INT NOT NULL DEFAULT 0 CHECK (reorder_level >= 0),
    last_restock_date DATE
);

COMMENT ON COLUMN core.order_items.net_revenue IS
    'quantity * unit_price * (1 - discount). Generated by Postgres so every query agrees.';
COMMENT ON TABLE core.stock IS
    'Simulated inventory snapshot — not sourced from Superstore. See etl/transform.py.';
