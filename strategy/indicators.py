import pandas as pd
import logging
import pandas as pd
import numpy as np

# --- Indicators (indicators.py) ---
def calculate_indicators(data, ma_short, ma_long, momentum_period):
    """Calculates indicators for the given data."""
    print("in calc indicators")
    
    # Calculate ATR first
    data['atr'] = calculate_atr(data)
    print(f"ATR Sample: {data['atr'].head()}")

    # Calculate other indicators
    data['short_MA'] = data['close'].rolling(window=ma_short).mean()
    data['long_MA'] = data['close'].rolling(window=ma_long).mean()
    
    # Calculate multiple momentum periods
    data['momentum_10'] = data['close'] - data['close'].shift(10)
    data['momentum_20'] = data['close'] - data['close'].shift(20)
    data['combined_momentum'] = (data['momentum_10'] + data['momentum_20']) / 2

    data['rsi'] = calculate_rsi(data['close'])
    print(f"RSI Sample: {data['rsi'].head()}")

    # Calculate TTM Squeeze after ATR
    data['ttm_squeeze'] = calculate_ttm_squeeze(data)

    # Calculate volatility using standard deviation of returns
    data['volatility'] = data['close'].pct_change().rolling(window=20).std()

    # Mark high-volatility stocks
    min_volatility = 0.02  # Example threshold for 2% daily return volatility
    data['high_volatility'] = data['volatility'] > min_volatility

    # Calculate volume spikes
    volume_mean = data['volume'].rolling(window=20).mean()
    volume_std = data['volume'].rolling(window=20).std()
    data['volume_spike'] = data['volume'] > (volume_mean + 2 * volume_std)

    return data



def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index (RSI)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ttm_squeeze(data):
    """Calculate TTM Squeeze indicator."""
    bollinger_mid = data['close'].rolling(window=20).mean()
    bollinger_std = data['close'].rolling(window=20).std()
    upper_band = bollinger_mid + 2 * bollinger_std
    lower_band = bollinger_mid - 2 * bollinger_std

    keltner_upper = bollinger_mid + 1.5 * data['atr']
    keltner_lower = bollinger_mid - 1.5 * data['atr']

    squeeze = (lower_band > keltner_lower) & (upper_band < keltner_upper)
    print(f"squeeze: {squeeze.astype(int)}")
    return squeeze.astype(int)

def calculate_atr(data, period=14):
    """Calculate Average True Range (ATR)."""
    # Calculate the components of True Range
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())

    # Use Pandas' max function to keep the result as a Series
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    print(f"in calc atr: {true_range}")
    
    # Apply rolling mean
    return true_range.rolling(window=period).mean()



