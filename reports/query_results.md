# Query Results

**Generated:** 2026-07-19 19:04 UTC  
Showing up to 20 rows per result set. Full SQL lives in [`sql/queries/`](../sql/queries).

---

## `q01_top_customers_by_ltv.sql`

*Q01 — Who are our 10 most valuable customers, and are they actually profitable?*

10 row(s) in 187 ms

| customer_id   | customer_name      | segment     |   order_count |   lifetime_value |   lifetime_profit |   margin_pct |   avg_order_value | last_order_date   |
|:--------------|:-------------------|:------------|--------------:|-----------------:|------------------:|-------------:|------------------:|:------------------|
| SM-20320      | Sean Miller        | Home Office |             5 |        25,043.05 |         -1,980.75 |        -7.90 |          5,008.61 | 2017-10-12        |
| TC-20980      | Tamara Chand       | Corporate   |             5 |        19,052.22 |          8,981.32 |        47.10 |          3,810.44 | 2016-11-26        |
| RB-19360      | Raymond Buch       | Consumer    |             6 |        15,117.34 |          6,976.09 |        46.10 |          2,519.56 | 2017-09-25        |
| TA-21385      | Tom Ashbrook       | Home Office |             4 |        14,595.62 |          4,703.80 |        32.20 |          3,648.91 | 2017-10-22        |
| AB-10105      | Adrian Barton      | Consumer    |            10 |        14,473.57 |          5,444.81 |        37.60 |          1,447.36 | 2017-11-19        |
| KL-16645      | Ken Lonsdale       | Consumer    |            12 |        14,175.23 |            806.84 |         5.70 |          1,181.27 | 2017-11-13        |
| SC-20095      | Sanjit Chand       | Consumer    |             9 |        14,142.33 |          5,757.42 |        40.70 |          1,571.37 | 2017-01-15        |
| HL-15040      | Hunter Lopez       | Consumer    |             6 |        12,873.30 |          5,622.43 |        43.70 |          2,145.55 | 2017-11-17        |
| SE-20110      | Sanjit Engle       | Consumer    |            11 |        12,209.44 |          2,650.67 |        21.70 |          1,109.95 | 2017-12-21        |
| CC-12370      | Christopher Conant | Consumer    |             5 |        12,129.07 |          2,177.05 |        17.90 |          2,425.81 | 2017-11-17        |

---

## `q02_mom_revenue_growth.sql`

*Q02 — How is revenue trending month over month, and how much of that is*

48 row(s) in 104 ms

| order_month   |   revenue |   orders |   active_customers |   prev_month_revenue |   mom_growth_pct |   yoy_growth_pct |   revenue_3mo_avg |
|:--------------|----------:|---------:|-------------------:|---------------------:|-----------------:|-----------------:|------------------:|
| 2014-01-01    | 14,236.90 |       32 |                 32 |               nan    |           nan    |           nan    |         14,236.90 |
| 2014-02-01    |  4,519.89 |       28 |                 27 |            14,236.90 |           -68.25 |           nan    |          9,378.39 |
| 2014-03-01    | 55,691.01 |       71 |                 69 |             4,519.89 |         1,132.13 |           nan    |         24,815.93 |
| 2014-04-01    | 28,295.35 |       66 |                 64 |            55,691.01 |           -49.19 |           nan    |         29,502.08 |
| 2014-05-01    | 23,648.29 |       69 |                 67 |            28,295.35 |           -16.42 |           nan    |         35,878.21 |
| 2014-06-01    | 34,595.13 |       66 |                 63 |            23,648.29 |            46.29 |           nan    |         28,846.25 |
| 2014-07-01    | 33,946.39 |       65 |                 65 |            34,595.13 |            -1.88 |           nan    |         30,729.94 |
| 2014-08-01    | 27,909.47 |       72 |                 70 |            33,946.39 |           -17.78 |           nan    |         32,150.33 |
| 2014-09-01    | 81,777.35 |      130 |                118 |            27,909.47 |           193.01 |           nan    |         47,877.74 |
| 2014-10-01    | 31,453.39 |       78 |                 75 |            81,777.35 |           -61.54 |           nan    |         47,046.74 |
| 2014-11-01    | 78,628.72 |      151 |                139 |            31,453.39 |           149.98 |           nan    |         63,953.15 |
| 2014-12-01    | 69,545.62 |      141 |                134 |            78,628.72 |           -11.55 |           nan    |         59,875.91 |
| 2015-01-01    | 18,174.08 |       29 |                 28 |            69,545.62 |           -73.87 |            27.65 |         55,449.47 |
| 2015-02-01    | 11,951.41 |       36 |                 36 |            18,174.08 |           -34.24 |           164.42 |         33,223.70 |
| 2015-03-01    | 38,726.25 |       79 |                 77 |            11,951.41 |           224.03 |           -30.46 |         22,950.58 |
| 2015-04-01    | 34,195.21 |       72 |                 69 |            38,726.25 |           -11.70 |            20.85 |         28,290.96 |
| 2015-05-01    | 30,131.69 |       74 |                 69 |            34,195.21 |           -11.88 |            27.42 |         34,351.05 |
| 2015-06-01    | 24,797.29 |       68 |                 68 |            30,131.69 |           -17.70 |           -28.32 |         29,708.06 |
| 2015-07-01    | 28,765.33 |       66 |                 64 |            24,797.29 |            16.00 |           -15.26 |         27,898.10 |
| 2015-08-01    | 36,898.33 |       68 |                 64 |            28,765.33 |            28.27 |            32.21 |         30,153.65 |

