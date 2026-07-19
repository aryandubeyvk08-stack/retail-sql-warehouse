-- ===========================================================================
-- Q09 — At what discount level do we stop making money?
-- Demonstrates: CASE bucketing, conditional aggregation (FILTER), correlated
--               profitability analysis, GROUPING SETS for a totals row.
-- ===========================================================================
--
-- This is the query that most often produces a genuinely surprising answer on
-- Superstore: profit does not decline smoothly with discount, it falls off a
-- cliff. Everything above ~30% off is sold at a loss, so "just discount it" is
-- an actively value-destroying policy — exactly the kind of finding an analyst
-- is hired to surface.

SELECT
    COALESCE(
        CASE
            WHEN discount = 0     THEN '0% (full price)'
            WHEN discount <= 0.10 THEN '01-10%'
            WHEN discount <= 0.20 THEN '11-20%'
            WHEN discount <= 0.30 THEN '21-30%'
            WHEN discount <= 0.50 THEN '31-50%'
            ELSE                       '50%+'
        END,
        'ALL LINES'
    ) AS discount_band,

    COUNT(*)                              AS line_items,
    SUM(quantity)                         AS units_sold,
    ROUND(SUM(gross_revenue), 2)          AS gross_revenue,
    ROUND(SUM(discount_amount), 2)        AS revenue_given_away,
    ROUND(SUM(net_revenue), 2)            AS net_revenue,
    ROUND(SUM(profit), 2)                 AS profit,

    ROUND(100.0 * SUM(profit) / NULLIF(SUM(net_revenue), 0), 2) AS margin_pct,

    -- FILTER is the clean ANSI way to do conditional aggregation; the
    -- SUM(CASE WHEN ... THEN 1 ELSE 0 END) form works too but reads worse.
    COUNT(*) FILTER (WHERE profit < 0)    AS loss_making_lines,
    ROUND(100.0 * COUNT(*) FILTER (WHERE profit < 0) / COUNT(*), 1)
                                          AS loss_making_pct
FROM mart.v_line_items
-- GROUPING SETS gives the per-band rows AND a grand-total row in one pass,
-- instead of a UNION ALL against a second scan of the same data.
GROUP BY GROUPING SETS (
    (CASE
        WHEN discount = 0     THEN '0% (full price)'
        WHEN discount <= 0.10 THEN '01-10%'
        WHEN discount <= 0.20 THEN '11-20%'
        WHEN discount <= 0.30 THEN '21-30%'
        WHEN discount <= 0.50 THEN '31-50%'
        ELSE                       '50%+'
     END),
    ()
)
ORDER BY discount_band;
