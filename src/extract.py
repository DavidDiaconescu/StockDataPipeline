import pandas as pd
import yfinance as yf

TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA"]


def extract_prices(tickers=TICKERS, period="3mo"):
    """Descarca preturile zilnice (OHLCV) pentru fiecare actiune."""
    frames = []
    for symbol in tickers:
        df = yf.Ticker(symbol).history(period=period, auto_adjust=False)
        if df.empty:
            print(f"[extract] Nicio data pentru {symbol}, sar peste")
            continue
        df = df.reset_index()
        df["symbol"] = symbol
        frames.append(df)
        print(f"[extract] {symbol}: {len(df)} randuri")

    prices = pd.concat(frames, ignore_index=True)
    prices = prices.rename(columns={
        "Date": "date", "Open": "open", "High": "high",
        "Low": "low", "Close": "close", "Volume": "volume",
    })
    return prices[["symbol", "date", "open", "high", "low", "close", "volume"]]


def extract_ticker_info(tickers=TICKERS):
    """Ia numele companiei si sectorul pentru dim_ticker."""
    rows = []
    for symbol in tickers:
        try:
            info = yf.Ticker(symbol).info
            rows.append({
                "symbol": symbol,
                "company_name": info.get("longName"),
                "sector": info.get("sector"),
            })
        except Exception as e:
            print(f"[extract] Info indisponibil pentru {symbol}: {e}")
            rows.append({"symbol": symbol, "company_name": None, "sector": None})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    prices = extract_prices()
    print(prices.head())
    print(prices.shape)
    print(extract_ticker_info())