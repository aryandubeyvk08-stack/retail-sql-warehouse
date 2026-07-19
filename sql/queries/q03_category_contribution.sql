-- ===========================================================================
-- Q03 — What share of revenue and profit does each category contribute?
-- Demonstrates: window aggregate over the whole result set (SUM(SUM(x)) OVER ()),
--               running cumulative share (Pareto / 80-20 analysis).
-- ===========================================================================
--
-- The SUM(SUM(...)) OVER () pattern is the point of this query: it computes a
-- grand total *after* the GROUP BY without a second pass over the table or a
-- self-join to a totals subquery.
--
-- Note this uses net_revenue — the same discount-adjusted figure as Q01/Q02.
-- Mixing gross here and net there is why two "correct" reports stop tying out.

SELECT
    category,
    sub_category,
    SUM(quantity)                AS units_sold,
    ROUND(SUM(net_revenue), 2)   AS revenue,
    ROUND(SUM(profit), 2)        AS profit,
    ROUND(100.0 * SUM(profit) / NULLIF(SUM(net_revenue), 0), 1) AS margin_pct,

    ROUND(100.0 * SUM(net_revenue) / SUM(SUM(net_revenue)) OVER (), 2)
        AS pct_of_total_revenue,

    ROUND(100.0 * SUM(net_revenue) / SUM(SUM(net_revenue)) OVER (PARTITION BY category), 2)
        AS pct_within_category,

    -- Cumulative share, biggest first: read down until you hit ~80% to see how
    -- few sub-categories the business actually runs on.
    ROUND(
        100.0 * SUM(SUM(net_revenue)) OVER (ORDER BY SUM(net_revenue) DESC
                                            ROWS UNBOUNDED PRECEDING)
              / SUM(SUM(net_revenue)) OVER ()
    , 2) AS cumulative_pct
FROM mart.v_line_items
GROUP BY category, sub_category
ORDER BY revenue DESC;
