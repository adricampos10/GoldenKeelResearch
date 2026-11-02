import pandas as pd

class Strategy:
    """
    Common interface for every strategy: fit(data) -> self, then get_signals(),
    get_entries() and get_exits().

    Subclasses implement _compute(df), which adds a 'signal' column (target
    position per bar: 1 = long, -1 = short, 0 = flat) plus any indicator
    columns, and list those indicator columns in `columns`.
    """

    columns = []

    def __init__(self):
        self.df = None

    def fit(self, data: pd.DataFrame) -> "Strategy":
        self.df = data.copy()
        self._compute(self.df)
        self.df['position'] = self.df['signal'].diff().fillna(0)
        return self

    def _compute(self, df: pd.DataFrame) -> None:
        raise NotImplementedError

    def get_signals(self) -> pd.DataFrame:
        self._check_fitted()
        return self.df[['Close'] + self.columns + ['signal', 'position']]

    def get_entries(self) -> pd.DataFrame:
        """Bars where a new position is opened (a reversal counts as an entry)."""
        self._check_fitted()
        signal, previous = self.df['signal'], self._previous_signal()
        return self.df[(signal != 0) & (signal != previous)]

    def get_exits(self) -> pd.DataFrame:
        """Bars where an open position is closed (a reversal counts as an exit)."""
        self._check_fitted()
        signal, previous = self.df['signal'], self._previous_signal()
        return self.df[(previous != 0) & (signal != previous)]

    def _previous_signal(self) -> pd.Series:
        return self.df['signal'].shift(1).fillna(0)

    def _check_fitted(self):
        if self.df is None:
            raise RuntimeError("Call fit(data) before accessing results.")

    @staticmethod
    def _crossover_signal(fast: pd.Series, slow: pd.Series, warmup: int) -> pd.Series:
        """1 while fast > slow, -1 otherwise, 0 during the first `warmup` bars."""
        signal = (fast > slow).map({True: 1, False: -1})
        signal.iloc[:warmup] = 0
        return signal
