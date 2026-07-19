# 🏬 Retail Sales Data Warehouse & SQL Analytics Engine

> A messy retail CSV taken all the way to a **cloud-hosted PostgreSQL warehouse** — layered schema, idempotent Python ETL, quarantine-not-drop data quality checks, and ten advanced SQL queries (window functions, CTEs, `GROUPING SETS`, `NTILE`) that answer questions a business would actually ask.

<p align="left">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-15%2B-336791">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.0-red">
  <img alt="Cloud" src="https://img.shields.io/badge/cloud-Supabase%20%7C%20AWS%20RDS-orange">
  <img alt="Tests" src="https://img.shields.io/badge/tests-26%20passing-green">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

---

## What it does

Most "SQL portfolio projects" are a flat table and five `SELECT`s. This one is
built the way a data team would actually build it, because the interesting
questions are never about the `SELECT`:

1. **Land** the raw CSV verbatim into an all-`TEXT` staging table, so a bad value can never abort the load — and so "how dirty was the source?" stays an answerable question.
2. **Transform** in Python: type coercion, date-format detection, dedupe, derived unit price. Rows that fail validation are **quarantined with a reason**, never silently dropped.
3. **Load** into a normalized, constrained schema via `INSERT ... ON CONFLICT DO UPDATE` inside a single transaction — so the pipeline is **idempotent** and re-running a failed load is safe.
4. **Verify** with an automated data quality suite that reconciles revenue from `raw` back to `core` and fails the build if anything is off.
5. **Analyse** with ten queries covering the SQL surface interviewers actually probe: window functions, frame clauses, cohort analysis, `GROUPING SETS`, ordered-set aggregates.

---

## Results

Live output, committed so a reviewer can read it without a database of their own:

- **[Data quality report](reports/data_quality_report.md)** — every check, with reasons
- **[Query results](reports/query_results.md)** — all 10 queries, real output

Run against the Kaggle *Sample - Superstore* dataset (9,994 rows, 2014–2017) on
**PostgreSQL 17.10 / Neon** `ap-southeast-1`. 12 statements, 0 failures, ~51s
end to end. Reconciliation is exact — `9,994 = 9,994 loaded + 0 quarantined +
0 deduplicated` — and `SUM(net_revenue)` ties to `SUM(raw.sales)` at
**0.000000%** drift.

### Four findings worth defending in an interview

**1. The single most valuable customer loses money.** Sean Miller is #1 by
lifetime revenue at **$25,043 — on −7.9% margin**, i.e. −$1,981 of profit.
Ranking customers by revenue doesn't just miss this, it actively promotes it.
That is why [`q01`](sql/queries/q01_top_customers_by_ltv.sql) reports margin
beside revenue rather than below it.

**2. Discounting past 20% destroys value — it doesn't taper, it snaps.**
From [`q09`](sql/queries/q09_discount_impact_on_margin.sql):

| Discount band | Net revenue | Margin | Loss-making lines |
|---|---:|---:|---:|
| 0% (full price) | $1,087,908 | **+29.5%** | 0% |
| 01–10% | $54,369 | +16.6% | 4% |
| 11–20% | $792,153 | +11.6% | 14% |
| 21–30% | $103,227 | **−10.1%** | 92% |
| 31–50% | $195,315 | −24.8% | 92% |
| 50%+ | $64,229 | **−119.2%** | **100%** |

Every single line discounted above 50% lost money, and the business gave away
$566,734 of revenue in total. The breakeven sits between 20% and 30% — a
number a merchandising team can turn straight into a discount ceiling.

**3. An entire sub-category is underwater.** Furniture → Tables did $206,966 of
revenue at **−8.6% margin** ([`q03`](sql/queries/q03_category_contribution.sql)),
and [`q06`](sql/queries/q06_top_products_per_category.sql) flags **all three**
of Furniture's top-selling products as `REVENUE WITHOUT MARGIN` — they rank in
the top 3 on revenue and around 250th–360th on profit.

