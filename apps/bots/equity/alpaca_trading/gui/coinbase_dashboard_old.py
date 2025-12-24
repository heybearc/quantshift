"""Coinbase Trading Bot Dashboard for Streamlit.

Visual interface for tracking Coinbase bidirectional trading bot.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
import json
from pathlib import Path
from streamlit_autorefresh import st_autorefresh
import requests

logger = logging.getLogger(__name__)

# Coinbase bot state file path
COINBASE_STATE_FILE = Path("/opt/coinbase-trading-bot/data/trader_state.json")


def get_live_price(symbol: str) -> float:
    """Get live price from Coinbase API."""
    try:
        product_id = symbol.replace("/", "-")
        url = f"https://api.coinbase.com/v2/prices/{product_id}/spot"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("data", {}).get("amount", 0))
    except Exception as e:
        logger.error(f"Error getting live price for {symbol}: {e}")
    return 0.0


def calculate_position_metrics(position: Dict, current_price: float) -> Dict:
    """Calculate real-time metrics for a position."""
    side = position.get('side', 'long')
    entry_price = position.get('entry_price', 0)
    qty = position.get('qty', 0)
    stop_loss = position.get('stop_loss', 0)
    take_profit = position.get('take_profit', 0)
    
    if side == 'long':
        unrealized_pnl = (current_price - entry_price) * qty
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        distance_to_sl = ((current_price - stop_loss) / current_price * 100) if current_price > 0 else 0
        distance_to_tp = ((take_profit - current_price) / current_price * 100) if current_price > 0 else 0
    else:  # short
        unrealized_pnl = (entry_price - current_price) * qty
        pnl_pct = ((entry_price - current_price) / entry_price * 100) if entry_price > 0 else 0
        distance_to_sl = ((stop_loss - current_price) / current_price * 100) if current_price > 0 else 0
        distance_to_tp = ((current_price - take_profit) / current_price * 100) if current_price > 0 else 0
    
    # Calculate time in position
    entry_time = position.get('entry_time', '')
    if entry_time:
        try:
            entry_dt = datetime.fromisoformat(entry_time)
            time_in_position = datetime.now() - entry_dt
            hours = time_in_position.total_seconds() / 3600
            time_str = f"{int(hours)}h {int((hours % 1) * 60)}m"
        except:
            time_str = "N/A"
    else:
        time_str = "N/A"
    
    return {
        'unrealized_pnl': unrealized_pnl,
        'pnl_pct': pnl_pct,
        'distance_to_sl': distance_to_sl,
        'distance_to_tp': distance_to_tp,
        'time_in_position': time_str
    }


def show_coinbase_dashboard():
    """Main Coinbase dashboard page."""
    st.header("🔄 Coinbase Trading Bot")
    st.caption("Bidirectional Trading (Long + Short)")
    
    # Auto-refresh settings
    if "auto_refresh_enabled" not in st.session_state:
        st.session_state.auto_refresh_enabled = True
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 15
    
    # Sidebar settings
    with st.sidebar:
        st.subheader("⚙️ Dashboard Settings")
        
        interval_options = [10, 15, 30, 60]
        interval_labels = {10: "10 seconds", 15: "15 seconds", 30: "30 seconds", 60: "1 minute"}
        
        refresh_interval = st.selectbox(
            "Refresh interval", 
            interval_options, 
            index=interval_options.index(st.session_state.refresh_interval) if st.session_state.refresh_interval in interval_options else 1,
            format_func=lambda x: interval_labels.get(x, f"{x} seconds")
        )
        st.session_state.refresh_interval = refresh_interval
        
        auto_refresh = st.checkbox("Enable auto-refresh", value=st.session_state.auto_refresh_enabled)
        st.session_state.auto_refresh_enabled = auto_refresh
        
        if auto_refresh:
            count = st_autorefresh(interval=refresh_interval * 1000, limit=None, key="coinbase_autorefresh")
            st.caption(f"✅ Auto-refreshing every {interval_labels.get(refresh_interval, str(refresh_interval) + ' seconds')}")
        
        st.divider()
        
        st.subheader("📝 Trading Mode")
        st.info("🎮 **Sandbox Mode** - Paper trading with mock funds")
    
    # Load bot state
    if not COINBASE_STATE_FILE.exists():
        st.warning("⚠️ Coinbase bot not started yet")
        st.info("Set up Coinbase API keys to enable the bot")
        return
    
    try:
        with open(COINBASE_STATE_FILE) as f:
            bot_state = json.load(f)
    except Exception as e:
        st.error(f"Error loading bot state: {e}")
        return
    
    # Summary metrics
    balance = bot_state.get("current_balance", 0)
    starting_capital = bot_state.get("starting_capital", 1000)
    positions = bot_state.get("positions", [])
    trade_history = bot_state.get("trade_history", [])
    
    # Calculate metrics
    total_pnl = balance - starting_capital
    pnl_pct = (total_pnl / starting_capital * 100) if starting_capital > 0 else 0
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Balance", f"${balance:,.2f}", f"${total_pnl:+,.2f}")
    
    with col2:
        st.metric("Return", f"{pnl_pct:+.1f}%", f"${total_pnl:+,.2f}")
    
    with col3:
        st.metric("Open Positions", len(positions))
    
    with col4:
        st.metric("Total Trades", len(trade_history))
    
    st.divider()
    
    # Open Positions
    st.subheader("📊 Open Positions")
    
    if positions:
        position_data = []
        for pos in positions:
            side_emoji = "🟢" if pos.get('side') == 'long' else "🔴"
            position_data.append({
                "Side": f"{side_emoji} {pos.get('side', 'N/A').upper()}",
                "Symbol": pos.get('symbol', 'N/A'),
                "Qty": f"{pos.get('qty', 0):.6f}",
                "Entry": f"${pos.get('entry_price', 0):,.2f}",
                "Stop Loss": f"${pos.get('stop_loss', 0):,.2f}",
                "Take Profit": f"${pos.get('take_profit', 0):,.2f}",
                "Entry Time": pos.get('entry_time', 'N/A')[:19]
            })
        
        df = pd.DataFrame(position_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No open positions")
    
    st.divider()
    
    # Trade History
    st.subheader("📈 Recent Trades")
    
    if trade_history:
        # Show last 20 trades
        recent_trades = trade_history[-20:]
        
        trade_data = []
        for trade in reversed(recent_trades):
            side = trade.get('side', 'long').upper()
            side_emoji = "🟢" if side == "LONG" else "🔴"
            pnl = trade.get('pnl', 0)
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            
            trade_data.append({
                "Time": trade.get('timestamp', 'N/A')[:19],
                "Side": f"{side_emoji} {side}",
                "Symbol": trade.get('symbol', 'N/A'),
                "Qty": f"{trade.get('qty', 0):.6f}",
                "Entry": f"${trade.get('entry_price', 0):,.2f}",
                "Exit": f"${trade.get('exit_price', 0):,.2f}",
                "P&L": f"{pnl_emoji} ${pnl:+,.2f}",
                "P&L %": f"{trade.get('pnl_pct', 0):+.1f}%",
                "Reason": trade.get('reason', 'N/A')
            })
        
        df = pd.DataFrame(trade_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # P&L Chart
        st.subheader("💰 P&L Over Time")
        
        cumulative_pnl = []
        running_total = 0
        for trade in trade_history:
            running_total += trade.get('pnl', 0)
            cumulative_pnl.append({
                'timestamp': trade.get('timestamp', 'N/A')[:19],
                'pnl': running_total
            })
        
        if cumulative_pnl:
            chart_df = pd.DataFrame(cumulative_pnl)
            fig = px.line(chart_df, x='timestamp', y='pnl', 
                         title='Cumulative P&L',
                         labels={'timestamp': 'Time', 'pnl': 'P&L ($)'})
            fig.update_traces(line_color='#00ff00' if running_total >= 0 else '#ff0000')
            st.plotly_chart(fig, use_container_width=True)
        
        # Win rate stats
        st.subheader("📊 Statistics")
        
        wins = sum(1 for t in trade_history if t.get('pnl', 0) > 0)
        losses = sum(1 for t in trade_history if t.get('pnl', 0) < 0)
        total_trades = len(trade_history)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = sum(t.get('pnl', 0) for t in trade_history if t.get('pnl', 0) > 0) / wins if wins > 0 else 0
        avg_loss = sum(t.get('pnl', 0) for t in trade_history if t.get('pnl', 0) < 0) / losses if losses > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with col2:
            st.metric("Wins", wins)
        
        with col3:
            st.metric("Losses", losses)
        
        with col4:
            st.metric("Avg Win", f"${avg_win:,.2f}")
    else:
        st.info("No trades yet")
    
    # Bot status
    st.divider()
    last_update = bot_state.get('last_updated', 'N/A')
    st.caption(f"🟢 Bot Active | Last update: {last_update[:19] if last_update != 'N/A' else 'N/A'}")


def main():
    """Main entry point."""
    st.set_page_config(page_title="Coinbase Trading Bot", page_icon="🔄", layout="wide")
    show_coinbase_dashboard()


if __name__ == "__main__":
    main()
