import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def get_engine():
    """Creeaza conexiunea la PostgreSQL folosind datele din .env."""
    url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)


def to_records(df: pd.DataFrame) -> list[dict]:
    """Transforma DataFrame-ul in liste de dictionare cu tipuri Python simple (NaN -> None)."""
    records = df.to_dict(orient="records")
    clean = []
    for row in records:
        new_row = {}
        for key, value in row.items():
            if pd.isna(value):
                value = None
            elif hasattr(value, "item"):  # numpy int/float -> int/float Python
                value = value.item()
            new_row[key] = value
        clean.append(new_row)
    return clean


def load_dim_ticker(engine, tickers: pd.DataFrame):
    sql = text("""
        INSERT INTO dim_ticker (symbol, company_name, sector)
        VALUES (:symbol, :company_name, :sector)
        ON CONFLICT (symbol) DO UPDATE
        SET company_name = EXCLUDED.company_name,
            sector       = EXCLUDED.sector
    """)
    with engine.begin() as conn:
        conn.execute(sql, to_records(tickers))
    print(f"[load] dim_ticker: {len(tickers)} randuri")


def load_dim_date(engine, dim_date: pd.DataFrame):
    sql = text("""
        INSERT INTO dim_date (date_key, full_date, year, month, day, day_of_week)
        VALUES (:date_key, :full_date, :year, :month, :day, :day_of_week)
        ON CONFLICT (date_key) DO NOTHING
    """)
    with engine.begin() as conn:
        conn.execute(sql, to_records(dim_date))
    print(f"[load] dim_date: {len(dim_date)} randuri")


def load_fact_prices(engine, prices: pd.DataFrame):
    # Aflam ticker_key pentru fiecare simbol din dim_ticker
    keys = pd.read_sql("SELECT ticker_key, symbol FROM dim_ticker", engine)
    df = prices.merge(keys, on="symbol", how="inner")

    cols = ["ticker_key", "date_key", "open", "high", "low", "close",
            "volume", "daily_return", "ma_7d"]
    sql = text("""
        INSERT INTO fact_daily_prices
            (ticker_key, date_key, open, high, low, close, volume, daily_return, ma_7d)
        VALUES
            (:ticker_key, :date_key, :open, :high, :low, :close, :volume, :daily_return, :ma_7d)
        ON CONFLICT (ticker_key, date_key) DO UPDATE
        SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
            close = EXCLUDED.close, volume = EXCLUDED.volume,
            daily_return = EXCLUDED.daily_return, ma_7d = EXCLUDED.ma_7d
    """)
    with engine.begin() as conn:
        conn.execute(sql, to_records(df[cols]))
    print(f"[load] fact_daily_prices: {len(df)} randuri")


if __name__ == "__main__":
    from extract import extract_prices, extract_ticker_info
    from transform import transform_prices, build_dim_date

    engine = get_engine()
    clean = transform_prices(extract_prices())

    load_dim_ticker(engine, extract_ticker_info())
    load_dim_date(engine, build_dim_date(clean))
    load_fact_prices(engine, clean)