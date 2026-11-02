from data import get_data
from strategies.moving_average_crossover import MovingAverageStrategy
from strategies.fakeout import FakeoutStrategy
from strategies.ema_crossover import EMAStrategy
from strategies.range_fakeout import RangeFakeoutStrategy
from backtester import backtest
from metrics import Metrics
from datetime import datetime

import matplotlib.pyplot as plt
import os


def main():
    # 1. Get data
    data = get_data()

    # 2. Apply strategies
    df_ma      = MovingAverageStrategy(short_window=50, long_window=200).fit(data).get_signals()
    df_fakeout = FakeoutStrategy(window=252, trade_shorts=False).fit(data).get_signals()
    df_ema     = EMAStrategy(short_window=50, long_window=200).fit(data).get_signals()
    range_fakeout = RangeFakeoutStrategy(max_below_sma=0.15, macd_filter="divergence").fit(data)
    df_range   = range_fakeout.get_signals()

    # DEBUG fakeout
    print("Bull fakeouts:", df_fakeout['bull_fakeout'].sum())
    print("Bear fakeouts:", df_fakeout['bear_fakeout'].sum())
    print(df_fakeout[df_fakeout['position'] != 0][['Close', 'min_N', 'max_N', 'signal']].head(10))

    # DEBUG range fakeout
    print("\nRange fakeout trades:", len(range_fakeout.trades))
    for trade in range_fakeout.trades:
        print(trade['entry_date'].date(), trade['exit_date'].date(), round(trade['entry'], 2),
              'stop', round(trade['stop'], 2), 'target', round(trade['target'], 2))

    # DEBUG MA
    print("\nMA signals:")
    print(df_ma['signal'].value_counts())
    print(df_ma[['Close', 'ma_short', 'ma_long', 'signal']].dropna().head(10))

    # 3. Backtest
    result_ma      = backtest(df_ma)
    result_fakeout = backtest(df_fakeout)
    result_ema     = backtest(df_ema)
    result_range   = backtest(df_range)

    # 4. Metrics
    metrics = {
        "Moving Average": Metrics.compute(result_ma),
        "Fakeout":        Metrics.compute(result_fakeout),
        "EMA":            Metrics.compute(result_ema),
        "Range Fakeout":  Metrics.compute(result_range),
    }

    for name, values in metrics.items():
        print(f"\n=== {name} Strategy ===")
        for k, v in values.items():
            print(f"{k}: {v:.2f}")

    # 5. Benchmark
    result_ma['benchmark'] = result_ma['Close'] / result_ma['Close'].iloc[0] * 10000

    # 6. Plot

    os.makedirs("results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Metrics table (Markdown) for the CI summary
    with open("results/metrics.md", "w") as f:
        f.write(Metrics.to_markdown(metrics) + "\n")

    curves = {
        "MA Strategy":      result_ma['equity'],
        "Fakeout Strategy": result_fakeout['equity'],
        "EMA Strategy":     result_ema['equity'],
        "Range Fakeout":    result_range['equity'],
        "Buy & Hold (SPY)": result_ma['benchmark'],
    }

    fig, (ax_eq, ax_dd) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1]}
    )

    for name, equity in curves.items():
        style    = '--' if name.startswith("Buy & Hold") else '-'
        drawdown = equity / equity.cummax() - 1

        ax_eq.plot(equity,   label=name, linestyle=style)
        ax_dd.plot(drawdown, label=name, linestyle=style)

    ax_eq.set_yscale('log')
    ax_eq.set_title("Strategy Comparison vs Benchmark (log scale)")
    ax_eq.set_ylabel("Equity ($)")
    ax_eq.legend()
    ax_eq.grid(True, which='both', alpha=0.3)

    ax_dd.set_title("Drawdown")
    ax_dd.set_ylabel("Drawdown")
    ax_dd.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax_dd.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"results/equity_curve_{timestamp}.png")
    plt.show()


if __name__ == "__main__":
    main()
