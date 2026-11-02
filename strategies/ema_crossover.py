import pandas as pd

from strategies.base import Strategy

class EMAStrategy(Strategy):
    columns = ['ema_short', 'ema_long']

    def __init__(self, short_window=50, long_window=200):
        super().__init__()
        self.short_window = short_window
        self.long_window  = long_window

    def _compute(self, df: pd.DataFrame) -> None:
        df['ema_short'] = df['Close'].ewm(span=self.short_window, adjust=False).mean()
        df['ema_long']  = df['Close'].ewm(span=self.long_window,  adjust=False).mean()

        # 1 = long, -1 = short, 0 = no signal yet
        df['signal'] = self._crossover_signal(df['ema_short'], df['ema_long'], self.long_window)
