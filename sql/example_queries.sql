-- 1. Ultimul pret si randamentul zilei pentru fiecare actiune
SELECT t.symbol, d.full_date, f.close,
       ROUND(f.daily_return * 100, 2) AS return_pct
FROM fact_daily_prices f
JOIN dim_ticker t ON f.ticker_key = t.ticker_key
JOIN dim_date   d ON f.date_key   = d.date_key
WHERE d.date_key = (SELECT MAX(date_key) FROM fact_daily_prices)
ORDER BY return_pct DESC;

-- 2. Randamentul total pe toata perioada (primul vs. ultimul pret)
WITH ordered AS (
    SELECT t.symbol, f.close,
           ROW_NUMBER() OVER (PARTITION BY t.symbol ORDER BY f.date_key ASC)  AS rn_first,
           ROW_NUMBER() OVER (PARTITION BY t.symbol ORDER BY f.date_key DESC) AS rn_last
    FROM fact_daily_prices f
    JOIN dim_ticker t ON f.ticker_key = t.ticker_key
)
SELECT symbol,
       MAX(close) FILTER (WHERE rn_first = 1) AS first_close,
       MAX(close) FILTER (WHERE rn_last = 1)  AS last_close,
       ROUND((MAX(close) FILTER (WHERE rn_last = 1)
            / MAX(close) FILTER (WHERE rn_first = 1) - 1) * 100, 2) AS total_return_pct
FROM ordered
GROUP BY symbol
ORDER BY total_return_pct DESC;

-- 3. Randamentul mediu lunar pe actiune
SELECT t.symbol, d.year, d.month,
       ROUND(AVG(f.daily_return) * 100, 3) AS avg_daily_return_pct
FROM fact_daily_prices f
JOIN dim_ticker t ON f.ticker_key = t.ticker_key
JOIN dim_date   d ON f.date_key   = d.date_key
GROUP BY t.symbol, d.year, d.month
ORDER BY t.symbol, d.year, d.month;

-- 4. Ce zi a saptamanii e cea mai buna, in medie (0 = luni)
SELECT d.day_of_week,
       ROUND(AVG(f.daily_return) * 100, 3) AS avg_return_pct,
       COUNT(*) AS nr_zile
FROM fact_daily_prices f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.day_of_week
ORDER BY d.day_of_week;

-- 5. Cea mai buna zi din perioada pentru fiecare actiune
SELECT symbol, full_date, return_pct
FROM (
    SELECT t.symbol, d.full_date,
           ROUND(f.daily_return * 100, 2) AS return_pct,
           ROW_NUMBER() OVER (PARTITION BY t.symbol ORDER BY f.daily_return DESC NULLS LAST) AS rn
    FROM fact_daily_prices f
    JOIN dim_ticker t ON f.ticker_key = t.ticker_key
    JOIN dim_date   d ON f.date_key   = d.date_key
) ranked
WHERE rn = 1
ORDER BY return_pct DESC;