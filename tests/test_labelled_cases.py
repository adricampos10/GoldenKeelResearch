"""RangeFakeoutStrategy against the hand-labelled chart cases in patterns/labels.yaml.

Prices come from tests/data/labels/<id>.csv (saved by `python -m patterns.fetch_label_data`),
so these tests stay offline.
"""
import os

import pandas as pd
import pytest
import yaml

from strategies.range_fakeout import RangeFakeoutStrategy

ROOT = os.path.dirname(os.path.dirname(__file__))
with open(os.path.join(ROOT, "patterns", "labels.yaml")) as f:
    CASES = yaml.safe_load(f)

CANDLE_REVERSALS = {"bullish_engulfing", "hammer_and_confirmation", "rejection_candle"}

# Filters that keep every winning case
FILTERS = dict(max_below_sma=0.15)

# How each failed case is caught: (settings that see the setup, settings that reject it)
CAUGHT_BY = {
    "btc-2022-05-failed-fakeout":    (dict(), dict(FILTERS)),                        # far below a falling 200-day average
    "ndx-2022-01-failed-fakeout":    (dict(min_range_bars=40), dict()),              # range only 2.5 months old
    "gold-2023-12-failed-bull-trap": (dict(), dict(trigger="structure")),            # one candle, no base
}

WINNERS = [c for c in CASES if c.get("outcome") != "failed"]
FAILED  = [c for c in CASES if c.get("outcome") == "failed"]


def load(case):
    return pd.read_csv(os.path.join(ROOT, "tests", "data", "labels", f"{case['id']}.csv"),
                       index_col=0, parse_dates=True)


def trigger_for(case):
    return "candle" if case.get("reversal") in CANDLE_REVERSALS else "structure"


def side_of(case):
    return 1 if case["pattern"] == "range_bull_fakeout" else -1


def holds_labelled_trade(case, **settings):
    """True if the strategy is in the labelled direction from at most 5 bars after the labelled entry."""
    df = load(case)
    params = dict(trigger=trigger_for(case), trade_shorts=True)
    params.update(settings)
    strategy = RangeFakeoutStrategy(**params).fit(df)
    entry = df.index.get_indexer([pd.Timestamp(case["trade"]["entry"]["date"])], method="bfill")[0]
    return any(trade["side"] == side_of(case) and trade["entry_bar"] <= entry + 5 and trade["exit_bar"] > entry
               for trade in strategy.trades)


@pytest.mark.parametrize("case", WINNERS, ids=lambda c: c["id"])
def test_winning_cases_are_traded_with_the_filters_on(case):
    if not isinstance(case["range"]["support"], list):
        pytest.xfail("sloping range floors are not supported yet")
    assert holds_labelled_trade(case, **FILTERS)


@pytest.mark.parametrize("case", FAILED, ids=lambda c: c["id"])
def test_failed_cases_are_seen_and_then_rejected(case):
    assert case["id"] in CAUGHT_BY, "say in CAUGHT_BY which rule should reject this case"
    sees, rejects = CAUGHT_BY[case["id"]]
    assert holds_labelled_trade(case, **sees)
    assert not holds_labelled_trade(case, **rejects)


def test_every_case_has_its_data_file():
    missing = [c["id"] for c in CASES
               if not os.path.exists(os.path.join(ROOT, "tests", "data", "labels", f"{c['id']}.csv"))]
    assert not missing, f"run `python -m patterns.fetch_label_data` for {missing}"
