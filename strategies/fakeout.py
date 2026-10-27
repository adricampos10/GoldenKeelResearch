import pandas as pd

class FakeoutStrategy:
    def __init__(self, window=252, trade_shorts=False):
        self.window       = window
        self.trade_shorts = trade_shorts
        self.df           = None

    def fit(self, data: pd.DataFrame) -> "FakeoutStrategy":
        self.df = data.copy()

        self.df['min_N'] = self.df['Low'].shift(1).rolling(self.window).min()
        self.df['max_N'] = self.df['High'].shift(1).rolling(self.window).max()

        self.df['bull_fakeout'] = (self.df['Low'] < self.df['min_N']) & (self.df['Close'] > self.df['min_N'])
        self.df['bear_fakeout'] = (self.df['High'] > self.df['max_N']) & (self.df['Close'] < self.df['max_N'])

        # Señal como estado: 1 = largo, -1 = corto, 0 = fuera
        # Bull fakeout -> largo. Bear fakeout -> corto si trade_shorts, si no, salir a liquidez
        exit_state = -1 if self.trade_shorts else 0
        state      = 0
        signal     = []

        for bull, bear in zip(self.df['bull_fakeout'], self.df['bear_fakeout']):
            if bull:
                state = 1
            elif bear and state != exit_state:
                state = exit_state
            signal.append(state)

        self.df['signal']   = signal
        self.df['position'] = self.df['signal'].diff().fillna(0)

        return self

    def get_signals(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[['Close', 'High', 'Low', 'min_N', 'max_N',
                        'bull_fakeout', 'bear_fakeout', 'signal', 'position']]

    def get_entries(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[self.df['signal'] != 0]

    def get_exits(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[self.df['position'] == 0]

    def _check_fitted(self):
        if self.df is None:
            raise RuntimeError("Call fit(data) before accessing results.")
