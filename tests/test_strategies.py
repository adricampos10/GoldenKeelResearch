"""Unit tests for the strategies in strategies/."""
import pytest

from conftest import make_prices
from strategies.base import Strategy
from strategies.ema_crossover import EMAStrategy
from strategies.fakeout import FakeoutStrategy
from strategies.macd_crossover import MACDStrategy
from strategies.moving_average_crossover import MovingAverageStrategy
from strategies.range_fakeout import RangeFakeoutStrategy

ALL_STRATEGIES = [
    MovingAverageStrategy(short_window=5, long_window=20),
    EMAStrategy(short_window=5, long_window=20),
    MACDStrategy(fast=5, slow=12, signal_window=4),
    FakeoutStrategy(window=20),
    FakeoutStrategy(window=20, trade_shorts=True),
    RangeFakeoutStrategy(trade_shorts=True),
]


class FixedSignal(Strategy):
    """Strategy with a given signal, to test the base class on its own."""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def _compute(self, df):
        df["signal"] = self.signal


# --- common interface ----------------------------------------------------------

@pytest.mark.parametrize("strategy", ALL_STRATEGIES, ids=lambda s: type(s).__name__)
def test_signals_respect_the_backtester_contract(strategy, random_walk):
    signals = strategy.fit(random_walk).get_signals()

    assert {"Close", "signal", "position"} <= set(signals.columns)
    assert signals.index.equals(random_walk.index)
    assert set(signals["signal"].unique()) <= {-1, 0, 1}


@pytest.mark.parametrize("strategy", ALL_STRATEGIES, ids=lambda s: type(s).__name__)
def test_fit_does_not_modify_the_input(strategy, random_walk):
    columns = list(random_walk.columns)
    strategy.fit(random_walk)
    assert list(random_walk.columns) == columns


def test_results_before_fit_raise():
    with pytest.raises(RuntimeError, match="fit"):
        MovingAverageStrategy().get_signals()


# --- entries and exits ---------------------------------------------------------

SIGNAL = [0, 1, 1, 0, -1, -1, 1]


def test_entries_are_the_bars_where_a_position_opens():
    fitted = FixedSignal(SIGNAL).fit(make_prices(range(1, 8)))
    assert [fitted.df.index.get_loc(i) for i in fitted.get_entries().index] == [1, 4, 6]


def test_exits_are_the_bars_where_a_position_closes():
    fitted = FixedSignal(SIGNAL).fit(make_prices(range(1, 8)))
    assert [fitted.df.index.get_loc(i) for i in fitted.get_exits().index] == [3, 6]


# --- crossovers ----------------------------------------------------------------

UP_THEN_DOWN = list(range(1, 21)) + list(range(19, 0, -1))


@pytest.mark.parametrize("strategy", [
    MovingAverageStrategy(short_window=2, long_window=4),
    EMAStrategy(short_window=2, long_window=4),
], ids=["MA", "EMA"])
def test_crossover_goes_long_in_the_uptrend_and_short_in_the_downtrend(strategy):
    signal = strategy.fit(make_prices(UP_THEN_DOWN)).get_signals()["signal"].tolist()

    assert signal[:4] == [0, 0, 0, 0]   # warm-up
    assert signal[10] == 1
    assert signal[-1] == -1


def test_macd_warm_up_lasts_slow_bars():
    signal = MACDStrategy(fast=2, slow=5, signal_window=2).fit(make_prices(UP_THEN_DOWN))
    assert signal.get_signals()["signal"].tolist()[:5] == [0] * 5


# --- fakeout -------------------------------------------------------------------

# Bar 3 breaks below the 3-bar low and closes back inside (bull fakeout);
# bar 5 breaks above the 3-bar high and closes back inside (bear fakeout).
FAKEOUT_PRICES = make_prices(
    closes=[10, 10, 10, 10, 10, 10, 10],
    high=[11, 11, 11, 11, 11, 12, 11],
    low=[9, 9, 9, 8, 9, 9, 9],
)


def test_fakeout_holds_the_long_until_a_bear_fakeout():
    signals = FakeoutStrategy(window=3).fit(FAKEOUT_PRICES).get_signals()
    assert signals["signal"].tolist() == [0, 0, 0, 1, 1, 0, 0]


def test_fakeout_goes_short_on_a_bear_fakeout_when_allowed():
    signals = FakeoutStrategy(window=3, trade_shorts=True).fit(FAKEOUT_PRICES).get_signals()
    assert signals["signal"].tolist() == [0, 0, 0, 1, 1, -1, -1]
