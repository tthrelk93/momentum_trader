import streamlit as st

def setup_config():
    st.set_page_config(page_title="Momentum Trading Dashboard", layout="wide")
    if 'stock_data' not in st.session_state:
        st.session_state['stock_data'] = {}
    if 'results' not in st.session_state:
        st.session_state['results'] = {}

