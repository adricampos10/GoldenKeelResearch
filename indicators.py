"""Indicators shared by the strategies."""
import pandas as pd


def macd(close: pd.Series, fast=12, slow=26, signal_window=9):
    """MACD line, signal line and histogram (MACD minus signal)."""
    line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    signal = line.ewm(span=signal_window, adjust=False).mean()
    return line, signal, line - signal
