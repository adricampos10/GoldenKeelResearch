import pandas as pd

def moving_average_strategy(data, short_window=50, long_window=200):
    df = data.copy()
    
    df['ma_short'] = df['Close'].rolling(window=short_window).mean()
    df['ma_long'] = df['Close'].rolling(window=long_window).mean()
    
    df['signal'] = 0
    df.loc[df.index[short_window:], 'signal'] = (
    df['ma_short'][short_window:] > df['ma_long'][short_window:]
).astype(int)
    
    df['position'] = df['signal'].diff().fillna(0)
    
    return df