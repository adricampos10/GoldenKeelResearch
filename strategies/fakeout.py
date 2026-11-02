import pandas as pd

from strategies.base import Strategy

class FakeoutStrategy(Strategy):
    columns = ['High', 'Low', 'min_N', 'max_N', 'bull_fakeout', 'bear_fakeout']

    def __init__(self, window=252, trade_shorts=False):
        super().__init__()
        self.window       = window
        self.trade_shorts = trade_shorts

    def _compute(self, df: pd.DataFrame) -> None:
        df['min_N'] = df['Low'].shift(1).rolling(self.window).min()
        df['max_N'] = df['High'].shift(1).rolling(self.window).max()

        df['bull_fakeout'] = (df['Low'] < df['min_N']) & (df['Close'] > df['min_N'])
        df['bear_fakeout'] = (df['High'] > df['max_N']) & (df['Close'] < df['max_N'])

        # Señal como estado: 1 = largo, -1 = corto, 0 = fuera
        # Bull fakeout -> largo. Bear fakeout -> corto si trade_shorts, si no, salir a liquidez
        exit_state = -1 if self.trade_shorts else 0
        state      = 0
        signal     = []

        for bull, bear in zip(df['bull_fakeout'], df['bear_fakeout']):
            if bull:
                state = 1
            elif bear and state != exit_state:
                state = exit_state
            signal.append(state)

        df['signal'] = signal
