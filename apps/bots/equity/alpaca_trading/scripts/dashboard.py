import streamlit as st
import alpaca_trade_api as tradeapi
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Alpaca API
try:
    api = tradeapi.REST(
        os.getenv('APCA_API_KEY_ID'),
        os.getenv('APCA_API_SECRET_KEY'),
        os.getenv('APCA_API_BASE_URL'),
        api_version='v2'
    )
except Exception as e:
    st.error(f"Failed to initialize Alpaca API: {e}")
    st.stop()

# Page config
st.set_page_config(
    page_title="Alpaca Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for user inputs
st.sidebar.header("Trading Parameters")
symbol = st.sidebar.text_input("Stock Symbol", value="AAPL")
short_window = st.sidebar.slider("Short MA Window", 1, 20, 5)
long_window = st.sidebar.slider("Long MA Window", 10, 100, 20)

# Main dashboard
def display_account_info():
    st.header("Account Information")
    try:
        account = api.get_account()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Account Status", account.status)
            st.metric("Buying Power", f"${float(account.buying_power):,.2f}")
        with col2:
            st.metric("Equity", f"${float(account.equity):,.2f}")
            st.metric("Cash", f"${float(account.cash):,.2f}")
        with col3:
            st.metric("Portfolio Value", f"${float(account.portfolio_value):,.2f}")
            st.metric("Day's P/L", f"${float(account.equity_change):,.2f}")
            
    except Exception as e:
        st.error(f"Error fetching account info: {e}")

def display_positions():
    st.header("Current Positions")
    try:
        positions = api.list_positions()
        if positions:
            df = pd.DataFrame([{
                "Symbol": p.symbol,
                "Qty": float(p.qty),
                "Avg. Price": f"${float(p.avg_entry_price):.2f}",
                "Market Price": f"${float(p.current_price):.2f}",
                "Market Value": f"${float(p.market_value):,.2f}",
                "Unrealized P/L": f"${float(p.unrealized_pl):,.2f}",
                "P/L %": f"{float(p.unrealized_plpc) * 100:.2f}%"
            } for p in positions])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No open positions")
    except Exception as e:
        st.error(f"Error fetching positions: {e}")

def display_price_chart():
    st.header(f"{symbol} Price Chart")
    try:
        # Get historical data
        bars = api.get_bars(
            symbol,
            tradeapi.TimeFrame.Day,
            limit=long_window * 2  # Get enough data for the long window
        ).df
        
        # Calculate moving averages
        bars['ma_short'] = bars['close'].rolling(window=short_window).mean()
        bars['ma_long'] = bars['close'].rolling(window=long_window).mean()
        
        # Create the chart
        fig = go.Figure()
        
        # Add candlestick
        fig.add_trace(go.Candlestick(
            x=bars.index,
            open=bars['open'],
            high=bars['high'],
            low=bars['low'],
            close=bars['close'],
            name='Price'
        ))
        
        # Add moving averages
        fig.add_trace(go.Scatter(
            x=bars.index,
            y=bars['ma_short'],
            name=f'MA {short_window}',
            line=dict(color='blue', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=bars.index,
            y=bars['ma_long'],
            name=f'MA {long_window}',
            line=dict(color='orange', width=1)
        ))
        
        # Update layout
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Price ($)',
            template='plotly_dark',
            showlegend=True,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error fetching chart data: {e}")

# Display the dashboard
def main():
    st.title("Alpaca Trading Dashboard")
    
    # Display account info
    display_account_info()
    
    # Display positions
    display_positions()
    
    # Display price chart
    display_price_chart()

if __name__ == "__main__":
    main()
