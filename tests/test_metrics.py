"""Unit tests for metrics.py."""
import numpy as np
import pandas as pd
import pytest

from metrics import Metrics


def equity(values):
    return pd.DataFrame({"equity": values},
                        index=pd.date_range("2020-01-01", periods=len(values)))


def test_total_return_and_win_rate():
    m = Metrics.compute(equity([100, 110, 99, 121]))
    assert m["Total Return"] == pytest.approx(0.21)
    assert m["Win Rate"] == pytest.approx(2 / 3)


def test_sharpe_is_annualised_with_252_days():
    values = [100, 101, 100.5, 102, 101, 103]
    returns = pd.Series(values).pct_change().dropna()
    expected = returns.mean() / returns.std() * np.sqrt(252)
    assert Metrics.compute(equity(values))["Sharpe"] == pytest.approx(expected)


def test_max_drawdown_from_the_highest_peak():
    m = Metrics.compute(equity([100, 120, 90, 130, 117]))
    assert m["Max Drawdown"] == pytest.approx(90 / 120 - 1)


def test_max_drawdown_includes_a_drop_from_the_first_day():
    m = Metrics.compute(equity([100, 80, 100]))
    assert m["Max Drawdown"] == pytest.approx(-0.2)


def test_to_markdown_has_one_row_per_strategy():
    table = Metrics.to_markdown({
        "EMA":  {"Total Return": 1.5, "Sharpe": 0.8123, "Max Drawdown": -0.25, "Win Rate": 0.5},
        "Fakeout": {"Total Return": -0.1, "Sharpe": -0.2, "Max Drawdown": -0.4, "Win Rate": 0.45},
    }).splitlines()

    assert table[0] == "| Strategy | Total Return | Sharpe | Max Drawdown | Win Rate |"
    assert len(table) == 4
    assert table[2] == "| EMA | 150.0% | 0.81 | -25.0% | 50.0% |"
