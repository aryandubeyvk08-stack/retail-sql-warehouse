# Data Quality Report

**Generated:** 2026-07-19 19:07 UTC  
**Verdict:** PASSED WITH WARNINGS — 9 passed, 1 warnings, 0 failures

## Checks

| | Check | Result |
|---|---|---|
| ✅ | Row count reconciliation | raw=9,994 = loaded 9,994 + quarantined 0 + deduplicated 0 → 9,994 |
| ✅ | Dimension cardinality | 793 customers · 1,862 products · 632 locations · 5,009 orders · 9,994 line items |
| ✅ | Revenue ties back to source | SUM(net_revenue) differs from SUM(raw.sales) by 0.000000% (tolerance 0.01%) |
| ✅ | No orphan foreign keys | 0 line items without an order, 0 orders without a customer |
| ✅ | ship_date >= order_date | 0 order(s) ship before they are placed |
| ✅ | quantity > 0 on every line | 0 line item(s) with non-positive quantity |
| ✅ | Postal code completeness | 0 location(s) have no postal code in the source (kept as NULL rather than guessed) |
| ⚠️ | Loss-making line items | 18.72% of line items were sold at a loss — real, and the subject of query q09 |
| ✅ | Date coverage | orders span 2014-01-03 → 2017-12-30 |
| ✅ | Every product has a stock row | 0 product(s) missing from core.stock (q05 would silently omit them) |

## Transform notes

- Detected date format: MM/DD/YYYY.
- No rows quarantined — every source row passed validation.
- 32 product_id(s) appear under multiple names in the source (a known Superstore defect); kept the most frequent name.
- Synthesised inventory for 1,862 products (seed=42, as-of 2017-12-30). NOT source data.
