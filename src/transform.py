import pandas as pd


def transform_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Curata preturile si calculeaza coloanele noi."""
    df = prices.copy()

    #1.Curatare
    df = df.dropna(subset=["close"])
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.drop_duplicates(subset=["symbol", "date"])
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    #2.Coloane calculate, separat pentru fiecare actiune
    grouped = df.groupby("symbol")["close"]
    df["daily_return"] = grouped.pct_change()
    df["ma_7d"] = grouped.transform(lambda s: s.rolling(window=7, min_periods=7).mean())

    #3.Cheia pentru dim_date (ex: 20261005)
    df["date_key"] = pd.to_datetime(df["date"]).dt.strftime("%Y%m%d").astype(int)
    df["volume"] = df["volume"].astype("int64")

    return df


def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """Construieste tabelul calendar din datele unice."""
    dates = pd.to_datetime(pd.Series(df["date"].unique())).sort_values()
    return pd.DataFrame({
        "date_key": dates.dt.strftime("%Y%m%d").astype(int),
        "full_date": dates.dt.date,
        "year": dates.dt.year,
        "month": dates.dt.month,
        "day": dates.dt.day,
        "day_of_week": dates.dt.dayofweek,  # 0 = luni
    }).reset_index(drop=True)


if __name__ == "__main__":
    from extract import extract_prices

    raw = extract_prices()
    clean = transform_prices(raw)
    print(clean[["symbol", "date", "close", "daily_return", "ma_7d"]].tail(10))
    print(build_dim_date(clean).head())