-- Dimensiune: actiunile urmarite
CREATE TABLE IF NOT EXISTS dim_ticker (
    ticker_key   SERIAL PRIMARY KEY,
    symbol       VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(200),
    sector       VARCHAR(100)
);

-- Dimensiune: calendarul
CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INT PRIMARY KEY,          -- ex: 20261005
    full_date   DATE UNIQUE NOT NULL,
    year        INT NOT NULL,
    month       INT NOT NULL,
    day         INT NOT NULL,
    day_of_week INT NOT NULL              -- 0 = luni ... 6 = duminica
);

-- Fapte: un rand = o actiune intr-o zi
CREATE TABLE IF NOT EXISTS fact_daily_prices (
    ticker_key   INT NOT NULL REFERENCES dim_ticker(ticker_key),
    date_key     INT NOT NULL REFERENCES dim_date(date_key),
    open         NUMERIC(12,4),
    high         NUMERIC(12,4),
    low          NUMERIC(12,4),
    close        NUMERIC(12,4),
    volume       BIGINT,
    daily_return NUMERIC(10,6),
    ma_7d        NUMERIC(12,4),
    PRIMARY KEY (ticker_key, date_key)
);
