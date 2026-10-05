import logging
import sys
import time

from extract import extract_prices, extract_ticker_info
from transform import transform_prices, build_dim_date
from load import get_engine, load_dim_ticker, load_dim_date, load_fact_prices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("pipeline")


def run():
    start = time.time()
    log.info("Pipeline pornit")

    # EXTRACT
    raw_prices = extract_prices()
    tickers = extract_ticker_info()
    log.info(f"Extract: {len(raw_prices)} randuri de preturi, {len(tickers)} actiuni")

    # TRANSFORM
    prices = transform_prices(raw_prices)
    dim_date = build_dim_date(prices)
    log.info(f"Transform: {len(prices)} randuri curate, {len(dim_date)} zile")

    # LOAD
    engine = get_engine()
    load_dim_ticker(engine, tickers)
    load_dim_date(engine, dim_date)
    load_fact_prices(engine, prices)

    log.info(f"Pipeline terminat cu succes in {time.time() - start:.1f} secunde")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        log.exception("Pipeline esuat")
        sys.exit(1)