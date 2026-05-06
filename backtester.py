import pandas as pd

def backtest(data, initial_cash=10000):
    df = data.copy()
    
    cash = initial_cash
    position = 0
    equity_curve = []

    for i in range(len(df)):
        price = df['Close'].iloc[i]
        
        # Buy
        if df['position'].iloc[i] == 1:
            position = cash / price
            cash = 0
        
        # Sell
        elif df['position'].iloc[i] == -1:
            cash = position * price
            position = 0
        
        total_value = cash + position * price
        equity_curve.append(total_value)

    df['equity'] = equity_curve
    return df