import sys
from datetime import datetime, timedelta
from pathlib import Path

import pendulum
from airflow.sdk import dag, task

# Codul pipeline-ului (folderul src/) e montat in container la /opt/airflow/src
sys.path.insert(0, "/opt/airflow/src")

STAGING_DIR = Path("/opt/airflow/data/staging")


@dag(
    dag_id="stock_data_pipeline",
    description="ETL zilnic: Yahoo Finance -> pandas -> PostgreSQL (star schema)",
    schedule="30 23 * * 1-5",  # luni-vineri la 23:30, dupa inchiderea bursei din SUA
    start_date=pendulum.datetime(2026, 10, 1, tz="Europe/Bucharest"),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["etl", "stocks"],
)
def stock_data_pipeline():

    @task
    def extract_prices() -> str:
        from extract import extract_prices as extract

        run_dir = STAGING_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "raw_prices.parquet"
        extract().to_parquet(path, index=False)
        return str(path)

    @task
    def extract_tickers(prices_path: str) -> str:
        from extract import extract_ticker_info

        path = Path(prices_path).parent / "tickers.parquet"
        extract_ticker_info().to_parquet(path, index=False)
        return str(path)

    @task
    def transform(prices_path: str) -> dict:
        import pandas as pd
        from transform import transform_prices, build_dim_date

        run_dir = Path(prices_path).parent
        clean = transform_prices(pd.read_parquet(prices_path))
        clean_path = run_dir / "clean_prices.parquet"
        dim_date_path = run_dir / "dim_date.parquet"
        clean.to_parquet(clean_path, index=False)
        build_dim_date(clean).to_parquet(dim_date_path, index=False)
        return {"prices": str(clean_path), "dim_date": str(dim_date_path)}

    @task
    def load_dimensions(tickers_path: str, paths: dict):
        import pandas as pd
        from load import get_engine, load_dim_ticker, load_dim_date

        engine = get_engine()
        load_dim_ticker(engine, pd.read_parquet(tickers_path))
        load_dim_date(engine, pd.read_parquet(paths["dim_date"]))

    @task
    def load_facts(paths: dict):
        import pandas as pd
        from load import get_engine, load_fact_prices

        load_fact_prices(get_engine(), pd.read_parquet(paths["prices"]))

    prices_path = extract_prices()
    tickers_path = extract_tickers(prices_path)
    paths = transform(prices_path)
    load_dimensions(tickers_path, paths) >> load_facts(paths)


stock_data_pipeline()