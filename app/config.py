import streamlit as st

API_KEY = "AKCK3NP8EFWM9GMJ97VY"
SECRET_KEY = "DEAv5T0IxryY2I77WgyT13wVXjnx0dYRxcCfKtUG"
BASE_URL = "https://api.alpaca.markets"


def setup_config():
    st.set_page_config(page_title="Momentum Trading Dashboard", layout="wide")
    if 'stock_data' not in st.session_state:
        st.session_state['stock_data'] = {}
    if 'results' not in st.session_state:
        st.session_state['results'] = {}

