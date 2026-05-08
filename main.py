from data import get_data
from strategies.moving_average_crossover import MovingAverageStrategy
from strategies.macd_crossover import MACDStrategy
from backtester import backtest
from metrics import Metrics

import matplotlib.pyplot as plt

# 1. Get data
data = get_data()

# 2. Apply strategies
df_ma = MovingAverageStrategy(short_window=50, long_window=200).fit(data).get_signals()
df_macd = MACDStrategy(fast=12, slow=26, signal_window=9).fit(data).get_signals()

# 3. Backtest
result_ma = backtest(df_ma)
result_macd = backtest(df_macd)

# 4. Metrics
metrics_ma = Metrics.compute(result_ma)
metrics_macd = Metrics.compute(result_macd)

print("\n=== Moving Average Strategy ===")
for k, v in metrics_ma.items():
    print(f"{k}: {v:.2f}")

print("\n=== MACD Strategy ===")
for k, v in metrics_macd.items():
    print(f"{k}: {v:.2f}")

# 5. Benchmark (usar uno de los results)
result_ma['benchmark'] = result_ma['Close'] / result_ma['Close'].iloc[0] * 10000

# 6. Plot
plt.figure(figsize=(10,5))

plt.plot(result_ma['equity'], label="MA Strategy")
plt.plot(result_macd['equity'], label="MACD Strategy")
plt.plot(result_ma['benchmark'], label="Buy & Hold (SPY)", linestyle='--')

plt.title("Strategy Comparison vs Benchmark")
plt.legend()

plt.savefig("equity_curve.png")
plt.show()