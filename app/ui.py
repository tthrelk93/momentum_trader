import streamlit as st
from app.data.fetch import get_sp500_tickers
import pandas as pd


def setup_sidebar():
    st.sidebar.header("Configuration")
    start_date = st.sidebar.date_input("Start Date")
    end_date = st.sidebar.date_input("End Date")
    ma_short = st.sidebar.slider("Short Moving Average Period", min_value=5, max_value=50, value=9)
    ma_long = st.sidebar.slider("Long Moving Average Period", min_value=10, max_value=200, value=21)
    momentum_period = st.sidebar.slider("Momentum Period", min_value=5, max_value=50, value=14)
    portfolio_value = st.sidebar.number_input("Portfolio Value", min_value=1000, value=10000)

    # Adjusted asset_universe to include all S&P 500 tickers
    asset_universe = {
        'US_Equities': get_sp500_tickers()  # Include all S&P 500 stocks
    }
    return asset_universe, start_date, end_date, ma_short, ma_long, momentum_period, portfolio_value