*…28 more rows omitted.*

---

## `q03_category_contribution.sql`

*Q03 — What share of revenue and profit does each category contribute?*

17 row(s) in 74 ms

| category        | sub_category   |   units_sold |    revenue |     profit |   margin_pct |   pct_of_total_revenue |   pct_within_category |   cumulative_pct |
|:----------------|:---------------|-------------:|-----------:|-----------:|-------------:|-----------------------:|----------------------:|-----------------:|
| Technology      | Phones         |        3,289 | 330,007.05 |  44,516.06 |        13.50 |                  14.37 |                 39.47 |            14.37 |
| Furniture       | Chairs         |        2,356 | 328,449.10 |  26,590.08 |         8.10 |                  14.30 |                 44.27 |            28.66 |
| Office Supplies | Storage        |        3,158 | 223,843.61 |  21,278.90 |         9.50 |                   9.74 |                 31.13 |            38.41 |
| Furniture       | Tables         |        1,241 | 206,965.53 | -17,725.57 |        -8.60 |                   9.01 |                 27.89 |            47.42 |
| Office Supplies | Binders        |        5,974 | 203,412.73 |  30,221.48 |        14.90 |                   8.85 |                 28.29 |            56.27 |
| Technology      | Machines       |          440 | 189,238.63 |   3,384.72 |         1.80 |                   8.24 |                 22.63 |            64.51 |
| Technology      | Accessories    |        2,976 | 167,380.32 |  41,936.78 |        25.10 |                   7.29 |                 20.02 |            71.80 |
| Technology      | Copiers        |          234 | 149,528.03 |  55,617.88 |        37.20 |                   6.51 |                 17.88 |            78.31 |
| Furniture       | Bookcases      |          868 | 114,880.00 |  -3,472.59 |        -3.00 |                   5.00 |                 15.48 |            83.31 |
| Office Supplies | Appliances     |        1,729 | 107,532.16 |  18,137.99 |        16.90 |                   4.68 |                 14.95 |            87.99 |
| Furniture       | Furnishings    |        3,563 |  91,705.16 |  13,059.18 |        14.20 |                   3.99 |                 12.36 |            91.98 |
| Office Supplies | Paper          |        5,178 |  78,479.21 |  34,053.11 |        43.40 |                   3.42 |                 10.91 |            95.40 |
| Office Supplies | Supplies       |          647 |  46,673.54 |  -1,189.08 |        -2.50 |                   2.03 |                  6.49 |            97.43 |
| Office Supplies | Art            |        3,000 |  27,118.79 |   6,527.84 |        24.10 |                   1.18 |                  3.77 |            98.61 |
| Office Supplies | Envelopes      |          906 |  16,476.40 |   6,964.06 |        42.30 |                   0.72 |                  2.29 |            99.32 |
| Office Supplies | Labels         |        1,400 |  12,486.31 |   5,546.18 |        44.40 |                   0.54 |                  1.74 |            99.87 |
| Office Supplies | Fasteners      |          914 |   3,024.28 |     949.52 |        31.40 |                   0.13 |                  0.42 |           100.00 |

