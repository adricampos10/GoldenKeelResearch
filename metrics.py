import numpy as np

class Metrics:
    @staticmethod
    def compute(df):
        returns = df['equity'].pct_change().dropna()

        # FIX: asegurar float limpio
        returns = returns.astype(float)

        total_return = df['equity'].iloc[-1] / df['equity'].iloc[0] - 1

        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

        # Drawdown sobre la equity completa, para incluir una caida desde el primer dia
        equity = df['equity'].astype(float)
        drawdown = equity / equity.cummax() - 1

        max_dd = drawdown.min()
        win_rate = (returns > 0).mean()

        return {
            "Total Return": float(total_return),
            "Sharpe": float(sharpe),
            "Max Drawdown": float(max_dd),
            "Win Rate": float(win_rate)
        }

    @staticmethod
    def to_markdown(metrics_by_strategy):
        """Markdown table with one row per strategy, e.g. for the CI job summary."""
        percent = {"Total Return", "Max Drawdown", "Win Rate"}
        names   = list(next(iter(metrics_by_strategy.values())))

        lines = [
            "| Strategy | " + " | ".join(names) + " |",
            "|---|" + "---:|" * len(names),
        ]
        for strategy, metrics in metrics_by_strategy.items():
            cells = [f"{metrics[n]:.1%}" if n in percent else f"{metrics[n]:.2f}" for n in names]
            lines.append(f"| {strategy} | " + " | ".join(cells) + " |")

        return "\n".join(lines)