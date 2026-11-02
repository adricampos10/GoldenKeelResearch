"""Shared helpers: small synthetic price series, so no test needs the network."""
import numpy as np
import pandas as pd
import pytest


def make_prices(closes, high=None, low=None):
    """OHLC DataFrame with a daily index. High/Low default to Close."""
    index = pd.date_range("2020-01-01", periods=len(closes), freq="D")
    closes = np.asarray(closes, dtype=float)
    return pd.DataFrame({
        "Open":  closes,
        "High":  closes if high is None else np.asarray(high, dtype=float),
        "Low":   closes if low is None else np.asarray(low, dtype=float),
        "Close": closes,
    }, index=index)


def with_signal(closes, signal):
    """Close + signal, the two columns the backtester needs."""
    df = make_prices(closes)[["Close"]]
    df["signal"] = signal
    return df


@pytest.fixture
def random_walk():
    rng = np.random.default_rng(0)
    closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400)))
    return make_prices(closes, high=closes * 1.01, low=closes * 0.99)
