import pandas as pd

def macd_strategy(data, fast=12, slow=26, signal_window=9):
    df = data.copy()
    
    # EMAs
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    
    # MACD y signal line
    df['macd'] = ema_fast - ema_slow
    df['signal_line'] = df['macd'].ewm(span=signal_window, adjust=False).mean()
    
    # Señal (estado)
    df['signal'] = 0
    df.loc[df.index[slow:], 'signal'] = (
        df['macd'][slow:] > df['signal_line'][slow:]
    ).astype(int)
    
    # Posición (evento de cruce)
    df['position'] = df['signal'].diff().fillna(0)
    
    return df