---

## `q04_cohort_retention.sql`

*Q04 — Do customers come back? Monthly acquisition cohorts, tracked forward.*

**Statement 1** — 894 row(s) in 242 ms

| cohort_month   |   customers_acquired |   months_since_acquisition |   customers_active |   retention_pct |
|:---------------|---------------------:|---------------------------:|-------------------:|----------------:|
| 2014-01-01     |                   32 |                          0 |                 32 |          100.00 |
| 2014-01-01     |                   32 |                          1 |                  3 |            9.40 |
| 2014-01-01     |                   32 |                          3 |                  2 |            6.30 |
| 2014-01-01     |                   32 |                          4 |                  2 |            6.30 |
| 2014-01-01     |                   32 |                          6 |                  2 |            6.30 |
| 2014-01-01     |                   32 |                          7 |                  4 |           12.50 |
| 2014-01-01     |                   32 |                          8 |                  5 |           15.60 |
| 2014-01-01     |                   32 |                          9 |                  3 |            9.40 |
| 2014-01-01     |                   32 |                         10 |                  7 |           21.90 |
| 2014-01-01     |                   32 |                         11 |                  5 |           15.60 |
| 2014-01-01     |                   32 |                         12 |                  3 |            9.40 |
| 2014-01-01     |                   32 |                         14 |                  3 |            9.40 |
| 2014-01-01     |                   32 |                         15 |                  3 |            9.40 |
| 2014-01-01     |                   32 |                         16 |                  3 |            9.40 |
| 2014-01-01     |                   32 |                         17 |                  4 |           12.50 |
| 2014-01-01     |                   32 |                         18 |                  3 |            9.40 |
| 2014-01-01     |                   32 |                         19 |                  2 |            6.30 |
| 2014-01-01     |                   32 |                         20 |                  4 |           12.50 |
| 2014-01-01     |                   32 |                         22 |                  6 |           18.80 |
| 2014-01-01     |                   32 |                         23 |                  5 |           15.60 |

*…874 more rows omitted.*

**Statement 2** — 64 row(s) in 80 ms

| customer_id   | customer_name        | segment     |   lifetime_value |
|:--------------|:---------------------|:------------|-----------------:|
| SC-20095      | Sanjit Chand         | Consumer    |        14,142.33 |
| CJ-12010      | Caroline Jumper      | Consumer    |        11,164.97 |
| EH-13765      | Edward Hooks         | Corporate   |        10,310.88 |
| CM-12385      | Christopher Martinez | Consumer    |         8,954.02 |
| KD-16495      | Keith Dawkins        | Corporate   |         8,181.26 |
| PS-19045      | Penelope Sewall      | Home Office |         6,843.63 |
| AR-10540      | Andy Reiter          | Consumer    |         6,608.45 |
| BH-11710      | Brosina Hoffman      | Consumer    |         6,255.35 |
| AD-10180      | Alan Dominguez       | Home Office |         6,106.88 |
| MH-18115      | Mick Hernandez       | Home Office |         5,503.09 |
| DP-13390      | Dennis Pardue        | Home Office |         5,480.72 |
| CP-12085      | Cathy Prescott       | Corporate   |         5,402.25 |
| TT-21460      | Tonja Turnell        | Home Office |         5,364.81 |
| SC-20725      | Steven Cartwright    | Consumer    |         5,226.21 |
| BW-11110      | Bart Watters         | Corporate   |         4,750.36 |
| GB-14575      | Giulietta Baptist    | Consumer    |         4,716.29 |
| TP-21130      | Theone Pippenger     | Consumer    |         4,454.06 |
| BD-11500      | Bradley Drucker      | Consumer    |         4,411.24 |
| MM-17920      | Michael Moore        | Consumer    |         3,794.08 |
| CA-11965      | Carol Adams          | Corporate   |         3,789.72 |

*…44 more rows omitted.*

---

## `q05_days_of_stock.sql`

