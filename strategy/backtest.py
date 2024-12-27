import numpy as np
import pandas as pd
from strategy.indicators import calculate_indicators
from strategy.signals import generate_signals
from data.fetch import fetch_stock_data


def calculate_risk_metrics(returns):
    """
    Calculates advanced risk metrics for given returns.
    """
    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else np.nan
    downside_deviation = np.sqrt(np.mean(np.minimum(0, returns) ** 2)) * np.sqrt(252)
    sortino_ratio = returns.mean() / downside_deviation if downside_deviation > 0 else np.nan
    max_drawdown = (returns.cumsum().cummax() - returns.cumsum()).max()
    skewness = returns.skew()
    tail_risk = (returns < -0.05).mean()

    return sharpe_ratio, sortino_ratio, max_drawdown, skewness, tail_risk

def backtest(data, initial_balance=10000):
    """
    Backtests a single stock's data.
    Returns risk metrics and performance data.
    """
    if data.empty:
        return [], initial_balance, pd.DataFrame(), None, None, None, None, None

    # Validate input data
    if data.isna().any().any():
        print("Warning: Input data contains NaN values. Dropping NaN rows.")
        data.dropna(inplace=True)

    balance = initial_balance
    positions = 0.0
    balance_history = []
    trades = []
    returns = []

    for i in range(1, len(data)):
        current_price = data['Close'].iloc[i]
        signal = data['Signal'].iloc[i]
        trade_date = data.index[i]

        if signal == 1:  # Buy signal
            if balance > 0:
                shares_bought = balance / current_price
                trades.append({'Date': trade_date, 'Type': 'Buy', 'Price': current_price, 'Shares': shares_bought})
                positions += shares_bought
                balance = 0
        elif signal == -1:  # Sell signal
            if positions > 0:
                trades.append({'Date': trade_date, 'Type': 'Sell', 'Price': current_price, 'Shares': positions})
                balance += positions * current_price
                positions = 0

        portfolio_value = balance + positions * current_price
        balance_history.append(portfolio_value)

        if i > 1:
            returns.append((portfolio_value - balance_history[i - 2]) / balance_history[i - 2])

    # Final portfolio value calculation
    final_value = balance + positions * data['Close'].iloc[-1] if not data.empty else balance
    trades_df = pd.DataFrame(trades)

    # Risk metrics calculations
    returns_series = pd.Series(returns)
    sharpe_ratio, sortino_ratio, max_drawdown, skewness, tail_risk = calculate_risk_metrics(returns_series)

    return balance_history, final_value, trades_df, sharpe_ratio, sortino_ratio, max_drawdown, skewness, tail_risk


def split_data(stock_data, split_date):
    """
    Splits the stock data into training and testing datasets based on the split date.
    """
    training_data = stock_data[stock_data.index < split_date]
    testing_data = stock_data[stock_data.index >= split_date]
    return training_data, testing_data

def backtest_with_split(data, split_date, initial_balance=10000):
    """
    Backtests a stock's data with a split into training and testing datasets.
    Returns performance data for both periods.
    """
    training_data, testing_data = split_data(data, split_date)

    if training_data.empty or testing_data.empty:
        return {
            "Training_Period": {
                "History": [],
                "Final_Balance": initial_balance
            },
            "Testing_Period": {
                "History": [],
                "Final_Balance": initial_balance
            }
        }

    train_history, train_final_value, _ = backtest(training_data, initial_balance)
    test_history, test_final_value, _ = backtest(testing_data, train_final_value)

    return {
        "Training_Period": {
            "History": train_history,
            "Final_Balance": train_final_value
        },
        "Testing_Period": {
            "History": test_history,
            "Final_Balance": test_final_value
        }
    }

from strategy.indicators import calculate_indicators

def robust_backtesting_for_ticker(ticker, asset_data, ma_short, ma_long, momentum_period, portfolio_value):
    """Backtests a single ticker robustly."""
    try:
        # Debug: Check column names before standardization
        print(f"Before Standardization - Ticker: {ticker}, Columns: {asset_data.columns}")
        
        # Standardize columns by removing ticker-specific suffix
        asset_data.columns = [col.split('_')[0] for col in asset_data.columns]
        
        # Debug: Check column names after standardization
        print(f"After Standardization - Ticker: {ticker}, Columns: {asset_data.columns}")

        # Calculate indicators
        asset_data = calculate_indicators(asset_data, ma_short, ma_long, momentum_period)

        # Generate signals and backtest
        asset_data = generate_signals(asset_data, ma_short, ma_long)
        balance_history, final_value, trades_df, sharpe_ratio, sortino_ratio, max_drawdown, skewness, tail_risk = backtest(
            asset_data, initial_balance=portfolio_value
        )
        return {
            'Ticker': ticker,
            'Final_Balance': final_value,
            'Trades': trades_df,
            'Performance_History': balance_history,
            'Sharpe_Ratio': sharpe_ratio,
            'Sortino_Ratio': sortino_ratio,
            'Max_Drawdown': max_drawdown,
            'Skewness': skewness,
            'Tail_Risk': tail_risk,
        }
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None



def robust_backtesting(asset_universe, start_date, end_date, ma_short, ma_long, momentum_period, portfolio_value):
    """
    Robust backtesting for multiple tickers.
    """
    results = []

    for asset_class, tickers in asset_universe.items():
        stock_data = fetch_stock_data(tickers, start_date, end_date)
        for ticker, data in stock_data.items():
            if not data.empty:
                print(f"Ticker: {ticker}, Columns: {data.columns}")

                result = robust_backtesting_for_ticker(
                    ticker,
                    data,
                    ma_short,
                    ma_long,
                    momentum_period,
                    portfolio_value
                )
                if result is not None:
                    results.append(result)

    return results
