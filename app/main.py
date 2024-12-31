import streamlit as st
import pandas as pd
from config import setup_config
from ui import setup_sidebar
from data.fetch import get_sp500_tickers, fetch_stock_data
from strategy.backtest import robust_backtesting, backtest_with_split, robust_backtesting_for_ticker
from strategy.portfolio import suggest_portfolio
from strategy.signals import generate_live_signals, monitor_and_trade
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from config import API_KEY, SECRET_KEY, BASE_URL

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')


# Initialize Streamlit Configuration
setup_config()

# UI Setup
asset_universe, start_date, end_date, ma_short, ma_long, momentum_period, portfolio_value = setup_sidebar()

#def filter_valid_tickers(tickers):
#    """
#    Filters and returns valid tickers based on Alpaca's tradable assets.
#    """
#    valid_tickers = []
#    for ticker in tickers:
#        try:
#            asset = api.get_asset(ticker)
#            if asset.tradable and 'warrant' not in asset.classification.lower():
#                valid_tickers.append(ticker)
#        except Exception as e:
#            print(f"Error validating ticker {ticker}: {e}")
#    return valid_tickers

def get_last_week_dates():
    """
    Calculate the start and end dates for the previous week.
    Returns:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
    """
    today = datetime.utcnow()
    end_date = today - timedelta(days=today.weekday() + 1)  # Last Sunday
    start_date = end_date - timedelta(days=6)  # Previous Monday
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
        


if st.sidebar.button("Fetch Data and Find Movers"):
    # Calculate last week's dates
    start_date, end_date = get_last_week_dates()

    # Fetch data for valid tickers
    tickers = asset_universe['US_Equities']
    fetched_data = fetch_stock_data(tickers, start_date, end_date)
    st.session_state['stock_data'] = fetched_data

    # Identify top movers based on momentum
    movers = []
    for ticker, data in fetched_data.items():
        if not data.empty:
            # Calculate momentum as percentage change from the start to end of the week
            start_price = data['close'].iloc[0]
            end_price = data['close'].iloc[-1]
            momentum = (end_price - start_price) / start_price
            movers.append({'ticker': ticker, 'momentum': momentum})

    # Sort movers by momentum and take the top 10
    movers = sorted(movers, key=lambda x: x['momentum'], reverse=True)[:10]
    st.session_state['top_movers'] = [m['ticker'] for m in movers]

    st.success("Data fetched and top movers identified!")
    st.write("Top Movers for the Week:", st.session_state['top_movers'])


    

# Run Robust Backtesting
if st.sidebar.button("Run Robust Backtesting"):
    if 'top_movers' not in st.session_state or not st.session_state['top_movers']:
        st.error("Please fetch data and identify top movers first!")
    else:
        st.subheader("Robust Backtesting Results")

        # Filter fetched data to only include the top movers
        top_movers_data = {ticker: st.session_state['stock_data'][ticker] for ticker in st.session_state['top_movers']}

        # Perform backtesting on the top movers
        results = robust_backtesting(
            top_movers_data,  # Use only the data for top movers
            ma_short,
            ma_long,
            momentum_period,
            portfolio_value
        )
        st.session_state['results'] = results  # Save results in session state

        # Display top results by Final Balance
        top_results = sorted(results, key=lambda x: float(x['Final_Balance']), reverse=True)[:10]  # Top 10 movers
        st.subheader("Top 10 Momentum Stocks")
        print(f"Top Results Debug: {top_results}")

        for i, result in enumerate(top_results, start=1):
            try:
                # Display each stock's performance metrics
                final_balance = float(result['Final_Balance'])  # Explicitly cast to float
                sharpe_ratio = float(result['Sharpe_Ratio'])
                sortino_ratio = float(result['Sortino_Ratio'])
                max_drawdown = float(result['Max_Drawdown'])
                skewness = float(result['Skewness'])
                tail_risk = float(result['Tail_Risk'])

                st.write(
                    f"{i}. Ticker: {result['Ticker']} | Final Balance: ${final_balance:,.2f} | "
                    f"Sharpe Ratio: {sharpe_ratio:.2f} | Sortino Ratio: {sortino_ratio:.2f} | "
                    f"Max Drawdown: {max_drawdown:.2%} | Skewness: {skewness:.2f} | "
                    f"Tail Risk: {tail_risk:.2f} "
                )
                st.line_chart(result['Performance_History'])  # Chart performance history

            except (ValueError, TypeError, KeyError) as e:
                print(f"Error processing result: {result}. Error: {e}")
                st.warning(f"Skipping result for ticker {result.get('Ticker', 'Unknown')}: {e}")

        # Display Risk Analysis Summary
        st.subheader("Risk Analysis Summary")
        for result in top_results:
            try:
                risk_report = f"""
                **Ticker:** {result['Ticker']}
                - **Maximum Drawdown:** {float(result['Max_Drawdown']):.2%}
                - **Return Skewness:** {float(result['Skewness']):.2f} (Positive = Right-skewed, Negative = Left-skewed)
                - **Tail Risk:** {float(result['Tail_Risk']):.2f} (Proportion of returns below -5%)
                """
                st.markdown(risk_report)
            except (ValueError, TypeError, KeyError) as e:
                print(f"Error creating risk report for ticker {result.get('Ticker', 'Unknown')}: {e}")
                st.warning(f"Unable to display risk report for ticker {result.get('Ticker', 'Unknown')}: {e}")