*Q05 — Which products run out first? Days-of-stock-remaining triage.*

40 row(s) in 71 ms

| product_id      | product_name                                                                    | category        |   current_stock |   reorder_level |   units_28d |   avg_daily_sales |   days_of_stock_remaining | status   | last_restock_date   |
|:----------------|:--------------------------------------------------------------------------------|:----------------|----------------:|----------------:|------------:|------------------:|--------------------------:|:---------|:--------------------|
| OFF-BI-10004209 | Fellowes Twister Kit, Gray/Clear, 3/pkg                                         | Office Supplies |               1 |               2 |           8 |              0.29 |                      3.50 | MONITOR  | 2017-12-27          |
| OFF-AP-10003622 | Bravo II Megaboss 12-Amp Hard Body Upright, Replacement Belts, 2 Belts per Pack | Office Supplies |               1 |               2 |           7 |              0.25 |                      4.00 | MONITOR  | 2017-12-16          |
| OFF-ST-10003208 | Adjustable Depth Letter/Legal Cart                                              | Office Supplies |               1 |               2 |           7 |              0.25 |                      4.00 | MONITOR  | 2017-12-12          |
| FUR-CH-10001797 | Safco Chair Connectors, 6/Carton                                                | Furniture       |               1 |               2 |           7 |              0.25 |                      4.00 | MONITOR  | 2017-12-27          |
| OFF-SU-10000946 | Staple remover                                                                  | Office Supplies |               1 |               2 |           7 |              0.25 |                      4.00 | MONITOR  | 2017-12-12          |
| OFF-AR-10000422 | Pencil and Crayon Sharpener                                                     | Office Supplies |               1 |               2 |           7 |              0.25 |                      4.00 | MONITOR  | 2017-12-27          |
| FUR-TA-10002903 | Bevis Round Bullnose 29" High Table Top                                         | Furniture       |               1 |               2 |           6 |              0.21 |                      4.70 | MONITOR  | 2017-12-23          |
| OFF-FA-10001332 | Acco Banker's Clasps, 5 3/4"-Long                                               | Office Supplies |               1 |               2 |           6 |              0.21 |                      4.70 | MONITOR  | 2017-12-18          |
| FUR-FU-10001940 | Staple-based wall hangings                                                      | Furniture       |               1 |               2 |           5 |              0.18 |                      5.60 | MONITOR  | 2017-12-12          |
| FUR-FU-10000320 | OIC Stacking Trays                                                              | Furniture       |               1 |               2 |           5 |              0.18 |                      5.60 | MONITOR  | 2017-12-25          |
| OFF-ST-10002289 | Safco Wire Cube Shelving System, For Use as 4 or 5 14" Cubes, Black             | Office Supplies |               1 |               2 |           5 |              0.18 |                      5.60 | MONITOR  | 2017-12-17          |
| OFF-BI-10001120 | Ibico EPK-21 Electric Binding System                                            | Office Supplies |               1 |               2 |           5 |              0.18 |                      5.60 | MONITOR  | 2017-12-24          |
| OFF-PA-10002222 | Xerox Color Copier Paper, 11" x 17", Ream                                       | Office Supplies |               1 |               2 |           5 |              0.18 |                      5.60 | MONITOR  | 2017-12-30          |
| OFF-PA-10001509 | Recycled Desk Saver Line "While You Were Out" Book, 5 1/2" X 4"                 | Office Supplies |               1 |               2 |           5 |              0.18 |                      5.60 | MONITOR  | 2017-12-10          |
| OFF-LA-10001404 | Avery 517                                                                       | Office Supplies |               1 |               2 |           5 |              0.18 |                      5.60 | MONITOR  | 2017-12-13          |
| OFF-PA-10002709 | Xerox 1956                                                                      | Office Supplies |               1 |               2 |           5 |              0.18 |                      5.60 | MONITOR  | 2017-12-18          |
| OFF-PA-10003651 | Xerox 1968                                                                      | Office Supplies |               2 |               3 |           9 |              0.32 |                      6.20 | MONITOR  | 2017-12-10          |
| OFF-AR-10004441 | BIC Brite Liner Highlighters                                                    | Office Supplies |               2 |               2 |           8 |              0.29 |                      7.00 | MONITOR  | 2017-12-29          |
| OFF-ST-10001328 | Personal Filing Tote with Lid, Black/Gray                                       | Office Supplies |               1 |               1 |           4 |              0.14 |                      7.00 | OK       | 2017-12-19          |
| FUR-FU-10001935 | 3M Hangers With Command Adhesive                                                | Furniture       |               1 |               1 |           4 |              0.14 |                      7.00 | OK       | 2017-12-06          |

