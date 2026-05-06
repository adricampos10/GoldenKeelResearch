import yfinance as yf
import pandas as pd

def get_data(ticker="SPY", start="1990-01-01", end="2026-01-01"):
    df = yf.download(ticker, start=start, end=end)

    # FIX CRiTICO: flatten columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[['Open', 'High', 'Low', 'Close']].copy()
    df = df.dropna()

    return df