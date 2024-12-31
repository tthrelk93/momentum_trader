import numpy as np
from strategy.indicators import calculate_rsi, calculate_ttm_squeeze, calculate_indicators  # Import shared utility
from alpaca_trade_api.rest import REST
from config import API_KEY, SECRET_KEY, BASE_URL  # Use your config file for keys
from alpaca_trade_api.rest import TimeFrame
import pandas as pd

# Initialize Alpaca API
api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')


def generate_signals(data, ma_short, ma_long, rsi_period=14, macd_short=12, macd_long=26, macd_signal=9):
    """
    Generates trading signals based on multiple technical indicators.
    """
    # Calculate RSI using the shared function
    data['rsi'] = calculate_rsi(data['close'], rsi_period)

    # Calculate MACD
    ema_short = data['close'].ewm(span=macd_short, adjust=False).mean()
    ema_long = data['close'].ewm(span=macd_long, adjust=False).mean()
    data['macd'] = ema_short - ema_long
    data['macd_signal'] = data['macd'].ewm(span=macd_signal, adjust=False).mean()

    # Calculate Moving Averages
    data[f'{ma_short}_ma'] = data['close'].rolling(ma_short).mean()
    data[f'{ma_long}_ma'] = data['close'].rolling(ma_long).mean()

    # Replace NaN with 0 for consistency
    data.fillna(0, inplace=True)

    # Trailing Stop-Loss Logic
    data['trailing_stop'] = data['close'] - (2 * data['atr'])  # Trailing stop based on 2x ATR
    trailing_exit_condition = data['close'] < data['trailing_stop']

    # Buy Condition
    buy_condition = (
        (data[f'{ma_short}_ma'] > data[f'{ma_long}_ma']) &
        (data['combined_momentum'] > 0) &
        (data['rsi'] < 80) &
        (data['macd'] > data['macd_signal']) &
        ((data['ttm_squeeze'] == 1) | (data['high_volatility'])) &
        (data['volume_spike'])
    )

    # Sell Condition
    sell_condition = (
        (data[f'{ma_short}_ma'] < data[f'{ma_long}_ma']) &
        ((data['rsi'] > 70) | (data['rsi'] < 30)) &
        (data['macd'] < data['macd_signal']) &
        ((data['volume_spike'] == False) | (data['volatility'] < 0.015))
    )

    # Include Trailing Stop-Loss in Sell Condition
    sell_condition = sell_condition | trailing_exit_condition

    # Signal Logic
    data['signal'] = 0
    data.loc[buy_condition, 'signal'] = 1
    data.loc[sell_condition, 'signal'] = -1

    return data


def fetch_live_data(ticker):
    """
    Fetch live data for a single ticker using Alpaca.
    """
    try:
        bars = api.get_bars(ticker, TimeFrame.Minute, limit=60).df  # Fetch 1-hour data (60 minutes)
        bars.index = pd.to_datetime(bars.index)  # Ensure proper datetime indexing
        return bars[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        print(f"Error fetching live data for {ticker}: {e}")
        return None


def generate_live_signals(data, ma_short, ma_long, momentum_period):
    """
    Generates live trading signals for a given ticker.
    Calculates indicators and evaluates signals.
    Args:
        data (DataFrame): Live stock data for the ticker.
        ma_short (int): Short-term moving average period.
        ma_long (int): Long-term moving average period.
        momentum_period (int): Momentum period.
    Returns:
        str: "Buy", "Sell", or "Hold" signal.
    """
    # Calculate indicators for the live data
    data = calculate_indicators(data, ma_short, ma_long, momentum_period)

    # Generate signals using the live data
    data = generate_signals(data, ma_short, ma_long)
    print(f"data after generate signals: {data}")
    # Check latest signal
    latest_signal = data['signal'].iloc[-1]
    return "Buy" if latest_signal == 1 else "Sell" if latest_signal == -1 else "Hold"
    
def place_order(ticker, qty, side):
    """
    Place a buy or sell order via Alpaca.
    Args:
        ticker (str): The stock ticker symbol.
        qty (int): Number of shares to trade.
        side (str): "buy" or "sell".
    """
    try:
        order = api.submit_order(
            symbol=ticker,
            qty=qty,
            side=side,
            type='market',
            time_in_force='gtc'  # Good-Til-Canceled
        )
        print(f"Order placed: {side} {qty} shares of {ticker}")
    except Exception as e:
        print(f"Error placing order for {ticker}: {e}")

def monitor_and_trade(tickers, ma_short, ma_long, momentum_period=7):
    """
    Continuously monitor live data, generate signals, and execute trades for the top movers.
    Args:
        tickers (list): List of stock tickers to monitor.
        ma_short (int): Short-term moving average period.
        ma_long (int): Long-term moving average period.
        momentum_period (int): Momentum period (default: 7 days).
    """
    import time  # Ensure time is imported
    positions = {}  # Track active positions

    while True:
        for ticker in tickers:
            try:
                # Fetch live data
                live_data = fetch_live_data(ticker)
                print(f"live_data: {live_data}")
                if live_data is None or live_data.empty:
                    continue

                # Generate signals with momentum and indicator calculation
                signal = generate_live_signals(live_data, ma_short, ma_long, momentum_period)

                # Check current position
                current_position = positions.get(ticker, 0)
                print(f"latest signal: {signal}, current_position: {current_position}")

                # Execute buy/sell based on signal
                if signal == "Buy" and current_position == 0:
                    qty = 10  # Example: Buy 10 shares
                    print("placing buy order")
                    place_order(ticker, qty, "buy")
                    positions[ticker] = qty
                elif signal == "Sell" and current_position > 0:
                    print("placing sell order")

                    place_order(ticker, positions[ticker], "sell")
                    positions[ticker] = 0

                # Monitor trailing stop-loss
                trailing_stop = live_data['trailing_stop'].iloc[-1]
                current_price = live_data['close'].iloc[-1]
                print(f"trailing_stop: {trailing_stop}, current_price: {current_price}")
                if current_price < trailing_stop and current_position > 0:
                    print(f"Stop-loss triggered for {ticker}. Selling position.")
                    place_order(ticker, positions[ticker], "sell")
                    positions[ticker] = 0

            except Exception as e:
                print(f"Error monitoring {ticker}: {e}")

        # Sleep before the next iteration
        time.sleep(60)  # Fetch new data every minute
