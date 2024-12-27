import numpy as np
from strategy.indicators import calculate_rsi  # Import shared utility

def generate_signals(data, ma_short, ma_long, rsi_period=14, macd_short=12, macd_long=26, macd_signal=9):
    """
    Generates trading signals based on multiple technical indicators.
    """
    # Calculate RSI using the shared function
    data['RSI'] = calculate_rsi(data['Close'], rsi_period)

    # Calculate MACD
    ema_short = data['Close'].ewm(span=macd_short, adjust=False).mean()
    ema_long = data['Close'].ewm(span=macd_long, adjust=False).mean()
    data['MACD'] = ema_short - ema_long
    data['MACD_Signal'] = data['MACD'].ewm(span=macd_signal, adjust=False).mean()

    # Calculate Moving Averages
    data[f'{ma_short}_MA'] = data['Close'].rolling(ma_short).mean()
    data[f'{ma_long}_MA'] = data['Close'].rolling(ma_long).mean()

    # Calculate Momentum
    data['Momentum'] = data['Close'] - data['Close'].shift(ma_short)

    # Replace NaN with 0 for consistency
    data.fillna(0, inplace=True)

    # Signal Logic
    data['Signal'] = 0

    buy_condition = (
        (data[f'{ma_short}_MA'] > data[f'{ma_long}_MA']) &
        (data['Momentum'] > 0) &
        (data['RSI'] < 60) &
        (data['MACD'] > data['MACD_Signal'])
    )
    sell_condition = (
        (data[f'{ma_short}_MA'] < data[f'{ma_long}_MA']) &
        (data['Momentum'] < 0) &
        (data['RSI'] > 40) &
        (data['MACD'] < data['MACD_Signal'])
    )

    data.loc[buy_condition, 'Signal'] = 1
    data.loc[sell_condition, 'Signal'] = -1

    return data


def generate_live_signals(ticker, ma_short, ma_long, momentum_period):
    """
    Generates live trading signals for a given ticker.
    Fetches live data, calculates indicators, and evaluates signals.
    """
    import yfinance as yf

    # Fetch live data
    live_data = yf.download(ticker, period="5d", interval="1h")  # Example: last 5 days, hourly data

    # Generate signals
    live_data = generate_signals(live_data, ma_short, ma_long)

    # Check latest signal
    latest_signal = live_data['Signal'].iloc[-1]
    return "Buy" if latest_signal == 1 else "Sell" if latest_signal == -1 else "Hold"