*…20 more rows omitted.*

---

## `q06_top_products_per_category.sql`

*Q06 — Top 3 revenue-generating products *within each* category.*

9 row(s) in 99 ms

| category        |   revenue_rank | product_name                                                                |   units_sold |   revenue |    profit |   pct_of_category |   profit_rank | flag                   |
|:----------------|---------------:|:----------------------------------------------------------------------------|-------------:|----------:|----------:|------------------:|--------------:|:-----------------------|
| Furniture       |              1 | HON 5400 Series Task Chairs for Big and Tall                                |           39 | 21,870.58 |      0.00 |              2.95 |           252 | REVENUE WITHOUT MARGIN |
| Furniture       |              2 | Riverside Palais Royal Lawyers Bookcase, Royale Cherry Finish               |           24 | 15,610.97 |   -669.53 |              2.10 |           361 | REVENUE WITHOUT MARGIN |
| Furniture       |              3 | Bretford Rectangular Conference Table Tops                                  |           46 | 12,995.29 |   -327.25 |              1.75 |           335 | REVENUE WITHOUT MARGIN |
| Office Supplies |              1 | Fellowes PB500 Electric Punch Plastic Comb Binding Machine with Manual Bind |           31 | 27,453.38 |  7,753.04 |              3.82 |             1 | nan                    |
| Office Supplies |              2 | GBC DocuBind TL300 Electric Binding System                                  |           37 | 19,823.48 |  2,233.50 |              2.76 |             6 | nan                    |
| Office Supplies |              3 | GBC Ibimaster 500 Manual ProClick Binding System                            |           48 | 19,024.50 |    760.98 |              2.65 |            28 | REVENUE WITHOUT MARGIN |
| Technology      |              1 | Canon imageCLASS 2200 Advanced Copier                                       |           20 | 61,599.82 | 25,199.94 |              7.37 |             1 | nan                    |
| Technology      |              2 | Cisco TelePresence System EX90 Videoconferencing Unit                       |            6 | 22,638.48 | -1,811.08 |              2.71 |           398 | REVENUE WITHOUT MARGIN |
| Technology      |              3 | Hewlett Packard LaserJet 3310 Copier                                        |           38 | 18,839.69 |  6,983.89 |              2.25 |             2 | nan                    |

---

## `q07_regional_running_totals.sql`

*Q07 — Cumulative revenue by region over time, plus each region's share.*

192 row(s) in 86 ms

