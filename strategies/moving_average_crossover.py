import pandas as pd

from strategies.base import Strategy

class MovingAverageStrategy(Strategy):
    columns = ['ma_short', 'ma_long']

    def __init__(self, short_window=50, long_window=200):
        super().__init__()
        self.short_window = short_window
        self.long_window  = long_window

    def _compute(self, df: pd.DataFrame) -> None:
        df['ma_short'] = df['Close'].rolling(window=self.short_window).mean()
        df['ma_long']  = df['Close'].rolling(window=self.long_window).mean()

        # 1 = long, -1 = short, 0 = no signal yet
        df['signal'] = self._crossover_signal(df['ma_short'], df['ma_long'], self.long_window)
