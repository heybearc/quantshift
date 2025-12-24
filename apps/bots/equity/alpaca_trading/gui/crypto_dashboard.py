"""Crypto Trading Dashboard for Streamlit.

Provides a visual interface for monitoring and controlling crypto trading.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Import crypto trading modules
try:
    from alpaca_trading.crypto import CryptoTrader, crypto_config
    from alpaca_trading.crypto.crypto_strategy import RSIStrategy, BollingerStrategy, MomentumStrategy
    CRYPTO_AVAILABLE = True
except ImportError as e:
    CRYPTO_AVAILABLE = False
    IMPORT_ERROR = str(e)

logger = logging.getLogger(__name__)


def show_crypto_dashboard():
    """Main crypto dashboard page."""
    st.header("🪙 Crypto Trading Dashboard")
    
    if not CRYPTO_AVAILABLE:
        st.error(f"Crypto module not available: {IMPORT_ERROR}")
        return
    
    # Initialize trader in session state
    if "crypto_trader" not in st.session_state:
        try:
            st.session_state.crypto_trader = CryptoTrader()
        except Exception as e:
            st.error(f"Failed to initialize crypto trader: {e}")
            return
    
    trader = st.session_state.crypto_trader
    
    # Get status
    try:
        status = trader.get_status()
    except Exception as e:
        st.error(f"Error getting status: {e}")
        return
    
    # Account Overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Portfolio Value", f"${status['account']['portfolio_value']:,.2f}")
    with col2:
        st.metric("Cash", f"${status['account']['cash']:,.2f}")
    with col3:
        st.metric("Buying Power", f"${status['account']['buying_power']:,.2f}")
    with col4:
        st.metric("Open Positions", len(status['positions']))
    
    st.divider()
    
    # Two columns: Prices and Positions
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Live Crypto Prices")
        
        price_data = []
        for symbol in crypto_config.symbols:
            price = trader.get_crypto_price(symbol)
            if price:
                price_data.append({
                    "Symbol": symbol,
                    "Price": f"${price:,.2f}",
                    "Price_raw": price
                })
        
        if price_data:
            df = pd.DataFrame(price_data)
            st.dataframe(
                df[["Symbol", "Price"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No price data available")
    
    with col_right:
        st.subheader("💼 Open Positions")
        
        if status['positions']:
            pos_df = pd.DataFrame(status['positions'])
            pos_df['pnl_display'] = pos_df.apply(
                lambda x: f"${x['pnl']:.2f} ({x['pnl_pct']:.1f}%)", axis=1
            )
            pos_df['entry'] = pos_df['entry_price'].apply(lambda x: f"${x:.2f}")
            pos_df['current'] = pos_df['current_price'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(
                pos_df[['symbol', 'qty', 'entry', 'current', 'pnl_display', 'strategy']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "symbol": "Symbol",
                    "qty": "Quantity",
                    "entry": "Entry",
                    "current": "Current",
                    "pnl_display": "P&L",
                    "strategy": "Strategy"
                }
            )
        else:
            st.info("No open positions")
    
    st.divider()
    
    # Strategy Signals
    st.subheader("🎯 Strategy Signals")
    
    if st.button("🔄 Analyze All Symbols", use_container_width=True):
        with st.spinner("Analyzing..."):
            all_signals = []
            for symbol in crypto_config.symbols:
                signals = trader.analyze_symbol(symbol)
                for sig in signals:
                    if sig.action != "HOLD":
                        all_signals.append({
                            "Symbol": sig.symbol,
                            "Action": sig.action,
                            "Strategy": sig.strategy,
                            "Strength": f"{sig.strength:.0%}",
                            "Reason": sig.reason,
                            "Price": f"${sig.price:.2f}"
                        })
            
            if all_signals:
                st.dataframe(
                    pd.DataFrame(all_signals),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("No actionable signals at this time")
    
    st.divider()
    
    # Configuration
    st.subheader("⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Monitored Symbols:**")
        st.write(", ".join(crypto_config.symbols))
        
        st.write("**Active Strategies:**")
        for s in status['strategies']:
            st.write(f"  • {s}")
    
    with col2:
        st.write("**Risk Parameters:**")
        st.write(f"  • Position Size: ${crypto_config.position_size_usd}")
        st.write(f"  • Max Positions: {crypto_config.max_positions}")
        st.write(f"  • Stop Loss: {crypto_config.stop_loss_pct:.1%}")
        st.write(f"  • Take Profit: {crypto_config.take_profit_pct:.1%}")
        st.write(f"  • Check Interval: {crypto_config.check_interval_minutes} min")
    
    st.divider()
    
    # Manual Trading
    st.subheader("🎮 Manual Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Buy Crypto**")
        buy_symbol = st.selectbox("Symbol to Buy", crypto_config.symbols, key="buy_symbol")
        if st.button("Execute Buy", type="primary", key="buy_btn"):
            with st.spinner("Placing order..."):
                signals = trader.analyze_symbol(buy_symbol)
                order_id = trader.place_buy_order(buy_symbol, signals)
                if order_id:
                    st.success(f"Buy order placed: {order_id}")
                else:
                    st.error("Order failed - check logs")
    
    with col2:
        st.write("**Sell Position**")
        open_symbols = [p['symbol'] for p in status['positions']]
        if open_symbols:
            sell_symbol = st.selectbox("Position to Sell", open_symbols, key="sell_symbol")
            if st.button("Execute Sell", type="secondary", key="sell_btn"):
                with st.spinner("Placing order..."):
                    order_id = trader.place_sell_order(sell_symbol, reason="manual")
                    if order_id:
                        st.success(f"Sell order placed: {order_id}")
                    else:
                        st.error("Order failed - check logs")
        else:
            st.info("No positions to sell")


def show_crypto_chart(trader: 'CryptoTrader', symbol: str):
    """Show price chart for a crypto symbol."""
    bars = trader.get_crypto_bars(symbol, days=7)
    
    if bars.empty:
        st.warning(f"No chart data for {symbol}")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=bars.index,
        open=bars['open'],
        high=bars['high'],
        low=bars['low'],
        close=bars['close'],
        name=symbol
    ))
    
    fig.update_layout(
        title=f"{symbol} - 7 Day Chart",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    st.set_page_config(page_title="Crypto Dashboard", page_icon="🪙", layout="wide")
    show_crypto_dashboard()
