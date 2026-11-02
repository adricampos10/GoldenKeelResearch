import numpy as np
import pandas as pd

from indicators import macd
from strategies.base import Strategy


class RangeFakeoutStrategy(Strategy):
    """False break of a long sideways range, confirmed by a reversal.

    Bull side (bear side is the mirror image, only with trade_shorts=True):

    1. Range: on the bar where price trades below the lowest low of the last
       `w` bars, that window is a range if both its floor and its ceiling were
       touched at least `min_touches` times (swing lows/highs within `zone` x
       range height of the extremes). The longest valid window wins, from
       `min_range_bars` to `max_range_bars`.
    2. Fakeout: price must not close more than `max_depth` x range height below
       the support, and the reversal must come within `max_base_bars`.
    3. Reversal trigger:
       - "structure": the two latest swing lows of the base (at least one below
         the support, the later one no more than one ATR lower) and a close
         above the highest high between them, back inside the range. Covers
         double/triple bottoms, inverse head and shoulders and messy bases.
       - "candle": a bullish engulfing, or a hammer below the support followed
         by a close above the hammer's high.
    4. Trade: long on the trigger close, stop `stop_atr` ATR below the base
       low, target at the bottom of the resistance zone. The signal is held
       until the stop or the target is touched.

    Optional filters: `max_below_sma` (skip longs this far below the 200-day
    average, shorts this far above it), `min_reward_risk`, and `macd_filter`,
    which holds the entry until the MACD (12/26/9) agrees:
       - "momentum": MACD line above its signal line on the trigger bar.
       - "divergence": MACD higher at the later of the two base lows than at the
         earlier one (bullish divergence when the later low is as low or lower).
       - "slow_trend": slow MACD (60/130/45, about 12/26/9 on weekly bars) above
         its signal line.
    """

    columns = ['support', 'resistance', 'stop', 'target']

    def __init__(self, min_range_bars=80, max_range_bars=756, range_step=10,
                 zone=0.15, min_touches=2, min_height_atr=3.0, max_depth=0.5,
                 max_base_bars=100, trigger="structure", stop_atr=0.25,
                 max_below_sma=None, min_reward_risk=None, trade_shorts=False,
                 macd_filter=None, atr_window=20, pivot=5, base_pivot=2):
        super().__init__()
        if trigger not in ("structure", "candle", "both"):
            raise ValueError("trigger must be 'structure', 'candle' or 'both'")
        if macd_filter not in (None, "momentum", "divergence", "slow_trend"):
            raise ValueError("macd_filter must be None, 'momentum', 'divergence' or 'slow_trend'")
        self.windows         = list(range(min_range_bars, max_range_bars + 1, range_step))[::-1]
        self.zone            = zone
        self.min_touches     = min_touches
        self.min_height_atr  = min_height_atr
        self.max_depth       = max_depth
        self.max_base_bars   = max_base_bars
        self.trigger         = trigger
        self.stop_atr        = stop_atr
        self.max_below_sma   = max_below_sma
        self.min_reward_risk = min_reward_risk
        self.trade_shorts    = trade_shorts
        self.macd_filter     = macd_filter
        self.atr_window      = atr_window
        self.pivot           = pivot
        self.base_pivot      = base_pivot
        self.trades          = []
        self.events          = []

    def _compute(self, df: pd.DataFrame) -> None:
        o, h, l, c = (df[col].to_numpy(dtype=float) for col in ('Open', 'High', 'Low', 'Close'))
        prev_close = np.concatenate(([c[0]], c[:-1]))
        true_range = np.maximum(h, prev_close) - np.minimum(l, prev_close)
        atr = pd.Series(true_range).rolling(self.atr_window).mean().to_numpy()
        sma_gap = c / pd.Series(c).rolling(200).mean().to_numpy() - 1

        # The bear side runs the same rules on prices mirrored around zero
        self.events = []
        trades = self._scan(o, h, l, c, atr, sma_gap, side=1)
        if self.trade_shorts:
            trades += self._scan(-o, -l, -h, -c, atr, -sma_gap, side=-1)

        # One position at a time: a signal on the other side reverses the open trade,
        # one on the same side is ignored
        self.trades = []
        for trade in sorted(trades, key=lambda tr: tr['entry_bar']):
            current = self.trades[-1] if self.trades else None
            if current is not None and trade['entry_bar'] < current['exit_bar']:
                if trade['side'] == current['side']:
                    continue
                current['exit_bar'] = trade['entry_bar']
                current['reversed'] = True
            self.trades.append(trade)

        n = len(df)
        signal = np.zeros(n, dtype=int)
        levels = {col: np.full(n, np.nan) for col in self.columns}
        for trade in self.trades:
            span = slice(trade['entry_bar'], trade['exit_bar'])
            signal[span] = trade['side']
            for col in self.columns:
                levels[col][span] = trade[col]
            trade['entry_date'] = df.index[trade['entry_bar']]
            trade['exit_date'] = df.index[min(trade['exit_bar'], n - 1)]
        for event in self.events:
            event['date'] = df.index[event['bar']]
        self.events.sort(key=lambda event: event['bar'])

        for col in self.columns:
            df[col] = levels[col]
        df['signal'] = signal

    # --- one side of the market ---------------------------------------------------

    def _scan(self, o, h, l, c, atr, sma_gap, side):
        """Bull-side state machine. Returns the trades, prices in real (unmirrored) units."""
        n = len(c)
        lows_min  = {w: pd.Series(l).rolling(w).min().shift(1).to_numpy() for w in self.windows}
        highs_max = {w: pd.Series(h).rolling(w).max().shift(1).to_numpy() for w in self.windows}
        range_lows  = _pivots(l, self.pivot, low=True)
        range_highs = _pivots(h, self.pivot, low=False)
        base_lows   = _pivots(l, self.base_pivot, low=True)
        closes      = pd.Series(c)
        macd_line, macd_signal, _ = (x.to_numpy() for x in macd(closes))
        slow_line, slow_signal, _ = (x.to_numpy() for x in macd(closes, 60, 130, 45))

        trades, setup, position = [], None, None
        for t in range(1, n):
            if position is not None:
                if not (l[t] <= position['stop_px'] or h[t] >= position['target_px']):
                    continue
                # Closed: the same bar may already break a range and start a new setup
                position['exit_bar'] = t
                trades.append(position)
                position = None

            # A new low can break the floor of a bigger range below the current one: switch to it,
            # judging that range on the bars before the first break
            if setup is None or l[t] < l[setup['break_bar']:t].min():
                anchor = t if setup is None else setup['anchor']
                found = self._find_range(t, anchor, h, l, atr, lows_min, highs_max, range_lows, range_highs)
                if found is not None and (setup is None or found['support'] < setup['support']):
                    setup = found
                    self._log(t, side, 'range', support=side * setup['support'],
                              resistance=side * setup['resistance'], bars=setup['window'])
                if setup is None:
                    continue

            support, height = setup['support'], setup['height']
            too_deep = c[t] < support - self.max_depth * height
            too_long = t - setup['break_bar'] > self.max_base_bars
            missed   = c[t] > support + height / 2
            if too_deep or too_long or missed:
                reason = 'too deep' if too_deep else 'too long' if too_long else 'missed'
                self._log(t, side, reason)
                setup = None
                continue

            base_low = l[setup['break_bar']:t + 1].min()
            if not self._triggered(t, o, h, l, c, atr, support, setup['break_bar'], base_lows):
                continue
            # The MACD filter only delays the entry: the setup stays alive until it agrees
            if self.macd_filter == "momentum" and not macd_line[t] > macd_signal[t]:
                continue
            if self.macd_filter == "slow_trend" and not slow_line[t] > slow_signal[t]:
                continue
            if self.macd_filter == "divergence":
                pair = self._base_pair(t, l, atr, support, setup['break_bar'], base_lows)
                if pair is None or not macd_line[pair[1]] > macd_line[pair[0]]:
                    continue

            stop   = base_low - self.stop_atr * atr[t]
            target = setup['resistance'] - self.zone * height
            reward, risk = target - c[t], c[t] - stop
            ok_sma = self.max_below_sma is None or not (sma_gap[t] < -self.max_below_sma)
            ok_rr  = self.min_reward_risk is None or (risk > 0 and reward / risk >= self.min_reward_risk)
            if not (ok_sma and ok_rr and reward > 0):
                self._log(t, side, 'filtered', sma_gap=side * sma_gap[t], reward_risk=reward / risk if risk > 0 else None)
            else:
                position = {
                    'side': side, 'entry_bar': t, 'exit_bar': n,
                    'entry': side * c[t], 'stop': side * stop, 'target': side * target,
                    'support': side * support, 'resistance': side * setup['resistance'],
                    'range_bars': setup['window'], 'stop_px': stop, 'target_px': target,
                }
            setup = None

        if position is not None:
            trades.append(position)
        for trade in trades:
            del trade['stop_px'], trade['target_px']
        return trades

    def _log(self, t, side, kind, **info):
        self.events.append({'bar': t, 'side': side, 'event': kind, **info})

    def _find_range(self, t, anchor, h, l, atr, lows_min, highs_max, range_lows, range_highs):
        """Longest valid range of the `w` bars before `anchor` whose floor bar t breaks, or None."""
        for w in self.windows:                       # longest first
            support, resistance = lows_min[w][anchor], highs_max[w][anchor]
            if np.isnan(support) or not l[t] < support:
                continue
            height = resistance - support
            if height < self.min_height_atr * atr[anchor - 1]:
                continue
            zone  = self.zone * height
            first = anchor - w
            last  = anchor - 1 - self.pivot         # swing points confirmed before the anchor bar
            floor = _touches(range_lows, first, last, lambda i: l[i] <= support + zone, 2 * self.pivot)
            ceiling = _touches(range_highs, first, last, lambda i: h[i] >= resistance - zone, 2 * self.pivot)
            if len(floor) < self.min_touches or len(ceiling) < self.min_touches:
                continue
            # Sideways, not a downtrend: the ceiling is touched again after the floor's first touch
            if ceiling[-1] < floor[0]:
                continue
            return {'support': support, 'resistance': resistance, 'height': height,
                    'window': w, 'break_bar': t, 'anchor': anchor}
        return None

    def _triggered(self, t, o, h, l, c, atr, support, break_bar, base_lows):
        if c[t] <= support:
            return False
        if self.trigger in ("structure", "both") and self._structure(t, h, l, c, atr, support, break_bar, base_lows):
            return True
        if self.trigger in ("candle", "both") and self._candle(t, o, h, l, c, support):
            return True
        return False

    def _base_pair(self, t, l, atr, support, break_bar, base_lows):
        """The two swing lows that shape the base, (earlier, later), or None."""
        # Swing lows of the base, confirmed by bar t; the base may start a few bars before the break
        confirmed = base_lows[(base_lows >= break_bar - 4 * self.pivot) & (base_lows + self.base_pivot <= t)]
        near = [i for i in confirmed if l[i] <= support + atr[t]]
        if len(near) < 2:
            return None
        # Pair the lowest swing low of the base (the head) with the latest one, a higher low.
        # If the head is the latest, pair it with the previous swing low: a double bottom
        # whose second low is slightly lower.
        head = min(near, key=lambda i: l[i])
        if l[head] >= support:
            return None
        if head != near[-1]:
            return head, near[-1]
        if l[near[-2]] > l[head] + atr[t]:
            return None
        return near[-2], head

    def _structure(self, t, h, l, c, atr, support, break_bar, base_lows):
        pair = self._base_pair(t, l, atr, support, break_bar, base_lows)
        if pair is None:
            return False
        a, b = pair
        neckline = h[a + 1:b].max() if b > a + 1 else h[a]
        return c[t] > neckline

    @staticmethod
    def _candle(t, o, h, l, c, support):
        prev_body_low, prev_body_high = min(o[t - 1], c[t - 1]), max(o[t - 1], c[t - 1])
        engulfing = (c[t] > o[t] and o[t] <= prev_body_low and c[t] >= prev_body_high
                     and min(l[t - 1], l[t]) < support)
        hammer = (l[t - 1] < support < c[t - 1]
                  and c[t - 1] - l[t - 1] >= 2 / 3 * (h[t - 1] - l[t - 1])
                  and c[t] > h[t - 1])
        return engulfing or hammer


def _pivots(values, k, low):
    """Indices i where values[i] is the extreme of values[i-k : i+k+1]."""
    window = pd.Series(values).rolling(2 * k + 1, center=True)
    extreme = window.min() if low else window.max()
    return np.flatnonzero(values == extreme.to_numpy())


def _touches(pivots, first, last, near, min_gap):
    """Separate touches: pivots in [first, last] that pass `near`, at least `min_gap` bars apart."""
    touches = []
    for i in pivots[(pivots >= first) & (pivots <= last)]:
        if near(i) and (not touches or i - touches[-1] >= min_gap):
            touches.append(i)
    return touches