| region   | order_month   |   revenue |   orders |   cumulative_revenue |   revenue_3mo_avg |   pct_of_month |   rank_in_month |
|:---------|:--------------|----------:|---------:|---------------------:|------------------:|---------------:|----------------:|
| Central  | 2014-01-01    |  1,539.91 |        8 |             1,539.91 |          1,539.91 |          10.82 |               3 |
| Central  | 2014-02-01    |  1,233.17 |       11 |             2,773.08 |          1,386.54 |          27.28 |               2 |
| Central  | 2014-03-01    |  5,827.60 |       14 |             8,600.68 |          2,866.89 |          10.46 |               4 |
| Central  | 2014-04-01    |  3,712.34 |        9 |            12,313.02 |          3,591.04 |          13.12 |               3 |
| Central  | 2014-05-01    |  4,048.51 |       20 |            16,361.53 |          4,529.48 |          17.12 |               4 |
| Central  | 2014-06-01    |  9,646.30 |       21 |            26,007.83 |          5,802.38 |          27.88 |               2 |
| Central  | 2014-07-01    |  6,740.57 |       13 |            32,748.40 |          6,811.79 |          19.86 |               2 |
| Central  | 2014-08-01    |  3,022.18 |        9 |            35,770.58 |          6,469.69 |          10.83 |               4 |
| Central  | 2014-09-01    | 34,408.69 |       29 |            70,179.27 |         14,723.82 |          42.08 |               1 |
| Central  | 2014-10-01    |  8,965.76 |       16 |            79,145.03 |         15,465.54 |          28.50 |               1 |
| Central  | 2014-11-01    | 14,057.57 |       41 |            93,202.60 |         19,144.01 |          17.88 |               3 |
| Central  | 2014-12-01    | 10,635.57 |       39 |           103,838.16 |         11,219.63 |          15.29 |               3 |
| Central  | 2015-01-01    |  2,510.51 |        7 |           106,348.68 |          9,067.88 |          13.81 |               4 |
| Central  | 2015-02-01    |  2,527.59 |        8 |           108,876.26 |          5,224.55 |          21.15 |               2 |
| Central  | 2015-03-01    |  6,730.27 |       20 |           115,606.53 |          3,922.79 |          17.38 |               3 |
| Central  | 2015-04-01    | 11,642.06 |       19 |           127,248.59 |          6,966.64 |          34.05 |               1 |
| Central  | 2015-05-01    |  8,623.90 |       19 |           135,872.49 |          8,998.74 |          28.62 |               2 |
| Central  | 2015-06-01    |  3,713.19 |       14 |           139,585.68 |          7,993.05 |          14.97 |               4 |
| Central  | 2015-07-01    |  7,605.57 |       15 |           147,191.24 |          6,647.55 |          26.44 |               2 |
| Central  | 2015-08-01    |  9,301.45 |       16 |           156,492.69 |          6,873.40 |          25.21 |               3 |

*…172 more rows omitted.*

---

## `q08_rfm_segmentation.sql`

*Q08 — RFM customer segmentation (Recency, Frequency, Monetary).*

793 row(s) in 219 ms

| customer_id   | customer_name      | segment     |   recency_days |   frequency |   monetary |   r_score |   f_score |   m_score |   rfm_cell | rfm_segment          |
|:--------------|:-------------------|:------------|---------------:|------------:|-----------:|----------:|----------:|----------:|-----------:|:---------------------|
| SM-20320      | Sean Miller        | Home Office |             79 |           5 |  25,043.05 |         3 |         2 |         5 |        325 | Needs Attention      |
| TC-20980      | Tamara Chand       | Corporate   |            399 |           5 |  19,052.22 |         1 |         2 |         5 |        125 | Lost                 |
| RB-19360      | Raymond Buch       | Consumer    |             96 |           6 |  15,117.34 |         3 |         3 |         5 |        335 | Needs Attention      |
| TA-21385      | Tom Ashbrook       | Home Office |             69 |           4 |  14,595.62 |         3 |         2 |         5 |        325 | Needs Attention      |
| AB-10105      | Adrian Barton      | Consumer    |             41 |          10 |  14,473.57 |         4 |         5 |         5 |        455 | Champions            |
| KL-16645      | Ken Lonsdale       | Consumer    |             47 |          12 |  14,175.23 |         4 |         5 |         5 |        455 | Champions            |
| SC-20095      | Sanjit Chand       | Consumer    |            349 |           9 |  14,142.33 |         1 |         5 |         5 |        155 | At Risk — High Value |
| HL-15040      | Hunter Lopez       | Consumer    |             43 |           6 |  12,873.30 |         4 |         3 |         5 |        435 | Loyal                |
| SE-20110      | Sanjit Engle       | Consumer    |              9 |          11 |  12,209.44 |         5 |         5 |         5 |        555 | Champions            |
| CC-12370      | Christopher Conant | Consumer    |             43 |           5 |  12,129.07 |         4 |         2 |         5 |        425 | New / Promising      |
| TS-21370      | Todd Sumrall       | Corporate   |             36 |           6 |  11,891.75 |         4 |         3 |         5 |        435 | Loyal                |
| GT-14710      | Greg Tran          | Consumer    |             36 |          11 |  11,820.12 |         4 |         5 |         5 |        455 | Champions            |
| BM-11140      | Becky Martin       | Consumer    |            307 |           4 |  11,789.63 |         1 |         2 |         5 |        125 | Lost                 |
| SV-20365      | Seth Vernon        | Consumer    |            101 |          10 |  11,470.95 |         3 |         5 |         5 |        355 | Needs Attention      |
| CJ-12010      | Caroline Jumper    | Consumer    |            189 |           8 |  11,164.97 |         2 |         4 |         5 |        245 | At Risk — High Value |
| CL-12565      | Clay Ludtke        | Consumer    |            284 |          12 |  10,880.55 |         1 |         5 |         5 |        155 | At Risk — High Value |
| ME-17320      | Maria Etezadi      | Home Office |             42 |          10 |  10,663.73 |         4 |         5 |         5 |        455 | Champions            |
| KF-16285      | Karen Ferguson     | Home Office |             97 |           7 |  10,604.27 |         3 |         4 |         5 |        345 | Needs Attention      |
| BS-11365      | Bill Shonely       | Corporate   |            558 |           5 |  10,501.65 |         1 |         2 |         5 |        125 | Lost                 |
| EH-13765      | Edward Hooks       | Corporate   |            135 |          12 |  10,310.88 |         2 |         5 |         5 |        255 | At Risk — High Value |

