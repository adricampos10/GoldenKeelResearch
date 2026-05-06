# Systematic Trading Research Project

This repository contains a Python-based framework for developing and testing systematic trading strategies in financial markets.

## Overview

The project focuses on translating price action and market structure concepts into rule-based, testable trading strategies. It includes a modular backtesting engine with performance evaluation tools.

## Features

- Historical data ingestion (Yahoo Finance)
- Strategy development framework
- Moving average crossover strategy (baseline)
- Backtesting engine with transaction costs
- Performance metrics (Sharpe ratio, drawdown, win rate)
- Benchmark comparison against buy & hold

## Current Focus

Ongoing development is focused on:

- Expanding price action and market structure-based strategies
- Building robust backtesting infrastructure
- Implementing risk management rules
- Developing quantitative tools using Python (NumPy, pandas)

## Tech Stack

- Python
- NumPy
- Pandas
- Matplotlib
- yfinance

## Disclaimer

This project is for educational and research purposes only and does not constitute financial advice.

## Moving Average Crossover Strategy (50 / 200)

This strategy is based on a simple moving average crossover system.

### Logic

- A **buy signal** is generated when the short-term moving average (50-period) crosses **above** the long-term moving average (200-period).
- A **sell signal** is generated when the short-term moving average crosses **below** the long-term moving average.

This strategy aims to capture medium-to-long term trends by following momentum and filtering out short-term market noise.

### Performance

- Total Return: 19.03  
- Sharpe Ratio: 0.74  
- Max Drawdown: -0.34  
- Win Rate: 0.41  


## MACD Crossover Strategy (Frast: 12, Slow: 26, Signal: 9)

This strategy is based on the Moving Average Convergence Divergence (MACD) indicator, which measures momentum using the difference between two exponential moving averages.

### Logic
- A buy signal is generated when the MACD line crosses above the signal line, indicating increasing bullish momentum.
- A sell signal is generated when the MACD line crosses below the signal line, indicating weakening momentum or potential bearish conditions.

This baseline implementation does not include any trend or volatility filters, making it more sensitive to market noise and prone to false signals during sideways market conditions.

### Performance
- Total Return: 2.74
- Sharpe Ratio: 0.42
- Max Drawdown: -0.38
- Win Rate: 0.27


### Equity Curve

![Equity Curve](equity_curve.png)
