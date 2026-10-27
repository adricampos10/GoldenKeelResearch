import numpy as np
import pandas as pd

def backtest(data, initial_cash=10000, commission=0.0005, slippage=0.0005):
    """
    'signal' es la posicion objetivo: 1 = largo, -1 = corto, 0 = fuera del mercado.
    commission y slippage son fracciones del nocional por operacion (0.0005 = 5 pb).
    """
    df = data.copy()

    # La señal se calcula con el cierre del dia t, asi que se ejecuta en el cierre de t+1
    target    = df['signal'].shift(1).fillna(0)
    cost_rate = commission + slippage

    cash         = initial_cash
    position     = 0
    entry_price  = 0
    equity_curve = []

    for i in range(len(df)):
        price = df['Close'].iloc[i]
        tgt   = target.iloc[i]

        if tgt != np.sign(position):
            # Cerrar la posicion actual
            if position > 0:
                cash = position * price
            elif position < 0:
                cash = cash + (entry_price - price) * abs(position)
            if position != 0:
                cash -= abs(position) * price * cost_rate
            position = 0

            # Abrir la nueva posicion, descontando los costes del tamaño
            if tgt != 0:
                size  = cash / (price * (1 + cost_rate))
                cash -= size * price * cost_rate

                if tgt == 1:
                    position = size
                    cash    -= size * price
                else:
                    # Short: el cash se mantiene como garantia
                    position    = -size
                    entry_price = price

        # Calculate equity
        if position > 0:
            total_value = cash + position * price
        elif position < 0:
            total_value = cash + (entry_price - price) * abs(position)
        else:
            total_value = cash

        equity_curve.append(total_value)

    df['equity'] = equity_curve
    return df
