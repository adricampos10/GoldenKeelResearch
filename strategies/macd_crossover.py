import pandas as pd

class MACDStrategy:
    def __init__(self, fast=12, slow=26, signal_window=9):
        self.fast          = fast
        self.slow          = slow
        self.signal_window = signal_window
        self.df            = None

    def fit(self, data: pd.DataFrame) -> "MACDStrategy":
        self.df = data.copy()

        ema_fast = self.df['Close'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = self.df['Close'].ewm(span=self.slow, adjust=False).mean()

        self.df['macd']        = ema_fast - ema_slow
        self.df['signal_line'] = self.df['macd'].ewm(span=self.signal_window, adjust=False).mean()

        self.df['signal'] = 0
        self.df.loc[self.df.index[self.slow:], 'signal'] = (
            self.df['macd'][self.slow:] > self.df['signal_line'][self.slow:]
        ).astype(int)

        self.df['position'] = self.df['signal'].diff().fillna(0)

        return self

    def get_signals(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[['Close', 'macd', 'signal_line', 'signal', 'position']]

    def get_entries(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[self.df['position'] == 1]

    def get_exits(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[self.df['position'] == -1]

    def _check_fitted(self):
        if self.df is None:
            raise RuntimeError("Call fit(data) before accessing results.")