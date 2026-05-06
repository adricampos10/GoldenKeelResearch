from data import get_data
from strategy import moving_average_strategy
from backtester import backtest
from metrics import Metrics

import matplotlib.pyplot as plt

# 1. Get data
data = get_data()

# 2. Apply strategy
df = moving_average_strategy(data)

# 3. Backtest
df = backtest(df)

result = backtest(df)

# 4. Metrics
metrics = Metrics.compute(df)

print("Performance:")
for k, v in metrics.items():
    print(f"{k}: {v:.2f}")

# Normalizar precio del SPY (para compararlo con equity)
result['benchmark'] = result['Close'] / result['Close'].iloc[0] * 10000

# 5. Plot
plt.figure(figsize=(10,5))

plt.plot(result['equity'], label="Strategy")
plt.plot(result['benchmark'], label="Buy & Hold (SPY)", linestyle='--')

plt.title("Strategy vs Benchmark")
plt.legend()

plt.savefig("equity_curve.png")

plt.show()