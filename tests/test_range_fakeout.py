"""Unit tests for RangeFakeoutStrategy on hand-built price paths."""
import numpy as np
import pandas as pd
import pytest

from conftest import make_prices
from strategies.range_fakeout import RangeFakeoutStrategy


def path(*points):
    """Closes moving one point per bar through the given levels."""
    closes = [points[0]]
    for target in points[1:]:
        steps = max(1, int(round(abs(target - closes[-1]))))
        closes += list(np.linspace(closes[-1], target, steps + 1)[1:])
    return closes


def prices(closes):
    closes = np.asarray(closes, dtype=float)
    return make_prices(closes, high=closes + 0.5, low=closes - 0.5)


# Six swings between 101 and 119 (lows 100.5, highs 119.5 with the 0.5 wicks)
RANGE = list(110 + 9 * np.sin(np.arange(300) * 2 * np.pi / 50))
# Below the range to 97, back to 104, a second bottom at 97.5, then up to the ceiling
FAKEOUT = RANGE + path(RANGE[-1], 97, 104, 97.5, 106, 120)
NECKLINE = 104.5    # high of the 104 close between the two bottoms
BREAKDOWN = RANGE + path(RANGE[-1], 85, 87, 80)


def test_double_bottom_below_the_range_goes_long_on_the_neckline_break():
    strategy = RangeFakeoutStrategy().fit(prices(FAKEOUT))
    [trade] = strategy.trades
    closes = np.asarray(FAKEOUT)

    assert trade['side'] == 1
    assert trade['support'] == pytest.approx(100.5, abs=0.1)
    assert closes[trade['entry_bar']] > NECKLINE >= closes[trade['entry_bar'] - 1]
    assert trade['stop'] < 96.5                                     # below the lower bottom
    assert trade['target'] == pytest.approx(119.5 - 0.15 * 19, abs=0.1)


def test_the_long_is_held_until_the_target():
    strategy = RangeFakeoutStrategy().fit(prices(FAKEOUT))
    [trade] = strategy.trades
    signal = strategy.get_signals()['signal']

    assert (signal.iloc[trade['entry_bar']:trade['exit_bar']] == 1).all()
    assert (signal.iloc[trade['exit_bar']:] == 0).all()
    assert prices(FAKEOUT)['High'].iloc[trade['exit_bar']] >= trade['target']


def test_a_real_breakdown_is_not_traded():
    strategy = RangeFakeoutStrategy().fit(prices(BREAKDOWN))
    assert strategy.trades == []
    assert 'too deep' in [event['event'] for event in strategy.events]


def test_a_downtrend_is_not_a_range():
    closes = list(np.linspace(150, 100, 300) + 3 * np.sin(np.arange(300) * 2 * np.pi / 50))
    closes += path(closes[-1], 95, 99, 95.5, 104)
    assert RangeFakeoutStrategy().fit(prices(closes)).trades == []


def test_the_mirror_image_goes_short_only_when_allowed():
    mirrored = list(220 - np.asarray(FAKEOUT))

    assert RangeFakeoutStrategy().fit(prices(mirrored)).trades == []
    [trade] = RangeFakeoutStrategy(trade_shorts=True).fit(prices(mirrored)).trades
    assert trade['side'] == -1
    assert trade['support'] == pytest.approx(220 - 100.5, abs=0.1)


def engulfing_prices():
    df = prices(RANGE + path(RANGE[-1], 102))
    bars = pd.DataFrame(
        {'Open': [102.0, 99.8], 'High': [102.3, 103.3], 'Low': [99.5, 98.0], 'Close': [100.0, 103.0]},
        index=pd.date_range(df.index[-1] + pd.Timedelta(days=1), periods=2),
    )
    return pd.concat([df, bars])


def test_candle_trigger_buys_a_bullish_engulfing_that_closes_back_in_the_range():
    df = engulfing_prices()
    [trade] = RangeFakeoutStrategy(trigger='candle').fit(df).trades
    assert trade['entry_bar'] == len(df) - 1


def test_structure_trigger_waits_for_a_base():
    assert RangeFakeoutStrategy(trigger='structure').fit(engulfing_prices()).trades == []


def test_a_young_range_is_ignored():
    # The same fakeout with only 100 bars of range before it
    closes = FAKEOUT[200:]
    assert RangeFakeoutStrategy(min_range_bars=150).fit(prices(closes)).trades == []
    assert len(RangeFakeoutStrategy(min_range_bars=80).fit(prices(closes)).trades) == 1


def test_min_reward_risk_filters_the_trade():
    # Reward to the target is about 11.7 for about 8.8 of risk
    assert len(RangeFakeoutStrategy(min_reward_risk=1.2).fit(prices(FAKEOUT)).trades) == 1
    strategy = RangeFakeoutStrategy(min_reward_risk=2).fit(prices(FAKEOUT))
    assert strategy.trades == []
    assert 'filtered' in [event['event'] for event in strategy.events]


def test_unknown_trigger_raises():
    with pytest.raises(ValueError, match="trigger"):
        RangeFakeoutStrategy(trigger='magic')
