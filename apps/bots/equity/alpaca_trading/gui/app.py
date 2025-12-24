"""Multi-page Trading Dashboard App.

Main entry point for the trading dashboard with navigation between Alpaca and Coinbase bots.
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Navigation in sidebar
with st.sidebar:
    st.title("💰 Trading Dashboard")
    st.divider()
    
    page = st.radio(
        "Select Bot",
        ["Alpaca Bot", "Coinbase Bot"],
        index=0
    )
    
    st.divider()

# Route to appropriate dashboard
if page == "Alpaca Bot":
    from alpaca_trading.gui.challenge_dashboard import show_combined_dashboard
    show_combined_dashboard()
elif page == "Coinbase Bot":
    from alpaca_trading.gui.coinbase_dashboard import show_coinbase_dashboard
    show_coinbase_dashboard()
