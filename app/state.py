import streamlit as st

def initialize_session_state():
    if 'stock_data' not in st.session_state:
        st.session_state['stock_data'] = {}
    if 'results' not in st.session_state:
        st.session_state['results'] = {}

