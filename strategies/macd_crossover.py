import pandas as pd

from strategies.base import Strategy

class MACDStrategy(Strategy):
    columns = ['macd', 'signal_line']

    def __init__(self, fast=12, slow=26, signal_window=9):
        super().__init__()
        self.fast          = fast
        self.slow          = slow
        self.signal_window = signal_window

    def _compute(self, df: pd.DataFrame) -> None:
        ema_fast = df['Close'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=self.slow, adjust=False).mean()

        df['macd']        = ema_fast - ema_slow
        df['signal_line'] = df['macd'].ewm(span=self.signal_window, adjust=False).mean()

        # 1 = long, -1 = short, 0 = no signal yet
        df['signal'] = self._crossover_signal(df['macd'], df['signal_line'], self.slow)