*…773 more rows omitted.*

---

## `q09_discount_impact_on_margin.sql`

*Q09 — At what discount level do we stop making money?*

7 row(s) in 86 ms

| discount_band   |   line_items |   units_sold |   gross_revenue |   revenue_given_away |   net_revenue |     profit |   margin_pct |   loss_making_lines |   loss_making_pct |
|:----------------|-------------:|-------------:|----------------:|---------------------:|--------------:|-----------:|-------------:|--------------------:|------------------:|
| 0% (full price) |        4,798 |       18,267 |    1,087,908.47 |                 0.00 |  1,087,908.47 | 320,987.01 |        29.50 |                   0 |              0.00 |
| 01-10%          |           94 |          373 |       60,410.39 |             6,041.04 |     54,369.35 |   9,029.21 |        16.61 |                   4 |              4.30 |
| 11-20%          |        3,709 |       13,858 |      988,164.75 |           196,011.86 |    792,152.89 |  91,756.60 |        11.58 |                 519 |             14.00 |
| 21-30%          |          227 |          849 |      147,466.65 |            44,240.00 |    103,226.66 | -10,369.32 |       -10.05 |                 208 |             91.60 |
| 31-50%          |          310 |        1,177 |      343,153.31 |           147,838.55 |    195,314.76 | -48,447.83 |       -24.81 |                 284 |             91.60 |
| 50%+            |          856 |        3,349 |      236,831.47 |           172,602.73 |     64,228.74 | -76,559.13 |      -119.20 |                 856 |            100.00 |
| ALL LINES       |        9,994 |       37,873 |    2,863,935.04 |           566,734.18 |  2,297,200.86 | 286,396.54 |        12.47 |               1,871 |             18.70 |

---

## `q10_repeat_purchase_and_fulfillment.sql`

*Q10 — Two operational questions in one file.*

**Statement 1** — 1 row(s) in 101 ms

| metric                   |   repeat_orders |   repeat_customers |   avg_gap_days |   median_gap_days |   p90_gap_days |   min_gap_days |   max_gap_days |
|:-------------------------|----------------:|-------------------:|---------------:|------------------:|---------------:|---------------:|---------------:|
| Repeat purchase interval |           4,216 |                781 |         188.00 |            128.50 |         443.50 |              0 |          1,364 |

**Statement 2** — 4 row(s) in 101 ms

| ship_mode      |   orders |   avg_days |   median_days |   p90_days |   worst_days |   same_day_orders |   pct_over_5_days |
|:---------------|---------:|-----------:|--------------:|-----------:|-------------:|------------------:|------------------:|
| Same Day       |      264 |       0.05 |          0.00 |       0.00 |            1 |               252 |              0.00 |
| First Class    |      787 |       2.19 |          2.00 |       3.00 |            4 |                 0 |              0.00 |
| Second Class   |      964 |       3.23 |          3.00 |       5.00 |            5 |                 0 |              0.00 |
| Standard Class |    2,994 |       5.00 |          5.00 |       7.00 |            7 |                 0 |             30.20 |

