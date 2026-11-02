"""Unit tests for data.py. yfinance is replaced by a fake, so no network is used."""
import numpy as np
import pandas as pd

import data


def fake_download(ticker, start=None, end=None, **kwargs):
    # yfinance returns (field, ticker) MultiIndex columns, plus extra fields
    columns = pd.MultiIndex.from_product([["Open", "High", "Low", "Close", "Volume"], [ticker]])
    values = [[1, 2, 0.5, 1.5, 100], [np.nan] * 5, [2, 3, 1.5, 2.5, 200]]
    return pd.DataFrame(values, columns=columns,
                        index=pd.date_range("2024-01-01", periods=3))


def test_get_data_returns_flat_ohlc_columns_without_gaps(monkeypatch):
    monkeypatch.setattr(data.yf, "download", fake_download)

    df = data.get_data("SPY")

    assert list(df.columns) == ["Open", "High", "Low", "Close"]
    assert len(df) == 2
    assert not df.isna().any().any()


def test_get_data_defaults_to_the_latest_available_day(monkeypatch):
    calls = {}

    def spy(ticker, start=None, end=None, **kwargs):
        calls["end"] = end
        return fake_download(ticker)

    monkeypatch.setattr(data.yf, "download", spy)
    data.get_data()
    assert calls["end"] is None
