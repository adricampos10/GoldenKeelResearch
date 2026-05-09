from ib_insync import IB, Stock
import pandas as pd

class IBDataFetcher:
    def __init__(self, host='127.0.0.1', port=7496, client_id=1):
        self.host      = host
        self.port      = port
        self.client_id = client_id
        self.ib        = IB()

    def connect(self):
        self.ib.connect(self.host, self.port, clientId=self.client_id)
        print("Connected to IB ✅")

    def disconnect(self):
        self.ib.disconnect()
        print("Disconnected from IB")

    def get_data(self, ticker="SPY", duration="1 Y", bar_size="1 day") -> pd.DataFrame:
        contract = Stock(ticker, 'SMART', 'USD')

        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow='TRADES',
            useRTH=True
        )

        if not bars:
            raise RuntimeError(f"No data retrieved for {ticker}")

        df = pd.DataFrame(bars)[['date', 'open', 'high', 'low', 'close', 'volume']]
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = df.set_index('Date')
        df.index = pd.to_datetime(df.index)

        print(f"{ticker} — {len(df)} rows retrieved")
        return df