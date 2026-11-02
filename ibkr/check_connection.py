from ibkr.ibkr_data import IBDataFetcher

# Connect to TWS — make sure TWS is open and API is enabled
fetcher = IBDataFetcher(port=7496)
fetcher.connect()

# Fetch 1 year of daily SPY data
df = fetcher.get_data(ticker="SPY", duration="1 Y", bar_size="1 day")
print(df.head())

fetcher.disconnect()