**4. 52 high-value customers are quietly lapsing.**
[`q08`](sql/queries/q08_rfm_segmentation.sql) puts $286,793 of lifetime value in
the "At Risk — High Value" cell: customers who used to buy often and big, and
have now gone quiet. That is a retention list, not a report.

> **On reproducibility:** the repo also ships a synthetic generator so the
> pipeline runs without a Kaggle account. Do not cite results produced from it —
> it *constructs* margin as `0.32 − 1.15 × discount`, so `q09` finding a
> discount cliff in synthetic data would be circular. The numbers above are from
> the real dataset.

---

## Architecture

```
Superstore CSV (messy: mixed date formats, blank zips, $-formatted numbers, returns)
        │
        ▼
  raw.superstore_orders        all TEXT + _source_file + _loaded_at  (lineage)
        │
        ▼
  Python transform             coerce · dedupe · validate · derive unit_price
        │                              │
        │                              └──► quarantine (reason-coded, reported)
        ▼
  stg.*                        staging tables written by pandas
        │
        ▼  INSERT ... ON CONFLICT DO UPDATE   ← idempotent, one transaction
  core.*                       customers · locations · products
                               orders · order_items · stock
        │                      constraints + FKs + GENERATED net_revenue
        ▼
  mart.*                       v_line_items · v_monthly_revenue · v_customer_ltv
        │                      ← the single definition of "revenue"
        ▼
  10 analytics queries    +    data quality report    +    Streamlit dashboard
```

```
retail-sql-warehouse/
├── sql/
│   ├── 01_schema.sql              # raw / stg / core / mart schemas, constraints
│   ├── 02_indexes.sql             # indexes chosen from the actual query workload
│   ├── 03_marts.sql               # analytics views
│   └── queries/q01..q10.sql       # the ten deliverable queries
├── etl/
│   ├── config.py                  # .env loading, engine factory, URL masking
│   ├── extract.py                 # CSV → raw layer (encoding + header aliasing)
│   ├── transform.py               # cleaning, validation, quarantine, derivations
│   ├── load.py                    # staged upserts, one transaction
│   ├── quality.py                 # DQ checks → reports/data_quality_report.md
│   ├── run_pipeline.py            # end-to-end CLI
│   └── run_queries.py             # runs all queries → reports/query_results.md
├── tests/
│   ├── generate_sample_csv.py     # synthetic dirty CSV — run it without Kaggle
│   └── test_transform.py          # 26 offline tests, no database needed
├── dashboard/app.py               # Streamlit layer
└── docs/er_diagram.md             # Mermaid ER diagram + design rationale
```

📐 **[Schema & ER diagram →](docs/er_diagram.md)** (includes a table of every
design decision and what the alternative would have cost)

---

## Quickstart

```bash
# 1. Clone and enter
git clone https://github.com/<your-username>/retail-sql-warehouse.git
cd retail-sql-warehouse

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# 3. Dependencies
pip install -r requirements.txt

# 4. Point at your database
cp .env.example .env            # then edit DATABASE_URL

# 5. Run it
python -m etl.run_pipeline --init
python -m etl.run_queries
```

Outputs land in [`reports/`](reports): a data quality report and every query's
result set as markdown.

### Getting the data

