import pandas as pd

class MovingAverageStrategy:
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window  = long_window
        self.df           = None

    def fit(self, data: pd.DataFrame) -> "MovingAverageStrategy":
        self.df = data.copy()

        self.df['ma_short'] = self.df['Close'].rolling(window=self.short_window).mean()
        self.df['ma_long']  = self.df['Close'].rolling(window=self.long_window).mean()

        # 1 = long, -1 = short, 0 = no signal yet
        self.df['signal'] = 0
        mask = self.df.index[self.long_window:]
        self.df.loc[mask, 'signal'] = (
            self.df['ma_short'][self.long_window:] > self.df['ma_long'][self.long_window:]
        ).map({True: 1, False: -1})

        self.df['position'] = self.df['signal'].diff().fillna(0)

        return self

    def get_signals(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[['Close', 'ma_short', 'ma_long', 'signal', 'position']]

    def get_entries(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[self.df['signal'] != 0]

    def get_exits(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[self.df['position'] == 0]

    def _check_fitted(self):
        if self.df is None:
            raise RuntimeError("Call fit(data) before accessing results.")