# Portfolio Suggestions
if st.sidebar.button("Portfolio Suggestions"):
    if not st.session_state['results']:
        st.warning("Please run backtesting first!")
    else:
        portfolio = suggest_portfolio(st.session_state['results'], portfolio_value)
        st.subheader("Suggested Portfolio Allocation")
        st.dataframe(portfolio)

# Get Recommendations
if st.sidebar.button("Get Recommendations"):
    if not st.session_state['results']:
        st.warning("Please run backtesting first!")
    else:
        st.subheader("Recommended Actions")
        sorted_results = sorted(st.session_state['results'], key=lambda x: x['Final_Balance'], reverse=True)[:5]
        for res in sorted_results:
            st.write(f"Ticker: {res['Ticker']}, Action: {'Buy' if res['Final_Balance'] > portfolio_value else 'Hold'}, Risk Level: Low")

# Run Out-of-Sample Testing
if st.sidebar.button("Run Out-of-Sample Testing"):
    st.subheader("Out-of-Sample Testing Results")
    split_date = st.sidebar.date_input("Split Date", value=pd.to_datetime("2020-01-01"))
    split_date = pd.Timestamp(split_date)  # Ensure split_date is a pandas.Timestamp
    out_of_sample_results = []

    # Check if any data exists before the split_date
    any_data_available = False
    for ticker, stock_data in st.session_state['stock_data'].items():
        if not stock_data.empty and stock_data.index.min() <= split_date:
            any_data_available = True
            break

    if not any_data_available:
        st.error(f"No stock data available before {split_date}. Please fetch historical data or adjust the split date.")
    else:
        for ticker, stock_data in st.session_state['stock_data'].items():
            # Check for empty data or insufficient training data
            if stock_data.empty:
                st.warning(f"No data available for {ticker}. Skipping...")
                continue
            if stock_data.index.min() > split_date:
                st.warning(f"No training data available for {ticker} before {split_date}. Skipping...")
                continue

            # Run backtest with split
            results = backtest_with_split(stock_data, split_date)
            out_of_sample_results.append({
                "Ticker": ticker,
                "Training_Final_Balance": results["Training_Period"]["Final_Balance"],
                "Testing_Final_Balance": results["Testing_Period"]["Final_Balance"]
            })

        # Convert results to a DataFrame for easier handling
        results_df = pd.DataFrame(out_of_sample_results)

        if results_df.empty:
            st.error("No valid data was processed for out-of-sample testing.")
        else:
            # Display overall summary
            st.write("Summary of Out-of-Sample Testing")
            st.bar_chart(results_df.set_index('ticker')[['Training_Final_Balance', 'Testing_Final_Balance']])

            # Display detailed results
            st.write("Detailed Results")
            st.dataframe(results_df)

# Live Signals Button
if st.sidebar.button("Get Live Signals"):
    st.subheader("Live Signals")
    for ticker in st.session_state['stock_data']:
        signal = generate_live_signals(ticker, ma_short,
        ma_long,
        momentum_period)
        st.write(f"Ticker: {ticker}, Signal: {signal}")
        
if st.sidebar.button("Start Live Trading"):
    if 'top_movers' not in st.session_state or not st.session_state['top_movers']:
        st.error("Please fetch data and identify top movers first!")
    else:
        tickers = st.session_state['top_movers']
#        valid_tickers = filter_valid_tickers(tickers)  # Ensure valid tickers
        if not tickers:
            st.error("No valid tickers available for live trading.")
        else:
            st.success(f"Live trading started for: {', '.join(tickers)}")
            monitor_and_trade(tickers, ma_short, ma_long, momentum_period=7)



