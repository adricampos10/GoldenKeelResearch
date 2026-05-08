import pandas as pd

class MovingAverageStrategy:
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window = long_window
        self.df = None

    def fit(self, data: pd.DataFrame) -> "MovingAverageStrategy":
        self.df = data.copy()

        self.df['ma_short'] = self.df['Close'].rolling(window=self.short_window).mean()
        self.df['ma_long'] = self.df['Close'].rolling(window=self.long_window).mean()

        self.df['signal'] = 0
        self.df.loc[self.df.index[self.short_window:], 'signal'] = (
            self.df['ma_short'][self.short_window:] > self.df['ma_long'][self.short_window:]
        ).astype(int)

        self.df['position'] = self.df['signal'].diff().fillna(0)

        return self

    def get_signals(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[['Close', 'ma_short', 'ma_long', 'signal', 'position']]

    def get_entries(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[self.df['position'] == 1]

    def get_exits(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[self.df['position'] == -1]

    def _check_fitted(self):
        if self.df is None:
            raise RuntimeError("Call fit(data) before accessing results.")