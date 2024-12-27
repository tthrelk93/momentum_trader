import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO

def get_sp500_tickers():
    """
    Retrieves the list of S&P 500 tickers from Wikipedia.
    Returns:
        list: A list of S&P 500 ticker symbols.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        response = requests.get(url, timeout=10000)  # Set timeout to prevent indefinite hangs
        response.raise_for_status()  # Raise HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'constituents'})
        tickers = pd.read_html(StringIO(str(table)))[0]['Symbol'].tolist()
        return tickers
    except requests.RequestException as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return []

def fetch_stock_data(tickers, start_date, end_date):
    """Fetch stock data for a list of tickers using yfinance."""
    data = {}
    for ticker in tickers:
        try:
            stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not stock_data.empty:
                stock_data['Daily_Return'] = stock_data['Close'].pct_change()
                if isinstance(stock_data.columns, pd.MultiIndex):
                    stock_data.columns = ['_'.join(filter(None, col)).strip() for col in stock_data.columns]
                data[ticker] = stock_data
            else:
                print(f"No data fetched for {ticker}")
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    return data
