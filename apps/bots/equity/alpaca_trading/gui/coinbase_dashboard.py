"""Enhanced Coinbase Trading Bot Dashboard for Streamlit.

Visual interface with real-time position tracking, risk management, and trade alerts.
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
    else:
        unrealized_pnl = (entry_price - current_price) * qty
        pnl_pct = ((entry_price - current_price) / entry_price * 100) if entry_price > 0 else 0
        distance_to_sl = ((stop_loss - current_price) / current_price * 100) if current_price > 0 else 0
        distance_to_tp = ((current_price - take_profit) / current_price * 100) if current_price > 0 else 0
    
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


def show_real_time_positions(positions: List[Dict], balance: float):
    """Show real-time position tracking with live prices."""
    st.subheader("📊 Live Positions")
    
    if not positions:
        st.info("No open positions")
        return
    
    total_unrealized = 0
    position_data = []
    
    for pos in positions:
        symbol = pos.get('symbol', 'N/A')
        current_price = get_live_price(symbol)
        
        if current_price > 0:
            metrics = calculate_position_metrics(pos, current_price)
            total_unrealized += metrics['unrealized_pnl']
            
            side_emoji = "🟢" if pos.get('side') == 'long' else "🔴"
            pnl_emoji = "🟢" if metrics['unrealized_pnl'] >= 0 else "🔴"
            
            # Risk indicator
            if abs(metrics['distance_to_sl']) < 0.5:
                risk_indicator = "🔴 NEAR SL"
            elif abs(metrics['distance_to_tp']) < 0.5:
                risk_indicator = "🟢 NEAR TP"
            else:
                risk_indicator = "⚪ ACTIVE"
            
            position_data.append({
                "Status": risk_indicator,
                "Side": f"{side_emoji} {pos.get('side', 'N/A').upper()}",
                "Symbol": symbol,
                "Current": f"${current_price:,.2f}",
                "Entry": f"${pos.get('entry_price', 0):,.2f}",
                "P&L": f"{pnl_emoji} ${metrics['unrealized_pnl']:+,.2f}",
                "P&L %": f"{metrics['pnl_pct']:+.2f}%",
                "To SL": f"{metrics['distance_to_sl']:+.2f}%",
                "To TP": f"{metrics['distance_to_tp']:+.2f}%",
                "Time": metrics['time_in_position']
            })
    
    if position_data:
        df = pd.DataFrame(position_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Total unrealized P&L
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Unrealized P&L", f"${total_unrealized:+,.2f}")
        with col2:
            unrealized_pct = (total_unrealized / balance * 100) if balance > 0 else 0
            st.metric("Unrealized Return", f"{unrealized_pct:+.2f}%")


def show_risk_management(bot_state: Dict, balance: float, starting_capital: float):
    """Show risk management dashboard."""
    st.subheader("⚠️ Risk Management")
    
    positions = bot_state.get("positions", [])
    daily_loss = bot_state.get("daily_loss", 0)
    
    # Calculate total exposure
    total_exposure = 0
    for pos in positions:
        entry_price = pos.get('entry_price', 0)
        qty = pos.get('qty', 0)
        total_exposure += entry_price * qty
    
    exposure_pct = (total_exposure / balance * 100) if balance > 0 else 0
    
    # Daily loss tracking
    max_daily_loss = starting_capital * 0.03  # 3% max
    daily_loss_pct = (daily_loss / starting_capital * 100) if starting_capital > 0 else 0
    daily_loss_remaining = max_daily_loss - daily_loss
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Portfolio Exposure", f"{exposure_pct:.1f}%", f"${total_exposure:,.2f}")
    
    with col2:
        color = "🔴" if daily_loss_pct > 2 else "🟡" if daily_loss_pct > 1 else "🟢"
        st.metric("Daily Loss", f"{color} {daily_loss_pct:.2f}%", f"${daily_loss:,.2f}")
    
    with col3:
        st.metric("Loss Limit Remaining", f"${daily_loss_remaining:,.2f}")
    
    with col4:
        max_positions = 8
        st.metric("Position Slots", f"{len(positions)}/{max_positions}")
    
    # Risk breakdown
    st.write("**Position Risk Breakdown**")
    
    if positions:
        risk_data = []
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            side = pos.get('side', 'long')
            entry_price = pos.get('entry_price', 0)
            qty = pos.get('qty', 0)
            stop_loss = pos.get('stop_loss', 0)
            
            position_value = entry_price * qty
            
            if side == 'long':
                max_loss = (entry_price - stop_loss) * qty
            else:
                max_loss = (stop_loss - entry_price) * qty
            
            risk_reward = abs((pos.get('take_profit', 0) - entry_price) / (entry_price - stop_loss)) if (entry_price - stop_loss) != 0 else 0
            
            risk_data.append({
                "Symbol": symbol,
                "Side": side.upper(),
                "Position Value": f"${position_value:,.2f}",
                "Max Loss": f"${max_loss:,.2f}",
                "R:R Ratio": f"{risk_reward:.2f}:1"
            })
        
        df = pd.DataFrame(risk_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No positions to analyze")


def show_trade_alerts(trade_history: List[Dict]):
    """Show recent trade activity and alerts."""
    st.subheader("🔔 Trade Activity Feed")
    
    if not trade_history:
        st.info("No recent activity")
        return
    
    # Show last 10 trades
    recent_trades = trade_history[-10:]
    
    for trade in reversed(recent_trades):
        timestamp = trade.get('timestamp', 'N/A')[:19]
        symbol = trade.get('symbol', 'N/A')
        side = trade.get('side', 'long').upper()
        pnl = trade.get('pnl', 0)
        pnl_pct = trade.get('pnl_pct', 0)
        reason = trade.get('reason', 'N/A')
        
        side_emoji = "🟢" if side == "LONG" else "🔴"
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        
        with st.expander(f"{timestamp} - {side_emoji} {side} {symbol} - {pnl_emoji} ${pnl:+,.2f} ({pnl_pct:+.1f}%)"):
            st.write(f"**Exit Reason:** {reason}")
            st.write(f"**Entry:** ${trade.get('entry_price', 0):,.2f}")
            st.write(f"**Exit:** ${trade.get('exit_price', 0):,.2f}")
            st.write(f"**Quantity:** {trade.get('qty', 0):.6f}")


def show_coinbase_dashboard():
    """Main enhanced Coinbase dashboard."""
    st.header("🔄 Coinbase Trading Bot")
    st.caption("Bidirectional Trading (Long + Short) - Enhanced Dashboard")
    
    if "auto_refresh_enabled" not in st.session_state:
        st.session_state.auto_refresh_enabled = True
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 15
    
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
        st.info("🎮 **Sandbox Mode** - Paper trading")
    
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
    
    balance = bot_state.get("current_balance", 0)
    starting_capital = 1000.0
    positions = bot_state.get("positions", [])
    trade_history = bot_state.get("trade_history", [])
    
    total_pnl = balance - starting_capital
    pnl_pct = (total_pnl / starting_capital * 100) if starting_capital > 0 else 0
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Balance", f"${balance:,.2f}", f"${total_pnl:+,.2f}")
    
    with col2:
        st.metric("Return", f"{pnl_pct:+.1f}%")
    
    with col3:
        st.metric("Open Positions", len(positions))
    
    with col4:
        st.metric("Total Trades", len(trade_history))
    
    st.divider()
    
    # Feature 1: Real-time position tracking
    show_real_time_positions(positions, balance)
    
    st.divider()
    
    # Feature 2: Risk management dashboard
    show_risk_management(bot_state, balance, starting_capital)
    
    st.divider()
    
    # Feature 3: Trade alerts feed
    show_trade_alerts(trade_history)
    
    st.divider()
    
    # Bot status
    last_update = bot_state.get('last_updated', 'N/A')
    st.caption(f"🟢 Bot Active | Last update: {last_update[:19] if last_update != 'N/A' else 'N/A'}")


def main():
    """Main entry point."""
    st.set_page_config(page_title="Coinbase Trading Bot", page_icon="🔄", layout="wide")
    show_coinbase_dashboard()


if __name__ == "__main__":
    main()
