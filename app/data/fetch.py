import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO

import alpaca_trade_api as tradeapi
from config import API_KEY, SECRET_KEY, BASE_URL

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

from alpaca_trade_api.rest import TimeFrame

def fetch_stock_data(tickers, start_date, end_date, max_stocks=10):
    """
    Fetch historical stock data for a list of tickers from Alpaca.
    Stops fetching after finding max_stocks tradable and active stocks.
    Filters out warrants and other unsupported instruments.
    """
    stock_data = {}
    count = 0  # Counter for valid stocks

    for ticker in tickers:
#        if count >= max_stocks:
#            print(f"Reached the limit of {max_stocks} stocks. Stopping early.")
#            break

        try:
            # Validate the ticker
            asset = api.get_asset(ticker)
            if not asset.tradable or asset.status != "active":
                print(f"Skipping unsupported or inactive ticker: {ticker}")
                continue

            # Exclude warrants explicitly
            if '.ws' in ticker.lower():
                print(f"Skipping warrant: {ticker}")
                continue

            # Fetch data from Alpaca
            bars = api.get_bars(ticker, TimeFrame.Day, start=start_date, end=end_date).df
            if bars.empty:
                print(f"No data returned for ticker: {ticker}")
                continue

            print(f"Bars for ticker {ticker}: {bars}")
            bars.index = pd.to_datetime(bars.index)  # Ensure proper datetime indexing
            stock_data[ticker] = bars[['open', 'high', 'low', 'close', 'volume']]
            count += 1  # Increment the valid stock counter

        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    return stock_data





def get_sp500_tickers():
    """
    Retrieve the list of S&P 500 tickers. Replace Wikipedia-based logic.
    """
    try:
        # Replace with Alpaca's supported tickers
        assets = api.list_assets(status='active')
        sp500_tickers = [asset.symbol for asset in assets if asset.exchange == 'NYSE']
        return sp500_tickers
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return []

#
#def get_sp500_tickers():
#    """
#    Retrieves the list of S&P 500 tickers from Wikipedia.
#    Returns:
#        list: A list of S&P 500 ticker symbols.
#    """
#    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
#    try:
#        response = requests.get(url, timeout=10000)  # Set timeout to prevent indefinite hangs
#        response.raise_for_status()  # Raise HTTPError for bad responses
#        soup = BeautifulSoup(response.text, 'html.parser')
#        table = soup.find('table', {'id': 'constituents'})
#        tickers = pd.read_html(StringIO(str(table)))[0]['Symbol'].tolist()
#        return tickers
#    except requests.RequestException as e:
#        print(f"Error fetching S&P 500 tickers: {e}")
#        return []
#
#def fetch_stock_data(tickers, start_date, end_date):
#    """Fetch stock data for a list of tickers using yfinance."""
#    data = {}
#    for ticker in tickers:
#        try:
#            stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
#            if not stock_data.empty:
#                stock_data['Daily_Return'] = stock_data['Close'].pct_change()
#                if isinstance(stock_data.columns, pd.MultiIndex):
#                    stock_data.columns = ['_'.join(filter(None, col)).strip() for col in stock_data.columns]
#                data[ticker] = stock_data
#            else:
#                print(f"No data fetched for {ticker}")
#        except Exception as e:
#            print(f"Error fetching data for {ticker}: {e}")
#    return data
