"""Unit tests for indicators.py."""
import numpy as np
import pandas as pd

from indicators import macd


def test_macd_is_the_gap_between_two_emas():
    close = pd.Series(np.linspace(100, 150, 60))
    line, signal, hist = macd(close, fast=3, slow=6, signal_window=2)

    expected = close.ewm(span=3, adjust=False).mean() - close.ewm(span=6, adjust=False).mean()
    assert np.allclose(line, expected)
    assert np.allclose(signal, expected.ewm(span=2, adjust=False).mean())
    assert np.allclose(hist, line - signal)


def test_macd_is_flat_on_constant_prices():
    line, signal, hist = macd(pd.Series([50.0] * 40))
    assert (line == 0).all() and (signal == 0).all() and (hist == 0).all()


def test_macd_is_positive_in_an_uptrend():
    line, _, _ = macd(pd.Series(np.linspace(100, 200, 100)))
    assert line.iloc[-1] > 0
