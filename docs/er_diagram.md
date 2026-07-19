# Schema & ER Diagram

GitHub renders Mermaid natively, so this diagram stays in sync with the repo
instead of drifting away from a PNG someone exported once and never updated.

## Entity relationships (`core` schema)

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    LOCATIONS ||--o{ ORDERS : "ships to"
    ORDERS    ||--|{ ORDER_ITEMS : contains
    PRODUCTS  ||--o{ ORDER_ITEMS : "sold as"
    PRODUCTS  ||--|| STOCK : "has snapshot"

    CUSTOMERS {
        varchar customer_id PK
        varchar customer_name
        varchar segment
    }

    LOCATIONS {
        serial  location_id PK
        varchar country
        varchar state
        varchar city
        varchar postal_code "nullable"
        varchar region
    }

    PRODUCTS {
        varchar product_id PK
        varchar product_name
        varchar category
        varchar sub_category
        numeric list_price
    }

    ORDERS {
        varchar order_id PK
        varchar customer_id FK
        int     location_id FK
        date    order_date
        date    ship_date
        varchar ship_mode
    }

    ORDER_ITEMS {
        int     order_item_id PK
        varchar order_id FK
        varchar product_id FK
        int     quantity
        numeric unit_price
        numeric discount
        numeric profit
        numeric net_revenue "GENERATED"
    }

    STOCK {
        varchar product_id PK,FK
        int     current_stock
        int     reorder_level
        date    last_restock_date
    }
```

## Layer flow

```mermaid
flowchart LR
    CSV[Superstore CSV] --> RAW["raw.superstore_orders<br/>(all TEXT, + lineage)"]
    RAW --> T{{"Python transform<br/>clean · type · dedupe · validate"}}
    T -->|rejected| Q["quarantine<br/>(reported, never dropped)"]
    T -->|accepted| STG["stg.*<br/>staging tables"]
    STG -->|INSERT ... ON CONFLICT| CORE["core.*<br/>normalized + constrained"]
    CORE --> MART["mart.*<br/>views · one revenue definition"]
    MART --> SQL["10 analytics queries"]
    MART --> DASH["Streamlit dashboard"]
```

---

## Design decisions worth defending

| Decision | Why | The alternative, and what it costs |
|---|---|---|
| `customer_id VARCHAR`, not `INT` | Superstore IDs look like `CG-12520` | `INT` either errors on load or truncates the key |
| Geography on `orders`, not `customers` | A customer ships to several cities across the dataset | Region on `customers` picks one city arbitrarily and quietly corrupts every regional revenue figure |
| `net_revenue` as a `GENERATED` column | One definition of revenue, enforced by the database | Repeating the arithmetic per query — until one query forgets the discount and two reports stop tying out |
| `UNIQUE NULLS NOT DISTINCT` on locations | Postal code is genuinely missing for some rows | Default `UNIQUE` treats each `NULL` as distinct, so every ETL run inserts fresh duplicate locations |
| Surrogate `location_id`, natural keys elsewhere | Location has no stable natural key; the others do | A composite natural key on four nullable columns in every `orders` row |
| `unit_price NUMERIC(12,4)` | It is derived by division, so 2dp drifts | At 2dp, `SUM(net_revenue)` no longer reconciles to `SUM(sales)` |
| Raw layer typed as all `TEXT` | A malformed value can never abort the load | A typed landing table fails before it can tell you what was wrong |
| `stock` is synthetic, and labelled everywhere | Superstore has no inventory column, but Q05 needs one | Presenting generated data as sourced — the fastest way to lose credibility |

## Exporting a PNG (optional)

Some recruiters skim the repo outside GitHub. If you want a static image:

1. Paste the `erDiagram` block into <https://mermaid.live>
2. Export PNG → save as `docs/er_diagram.png`
3. Reference it in the README alongside the Mermaid block
