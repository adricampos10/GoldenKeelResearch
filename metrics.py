import numpy as np

class Metrics:
    @staticmethod
    def compute(df):
        returns = df['equity'].pct_change().dropna()

        # FIX: asegurar float limpio
        returns = returns.astype(float)

        total_return = df['equity'].iloc[-1] / df['equity'].iloc[0] - 1

        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak

        max_dd = drawdown.min()
        win_rate = (returns > 0).mean()

        return {
            "Total Return": float(total_return),
            "Sharpe": float(sharpe),
            "Max Drawdown": float(max_dd),
            "Win Rate": float(win_rate)
        }