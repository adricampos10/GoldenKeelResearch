"""Unit tests for backtester.py on hand-made price series."""
import pytest

from backtester import backtest
from conftest import with_signal

NO_COSTS = dict(commission=0, slippage=0)


def test_flat_signal_keeps_the_initial_cash():
    result = backtest(with_signal([100, 120, 80, 150], 0))
    assert (result["equity"] == 10000).all()


def test_long_without_costs_follows_the_price_from_the_next_bar():
    # The signal is shifted one bar, so the position is opened at the close of bar 1
    result = backtest(with_signal([100, 50, 75, 100], 1), **NO_COSTS)
    assert result["equity"].tolist() == pytest.approx([10000, 10000, 15000, 20000])


def test_a_signal_cannot_capture_the_move_of_its_own_bar():
    # Going long on the bar of the jump buys at 200: no look-ahead profit
    result = backtest(with_signal([100, 100, 200, 200], [0, 0, 1, 1]), **NO_COSTS)
    assert result["equity"].iloc[-1] == pytest.approx(10000)


def test_round_trip_pays_costs_on_open_and_close():
    commission, slippage = 0.001, 0.0005
    rate = commission + slippage
    result = backtest(with_signal([100, 100, 100], [1, 0, 0]),
                      commission=commission, slippage=slippage)
    assert result["equity"].iloc[-1] == pytest.approx(10000 * (1 - rate) / (1 + rate))
    assert result["equity"].iloc[-1] < 10000


def test_short_profits_when_the_price_falls():
    result = backtest(with_signal([100, 100, 50], -1), **NO_COSTS)
    assert result["equity"].iloc[-1] == pytest.approx(15000)


def test_reversal_closes_the_long_and_opens_a_short():
    # Long from 100 to 200 (x2), then short from 200 to 100 (+50% of 20000)
    result = backtest(with_signal([100, 100, 200, 200, 100], [1, 1, -1, -1, -1]), **NO_COSTS)
    assert result["equity"].iloc[-1] == pytest.approx(30000)


def test_the_input_is_not_modified():
    df = with_signal([100, 110, 120], 1)
    backtest(df)
    assert "equity" not in df.columns
