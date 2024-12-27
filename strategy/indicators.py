import pandas as pd
import logging
import pandas as pd
import numpy as np

def calculate_indicators(data, ma_short, ma_long, momentum_period):
    """Calculates indicators for the given data."""
    data['Short_MA'] = data['Close'].rolling(window=ma_short).mean()
    data['Long_MA'] = data['Close'].rolling(window=ma_long).mean()
    data['Momentum'] = data['Close'] - data['Close'].shift(momentum_period)
    data['RSI'] = calculate_rsi(data['Close'])
    return data

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index (RSI)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