**Option A — the real dataset (recommended).** Download *Sample - Superstore*
from [Kaggle](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
and save it as `data/raw/superstore.csv`.

**Option B — no Kaggle account.** The repo generates its own dirty dataset:

```bash
python -m tests.generate_sample_csv --rows 5000 --out data/raw/superstore.csv
```

This is **synthetic** — it exists so the pipeline runs out of the box and so
every failure mode has guaranteed test coverage. It is not presented as real
retail data anywhere.

### Setting up the cloud database

Any managed PostgreSQL 15+ instance works — the pipeline only needs a
connection string.

**Neon (~3 minutes, no credit card):** create a project at
[neon.com](https://neon.com) → *Connect* → copy the connection string → paste
into `.env` as `DATABASE_URL`. The free plan is permanent rather than a trial,
and compute scales to zero when idle. Nearest region to India is Singapore
(`ap-southeast-1`). Keep `sslmode=require` in the string — Neon requires TLS.

**Supabase:** *Project Settings → Database → Connection string → URI* (use the
Session Pooler — it is IPv4-friendly). Free projects pause after 7 days of
inactivity, so resume the project before demoing.

**AWS RDS:** *RDS → Create database → PostgreSQL → Free tier → db.t3.micro*.
Add your IP to the security group inbound rules on port 5432. Worth doing if
you want VPC/security-group experience to talk about.

`config.py` rewrites a bare `postgresql://` scheme to `postgresql+psycopg://`,
so a copy-pasted URI from any of these providers works unmodified.

**Schema requirements:** PostgreSQL **15 or newer** — `01_schema.sql` uses
`UNIQUE NULLS NOT DISTINCT` (15+) and `GENERATED ALWAYS AS ... STORED` (12+).

> **Never commit `.env`.** It is already in `.gitignore`, credentials are read
> only from the environment, and `config.py` masks the password before any URL
> is printed or logged.

---

## The ten queries

| # | Business question | SQL demonstrated |
|---|---|---|
| [01](sql/queries/q01_top_customers_by_ltv.sql) | Who are our most valuable customers — and are they profitable? | Multi-table aggregation, ranking, margin guard |
| [02](sql/queries/q02_mom_revenue_growth.sql) | How is revenue trending, and how much is just seasonality? | `LAG()`, named `WINDOW`, moving average, YoY offset |
| [03](sql/queries/q03_category_contribution.sql) | What share of revenue does each category drive? | `SUM(SUM(x)) OVER ()`, ratio-to-parent, Pareto cumulative |
| [04](sql/queries/q04_cohort_retention.sql) | Do customers come back? | Cohort matrix, CTE chaining, anti-join (and why not `NOT IN`) |
| [05](sql/queries/q05_days_of_stock.sql) | Which products run out first? | `CASE` triage, `NULLIF` guards, as-of date anchoring |
| [06](sql/queries/q06_top_products_per_category.sql) | Top 3 products *within* each category | `DENSE_RANK() OVER (PARTITION BY ...)`, filtering a window result |
| [07](sql/queries/q07_regional_running_totals.sql) | Cumulative revenue by region over time | Explicit `ROWS` frames, `RANK()` per period |
| [08](sql/queries/q08_rfm_segmentation.sql) | Which customers are champions, which are lapsing? | `NTILE(5)` quintile scoring, layered CTEs |
| [09](sql/queries/q09_discount_impact_on_margin.sql) | At what discount do we stop making money? | `GROUPING SETS`, `COUNT(*) FILTER (WHERE ...)` |
| [10](sql/queries/q10_repeat_purchase_and_fulfillment.sql) | How long until customers reorder? Are we shipping on time? | `LAG()` over partitions, `PERCENTILE_CONT` |

---

## Engineering notes (the interview-defensible part)

- **The pipeline is idempotent.** `to_sql(if_exists="append")` — what most tutorials use — either duplicates every row on a second run or dies on the primary key. Here pandas writes to `stg`, SQL merges into `core` with `ON CONFLICT DO UPDATE`, and the whole load commits or rolls back as one unit. Re-running a failed nightly load is safe.

- **Nothing is silently dropped.** Every rejected row is tagged with a reason, counted in the DQ report, and still queryable in `raw`. A pipeline that quietly discards 3% of revenue is worse than one that fails, because nobody notices.

- **Revenue is defined once.** `net_revenue` is a `GENERATED ALWAYS` column, so the database computes `quantity × unit_price × (1 − discount)` and no query can disagree. The original build guide applied the discount in two queries and forgot it in a third — those reports would never have tied out.

- **Revenue reconciles end to end.** The DQ suite joins every loaded line back to its raw row and compares `SUM(net_revenue)` against `SUM(raw.sales)`, failing above 0.01% drift. That check is why `unit_price` is `NUMERIC(12,4)` and not `(12,2)`.

- **Date formats are detected, not assumed.** `13/07/2017` can only be day-first; `07/13/2017` can only be month-first. The transform infers direction from the data, falls back to the US convention when a file is genuinely ambiguous, and **says which it chose** in the report.

- **Postal codes stay `TEXT`.** Casting them to integers eats the leading zero off every New England zip (`01234` → `1234`), which then joins to nothing. Same reason `customer_id` is `VARCHAR`: Superstore IDs look like `CG-12520`.

- **`UNIQUE NULLS NOT DISTINCT` on locations.** Standard `UNIQUE` treats every `NULL` as distinct, so a city with a missing postal code would insert a *new* duplicate location on every run and `ON CONFLICT` would never fire.

- **As-of anchoring, not `CURRENT_DATE`.** The dataset ends in 2017, so `WHERE order_date >= CURRENT_DATE - 7` returns nothing — which reads like "no products at risk" rather than "your filter is broken". Q05 and Q08 anchor to `MAX(order_date)` instead.

- **Indexes come from the workload.** PostgreSQL indexes primary keys automatically but *not* foreign keys, and every analytics query here joins on them.

---

## Tests

```bash
pytest -q     # 26 tests, fully offline — no database, no network
```

The tests target the transform layer, because that is where silent-corruption
bugs live: a bad date parse, a mangled key, a dropped row. They assert the
invariant that makes the pipeline auditable — **rows in = rows loaded + rows
quarantined**.

---

## Dashboard

```bash
streamlit run dashboard/app.py
```

![Dashboard](assets/dashboard.png)

> _Take a screenshot of the running app and save it as `assets/dashboard.png`._

Reads the same `mart` views the queries use, so the dashboard and the SQL can
never tell different stories — the KPI row shows `$2,297,201` because that is
what `SUM(net_revenue)` returns, not because a second calculation happened to
agree.

---

## Talking points this project gives you

- *"I made the database compute revenue as a generated column, because the moment two queries derive it separately, one of them forgets the discount and your reports stop tying out — usually in the meeting, not in review."*
- *"The load is idempotent — staged upserts inside one transaction — so re-running a failed job is safe. That's the difference between a script and a pipeline."*
- *"I don't drop bad rows, I quarantine them with a reason code and reconcile the totals. If 3% of revenue disappears, someone should have to notice."*
- *"Discounting past 20% is value-destroying in this dataset — margin goes from +11.6% to −10.1%, and every line above 50% off lost money. That's one query, and it turns into a discount ceiling a merchandising team can actually enforce."*
- *"The #1 customer by revenue has negative profit. That's the whole argument for reporting margin next to revenue instead of ranking on revenue and hoping."*

---

## Tech stack

PostgreSQL 15+ (Supabase / AWS RDS) · Python 3.11+ · pandas · SQLAlchemy 2.0 ·
psycopg 3 · pytest · Streamlit · Plotly

## Résumé bullet

> Designed a layered PostgreSQL data warehouse (raw → staging → normalized core
> → analytics marts) on a cloud-hosted instance, with an idempotent Python/pandas
> ETL using transactional upserts and a reason-coded quarantine + reconciliation
> suite; authored 10 advanced SQL analytics queries (window functions, CTEs,
> `GROUPING SETS`, `NTILE`) covering cohort retention, RFM segmentation, revenue
> trend and discount-margin analysis.

## License

MIT — see [`LICENSE`](LICENSE). Update the copyright line with your name before publishing.

> **Data note:** the Superstore dataset is a public sample dataset. The `stock`
> table is **synthetic**, generated by the ETL so the inventory query has
> something to run against; it is labelled as such in the schema, the ETL and
> the DQ report.
