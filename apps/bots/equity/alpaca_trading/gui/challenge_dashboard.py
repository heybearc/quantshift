"""Trading Challenge Dashboard for Streamlit.

Visual interface for tracking trading challenges:
- Small Account Challenge: $500 to $1,000
- Million Dollar Challenge: $1,000 to $1,000,000
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any
import logging
import json
from pathlib import Path
from streamlit_autorefresh import st_autorefresh

try:
    from alpaca_trading.challenges import SmallAccountChallenge
    CHALLENGE_AVAILABLE = True
except ImportError as e:
    CHALLENGE_AVAILABLE = False
    IMPORT_ERROR = str(e)

try:
    from alpaca_trading.challenges.million_dollar_challenge import MillionDollarChallenge
    MILLION_CHALLENGE_AVAILABLE = True
except ImportError:
    MILLION_CHALLENGE_AVAILABLE = False

try:
    import alpaca_trade_api as tradeapi
    from alpaca_trading.core.config import config
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

logger = logging.getLogger(__name__)


def show_challenge_dashboard():
    """Main challenge dashboard page."""
    st.header("🎯 Small Account Challenge")
    st.caption("Grow your account from $500 to $1,000")
    
    if not CHALLENGE_AVAILABLE:
        st.error(f"Challenge module not available: {IMPORT_ERROR}")
        return
    
    # Sidebar controls
    with st.sidebar:
        st.subheader("⚙️ Challenge Settings")
        
        starting_capital = st.number_input(
            "Starting Capital ($)", 
            min_value=100, 
            max_value=1000, 
            value=500,
            step=100
        )
        
        goal_multiplier = st.selectbox(
            "Goal",
            ["Double (2x)", "Triple (3x)", "Custom"],
            index=0
        )
        
        if goal_multiplier == "Double (2x)":
            goal = starting_capital * 2
        elif goal_multiplier == "Triple (3x)":
            goal = starting_capital * 3
        else:
            goal = st.number_input("Custom Goal ($)", min_value=starting_capital + 100, value=1000)
        
        st.write(f"**Goal:** ${goal:,.0f}")
        
        if st.button("🔄 Reset Challenge", type="secondary"):
            if "challenge" in st.session_state:
                st.session_state.challenge.reset_challenge(starting_capital)
                st.success("Challenge reset!")
                st.rerun()
    
    # Initialize challenge
    if "challenge" not in st.session_state:
        st.session_state.challenge = SmallAccountChallenge(
            starting_capital=starting_capital,
            goal=goal
        )
    
    challenge = st.session_state.challenge
    status = challenge.get_status()
    
    # Progress bar
    progress = status["challenge"]["progress_pct"] / 100
    st.progress(progress, text=f"Progress: {status['challenge']['progress_pct']:.1f}%")
    
    # Goal reached celebration
    if status["challenge"]["goal_reached"]:
        st.balloons()
        st.success("🎉 CONGRATULATIONS! You've reached your goal! 🎉")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta = status["challenge"]["current_balance"] - status["challenge"]["starting_balance"]
        st.metric(
            "Current Balance",
            f"${status['challenge']['current_balance']:,.2f}",
            f"${delta:+,.2f}"
        )
    
    with col2:
        st.metric(
            "Goal",
            f"${status['challenge']['goal']:,.2f}",
            f"${status['challenge']['goal'] - status['challenge']['current_balance']:,.2f} to go"
        )
    
    with col3:
        st.metric(
            "Total P&L",
            f"${status['performance']['total_pnl']:,.2f}",
            f"{status['performance']['total_pnl_pct']:+.1f}%"
        )
    
    with col4:
        st.metric(
            "Win Rate",
            f"{status['trades']['win_rate']:.0f}%",
            f"{status['trades']['total']} trades"
        )
    
    st.divider()
    
    # Two columns: Chart and Stats
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📈 Balance History")
        
        snapshots = challenge.get_daily_snapshots()
        if not snapshots.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=snapshots["date"],
                y=snapshots["balance"],
                mode='lines+markers',
                name='Balance',
                line=dict(color='#00CC96', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 204, 150, 0.1)'
            ))
            
            # Add goal line
            fig.add_hline(
                y=status["challenge"]["goal"],
                line_dash="dash",
                line_color="gold",
                annotation_text=f"Goal: ${status['challenge']['goal']:,.0f}"
            )
            
            # Add starting line
            fig.add_hline(
                y=status["challenge"]["starting_balance"],
                line_dash="dot",
                line_color="gray",
                annotation_text=f"Start: ${status['challenge']['starting_balance']:,.0f}"
            )
            
            fig.update_layout(
                title="Account Growth",
                xaxis_title="Date",
                yaxis_title="Balance ($)",
                height=350,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No history yet. Start trading to see your progress!")
    
    with col_right:
        st.subheader("📊 Statistics")
        
        st.write("**Performance**")
        st.write(f"• Peak Balance: ${status['performance']['peak_balance']:,.2f}")
        st.write(f"• Max Drawdown: {status['performance']['max_drawdown_pct']:.1f}%")
        st.write(f"• Days Active: {status['challenge']['days_active']}")
        
        st.write("")
        st.write("**Projections**")
        st.write(f"• Avg Daily Return: {status['projections']['avg_daily_return_pct']:.2f}%")
        if status['projections']['projected_days_to_goal']:
            st.write(f"• Est. Days to Goal: {status['projections']['projected_days_to_goal']}")
        else:
            st.write("• Est. Days to Goal: N/A")
        
        st.write("")
        st.write("**Today**")
        today_color = "green" if status['today']['pnl'] >= 0 else "red"
        st.write(f"• P&L: :{'green' if status['today']['pnl'] >= 0 else 'red'}[${status['today']['pnl']:+,.2f}]")
        st.write(f"• Trades: {status['today']['trades']}")
        st.write(f"• Status: {status['today']['status']}")
    
    st.divider()
    
    # Live Portfolio from Alpaca - SMALL ACCOUNT ONLY
    st.subheader("💰 Small Account Positions")
    
    # Small Account symbols
    small_account_symbols = ["BTCUSD", "BTC/USD", "SOLUSD", "SOL/USD", "DOGEUSD", "DOGE/USD"]
    
    if ALPACA_AVAILABLE:
        try:
            api = tradeapi.REST(config.api_key, config.api_secret, config.base_url)
            positions = api.list_positions()
            
            # Filter to only Small Account symbols
            small_positions = [p for p in positions if p.symbol in small_account_symbols]
            
            # Calculate totals for Small Account only
            total_cost = sum(float(p.cost_basis) for p in small_positions) if small_positions else 0
            total_unrealized_pl = sum(float(p.unrealized_pl) for p in small_positions) if small_positions else 0
            total_unrealized_pl_pct = (total_unrealized_pl / total_cost * 100) if total_cost > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Invested", f"${total_cost:,.2f}")
            with col2:
                st.metric("Unrealized P&L", f"${total_unrealized_pl:+,.2f}", f"{total_unrealized_pl_pct:+.2f}%")
            with col3:
                st.metric("Positions", len(small_positions))
            
            st.write("")
            
            # Open Positions Table - Small Account Only
            if small_positions:
                st.write("**Open Positions (BTC, SOL, DOGE)**")
                pos_data = []
                for p in small_positions:
                    entry_price = float(p.avg_entry_price)
                    current_price = float(p.current_price)
                    qty = float(p.qty)
                    cost_basis = float(p.cost_basis)
                    unrealized_pl = float(p.unrealized_pl)
                    unrealized_pl_pct = float(p.unrealized_plpc) * 100
                    
                    pos_data.append({
                        "Symbol": p.symbol,
                        "Qty": f"{qty:.6f}" if qty < 1 else f"{qty:.2f}",
                        "Entry": f"${entry_price:,.2f}",
                        "Current": f"${current_price:,.2f}",
                        "P&L": f"${unrealized_pl:+,.2f}",
                        "P&L %": f"{unrealized_pl_pct:+.2f}%"
                    })
                
                st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)
            else:
                st.info("No Small Account positions open")
                
        except Exception as e:
            st.error(f"Could not connect to Alpaca: {e}")
    else:
        st.warning("Alpaca API not available")
    
    st.divider()
    
    # Bot State (Stop Loss / Take Profit targets)
    st.subheader("🤖 Bot Trading Targets")
    
    try:
        bot_state_file = Path("data/autonomous_bot_state.json")
        if bot_state_file.exists():
            with open(bot_state_file) as f:
                bot_state = json.load(f)
            
            bot_positions = bot_state.get("positions", {})
            if bot_positions:
                target_data = []
                for symbol, pos in bot_positions.items():
                    target_data.append({
                        "Symbol": symbol,
                        "Side": pos.get("side", "").upper(),
                        "Entry": f"${pos.get('entry_price', 0):,.2f}",
                        "Stop Loss": f"${pos.get('stop_loss', 0):,.2f}",
                        "Take Profit": f"${pos.get('take_profit', 0):,.2f}",
                        "Entry Time": pos.get("entry_time", "")[:16].replace("T", " ")
                    })
                st.dataframe(pd.DataFrame(target_data), use_container_width=True, hide_index=True)
                st.caption(f"Bot state updated: {bot_state.get('last_update', 'N/A')[:19].replace('T', ' ')}")
            else:
                st.info("No bot positions tracked")
        else:
            st.info("Autonomous bot state file not found")
    except Exception as e:
        st.warning(f"Could not load bot state: {e}")
    
    st.divider()
    
    # Trade History
    st.subheader("📋 Recent Trades")
    
    trades = challenge.get_trade_history(limit=10)
    if trades:
        df = pd.DataFrame(trades)
        # Convert UTC to EST for display
        df['time'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC').dt.tz_convert('America/New_York').dt.strftime('%m/%d %I:%M %p')
        df['pnl_display'] = df.apply(
            lambda x: f"${x['pnl']:+.2f} ({x['pnl_pct']:+.1f}%)", axis=1
        )
        df['trade'] = df.apply(
            lambda x: f"{x['side'].upper()} {x['qty']} @ ${x['price']:.2f}", axis=1
        )
        
        st.dataframe(
            df[['time', 'symbol', 'trade', 'pnl_display', 'strategy']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "time": "Time",
                "symbol": "Symbol",
                "trade": "Trade",
                "pnl_display": "P&L",
                "strategy": "Strategy"
            }
        )
    else:
        st.info("No trades recorded yet. Start trading to build your history!")
    
    st.divider()
    
    # Position Sizing Calculator
    st.subheader("🧮 Position Size Calculator")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        calc_price = st.number_input("Stock/Crypto Price ($)", min_value=0.01, value=25.0)
    
    with col2:
        position_size = challenge.calculate_position_size(calc_price)
        position_value = position_size * calc_price
        st.metric("Suggested Shares/Units", f"{position_size:.2f}")
    
    with col3:
        st.metric("Position Value", f"${position_value:.2f}")
    
    st.caption(f"Based on {status['config']['position_size_pct']:.0f}% position sizing with ${status['challenge']['current_balance']:,.2f} balance")
    
    # Risk/Reward display
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        stop_price = calc_price * (1 - status['config']['stop_loss_pct'] / 100)
        st.write(f"🛑 Stop Loss: ${stop_price:.2f} (-{status['config']['stop_loss_pct']:.1f}%)")
    with col2:
        target_price = calc_price * (1 + status['config']['take_profit_pct'] / 100)
        st.write(f"🎯 Take Profit: ${target_price:.2f} (+{status['config']['take_profit_pct']:.1f}%)")
    with col3:
        risk = position_value * (status['config']['stop_loss_pct'] / 100)
        reward = position_value * (status['config']['take_profit_pct'] / 100)
        st.write(f"⚖️ Risk/Reward: ${risk:.2f} / ${reward:.2f}")


def show_million_dollar_dashboard():
    """Million Dollar Challenge dashboard page."""
    st.header("💰 Million Dollar Challenge")
    st.caption("Grow from $1,000 to $1,000,000 with aggressive swing trading")
    
    if not MILLION_CHALLENGE_AVAILABLE:
        st.error("Million Dollar Challenge module not available")
        return
    
    # Initialize challenge
    if "million_challenge" not in st.session_state:
        st.session_state.million_challenge = MillionDollarChallenge(starting_capital=1000.0)
    
    challenge = st.session_state.million_challenge
    status = challenge.get_status()
    
    # Sidebar
    with st.sidebar:
        st.subheader("⚙️ Challenge Settings")
        st.write(f"**Monthly Contribution:** ${status['contributions']['monthly_amount']:,.0f}")
        st.write(f"**Frequency:** Bi-monthly ($250 x 2)")
        st.write(f"**Next Contribution:** {status['contributions']['next_date']}")
        
        st.divider()
        
        if st.button("💵 Record Contribution ($250)"):
            challenge.add_contribution(250.0)
            st.success("Contribution recorded!")
            st.rerun()
        
        if st.button("🔄 Reset Challenge", type="secondary"):
            st.session_state.million_challenge = MillionDollarChallenge(starting_capital=1000.0)
            st.success("Challenge reset!")
            st.rerun()
    
    # ========== LIVE POSITIONS MONITOR - TOP PRIORITY ==========
    # Get symbols and calculate invested from bot state file FIRST
    million_state_file = Path("data/million_dollar_bot_state.json")
    bot_symbols = set()
    bot_invested = 0.0
    bot_targets = {}  # Store TP/SL targets
    if million_state_file.exists():
        try:
            with open(million_state_file) as f:
                bot_state = json.load(f)
            bot_positions_data = bot_state.get("positions", {})
            bot_symbols = set(bot_positions_data.keys())
            for sym, pos in bot_positions_data.items():
                bot_invested += pos.get("entry_price", 0) * pos.get("qty", 0)
                bot_targets[sym.replace("/", "")] = {
                    "stop_loss": pos.get("stop_loss", 0),
                    "take_profit": pos.get("take_profit", 0),
                    "entry_time": pos.get("entry_time", "")
                }
        except:
            pass
    
    # Get live P&L from Alpaca
    challenge_balance = status["challenge"]["current_balance"]
    available_cash = max(0, challenge_balance - bot_invested)
    total_unrealized_pl = 0.0
    total_unrealized_pl_pct = 0.0
    million_positions = []
    
    if ALPACA_AVAILABLE:
        try:
            api = tradeapi.REST(config.api_key, config.api_secret, config.base_url)
            positions = api.list_positions()
            
            for p in positions:
                symbol_clean = p.symbol.replace("/", "")
                for bot_sym in bot_symbols:
                    if bot_sym.replace("/", "") == symbol_clean:
                        million_positions.append(p)
                        break
            
            total_unrealized_pl = sum(float(p.unrealized_pl) for p in million_positions) if million_positions else 0
            if bot_invested > 0:
                total_unrealized_pl_pct = (total_unrealized_pl / bot_invested) * 100
        except Exception as e:
            st.error(f"Could not connect to Alpaca: {e}")
    
    # ========== COMPACT SUMMARY BAR ==========
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("💰 Balance", f"${challenge_balance:,.2f}")
    with col2:
        st.metric("📈 Invested", f"${bot_invested:,.2f}")
    with col3:
        pnl_color = "normal" if total_unrealized_pl >= 0 else "inverse"
        st.metric("💵 Unrealized", f"${total_unrealized_pl:+,.2f}", f"{total_unrealized_pl_pct:+.2f}%", delta_color=pnl_color)
    with col4:
        st.metric("💳 Cash", f"${available_cash:,.2f}")
    with col5:
        st.metric("📍 Positions", f"{len(bot_symbols)} / 8")
    with col6:
        gains = status['performance']['trading_gains']
        st.metric("📊 Realized", f"${gains:+,.2f}")
    
    # Progress bar (compact)
    progress = status["challenge"]["progress_pct"] / 100
    st.progress(progress, text=f"Progress to $1M: {status['challenge']['progress_pct']:.4f}%")
    
    st.write("")
    
    # ========== POSITION CARDS - MAIN FOCUS ==========
    if million_positions:
        st.write("")
        
        # Sort positions by P&L % (biggest movers first)
        sorted_positions = sorted(million_positions, key=lambda p: abs(float(p.unrealized_plpc)), reverse=True)
        
        # Create position cards in a grid
        for i in range(0, len(sorted_positions), 4):
            cols = st.columns(4)
            for j, col in enumerate(cols):
                if i + j < len(sorted_positions):
                    p = sorted_positions[i + j]
                    pnl = float(p.unrealized_pl)
                    pnl_pct = float(p.unrealized_plpc) * 100
                    current_price = float(p.current_price)
                    entry_price = float(p.avg_entry_price)
                    
                    # Get targets
                    targets = bot_targets.get(p.symbol, {})
                    tp = targets.get("take_profit", entry_price * 1.02)
                    sl = targets.get("stop_loss", entry_price * 0.99)
                    
                    # Calculate progress to TP/SL
                    price_range = tp - sl
                    if price_range > 0:
                        progress_pct = ((current_price - sl) / price_range) * 100
                        progress_pct = max(0, min(100, progress_pct))
                    else:
                        progress_pct = 50
                    
                    # Determine color and status
                    if pnl_pct >= 1.5:
                        bg_color = "#1a472a"  # Dark green - near TP
                        status_emoji = "🚀"
                        status_text = "NEAR TP!"
                    elif pnl_pct >= 0.5:
                        bg_color = "#2d5a3d"  # Green - profitable
                        status_emoji = "📈"
                        status_text = "Profit"
                    elif pnl_pct >= 0:
                        bg_color = "#3d4a3d"  # Slight green
                        status_emoji = "➡️"
                        status_text = "Flat"
                    elif pnl_pct >= -0.5:
                        bg_color = "#4a3d3d"  # Slight red
                        status_emoji = "⚠️"
                        status_text = "Watch"
                    else:
                        bg_color = "#5a2d2d"  # Red - losing
                        status_emoji = "🔻"
                        status_text = "Down"
                    
                    with col:
                        st.markdown(f"""
                        <div style="background: {bg_color}; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 16px; font-weight: bold;">{p.symbol}</span>
                                <span style="font-size: 12px;">{status_emoji} {status_text}</span>
                            </div>
                            <div style="font-size: 20px; font-weight: bold; margin: 8px 0;">
                                ${current_price:,.2f}
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 12px;">
                                <span>Entry: ${entry_price:,.2f}</span>
                                <span style="color: {'#4ade80' if pnl >= 0 else '#f87171'}; font-weight: bold;">
                                    {pnl_pct:+.2f}%
                                </span>
                            </div>
                            <div style="background: #333; height: 6px; border-radius: 3px; margin: 8px 0;">
                                <div style="background: linear-gradient(90deg, #ef4444, #eab308, #22c55e); width: {progress_pct}%; height: 100%; border-radius: 3px;"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888;">
                                <span>SL: ${sl:,.2f}</span>
                                <span>TP: ${tp:,.2f}</span>
                            </div>
                            <div style="text-align: center; margin-top: 6px; font-size: 14px; font-weight: bold; color: {'#4ade80' if pnl >= 0 else '#f87171'};">
                                ${pnl:+,.2f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Detailed table below cards
        with st.expander("📋 Detailed Position Data"):
            pos_data = []
            for p in sorted_positions:
                pnl_pct = float(p.unrealized_plpc) * 100
                targets = bot_targets.get(p.symbol, {})
                
                pos_data.append({
                    "Symbol": p.symbol,
                    "Qty": f"{float(p.qty):.6f}" if float(p.qty) < 1 else f"{float(p.qty):.2f}",
                    "Entry": f"${float(p.avg_entry_price):,.2f}",
                    "Current": f"${float(p.current_price):,.2f}",
                    "Stop Loss": f"${targets.get('stop_loss', 0):,.2f}",
                    "Take Profit": f"${targets.get('take_profit', 0):,.2f}",
                    "P&L": f"${float(p.unrealized_pl):+,.2f}",
                    "P&L %": f"{pnl_pct:+.2f}%"
                })
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)
    else:
        st.info("No positions open - Bot is scanning for opportunities...")
    
    # ========== SECONDARY INFO IN EXPANDERS ==========
    st.write("")
    
    # Momentum Screener (collapsed by default)
    with st.expander("🔍 Momentum Screener - Top Opportunities"):
        screener_file = Path("data/screener_results.json")
        if screener_file.exists():
            try:
                with open(screener_file) as f:
                    screener_data = json.load(f)
                
                last_update = screener_data.get("last_update", "N/A")[:19].replace("T", " ")
                opportunities = screener_data.get("opportunities", [])
                
                st.caption(f"Last scan: {last_update} | Refreshes every 3 min")
                
                if opportunities:
                    opp_data = []
                    for opp in opportunities[:8]:
                        trend_emoji = "📈" if opp["trend"] == "up" else "📉" if opp["trend"] == "down" else "➡️"
                        opp_data.append({
                            "Rank": f"#{opp['rank']}",
                            "Symbol": opp["symbol"],
                            "Price": f"${opp['price']:,.2f}",
                            "24h": f"{opp['change_24h_pct']:+.1f}%",
                            "RSI": f"{opp['rsi']:.0f}",
                            "Score": f"{opp['momentum_score']:.0f}",
                            "Trend": f"{trend_emoji} {opp['trend']}"
                        })
                    st.dataframe(pd.DataFrame(opp_data), use_container_width=True, hide_index=True)
                else:
                    st.info("No opportunities found in last scan")
            except Exception as e:
                st.warning(f"Could not load screener data: {e}")
        else:
            st.info("Screener data not available yet.")
    
    # Performance Tracking (collapsed)
    with st.expander("📈 Performance & Trade Stats"):
        total_trades = status["trades"].get("total", 0)
        winning_trades = status["trades"].get("winning", 0)
        losing_trades = status["trades"].get("losing", 0)
        total_pnl = status["performance"].get("total_pnl", 0)
        actual_win_rate = status["trades"].get("win_rate", 0)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Win Rate", f"{actual_win_rate:.1f}%" if total_trades > 0 else "N/A")
        with col2:
            st.metric("Total Trades", total_trades)
        with col3:
            st.metric("Wins / Losses", f"{winning_trades} / {losing_trades}")
        with col4:
            st.metric("Total P&L", f"${total_pnl:+,.2f}")
    
    # Bot Configuration (collapsed)
    with st.expander("⚙️ Bot Configuration"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Risk Parameters (Live-Ready):**")
            st.write("• Position Size: **12%** per trade")
            st.write("• Max Positions: **8**")
            st.write("• Stop Loss: **1%** (net -1.5% after fees)")
            st.write("• Take Profit: **2.5%** (net +2% after fees)")
            st.write("• **R:R Ratio: 1.33:1** (need 43% win rate)")
            st.write("• Daily Loss Limit: **3%**")
        with col2:
            st.write("**Bot Settings:**")
            st.write("• Check Interval: **5 seconds**")
            st.write("• Screener Refresh: **3 minutes**")
            st.write("• Strategy: **Aggressive Scalping**")
            st.write("• Fees: 0.25% per trade (0.5% round-trip)")
        st.divider()
        st.write("**📈 Trailing Stop (NEW):**")
        st.write("• Activates after **+1%** gain from entry")
        st.write("• Trails **1%** below highest price reached")
        st.write("• Locks in profits on big moves while letting winners run")
    
    # ETA & Milestones (collapsed)
    with st.expander("🎯 Milestones & ETA"):
        eta = status["eta"]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current ETA", eta["eta_string"], f"Target: {eta['eta_date']}")
            st.caption(f"Based on {eta['monthly_return_used']:.1f}% monthly return")
        with col2:
            nm = status["next_milestone"]
            if nm:
                st.write(f"**Next Milestone:** {nm['emoji']} {nm['name']}")
                st.progress(nm['progress_pct'] / 100)
                st.write(f"Target: ${nm['amount']:,.0f} | Remaining: ${nm['remaining']:,.2f}")
    
    # Trade History (collapsed)
    with st.expander("📜 Trade History"):
        # Load trades from challenge state file
        challenge_file = Path("data/million_dollar_challenge.json")
        if challenge_file.exists():
            try:
                with open(challenge_file) as f:
                    challenge_data = json.load(f)
                trades = challenge_data.get("trades", [])
                
                if trades:
                    # Show most recent trades first
                    trades_reversed = list(reversed(trades))
                    trade_data = []
                    for t in trades_reversed[:20]:  # Last 20 trades
                        timestamp = t.get("timestamp", "")[:16].replace("T", " ")
                        pnl = t.get("pnl", 0)
                        pnl_pct = t.get("pnl_pct", 0)
                        emoji = "🟢" if pnl >= 0 else "🔴"
                        trade_data.append({
                            "Time": timestamp,
                            "Symbol": t.get("symbol", ""),
                            "Entry": f"${t.get('entry_price', 0):,.2f}",
                            "Exit": f"${t.get('exit_price', 0):,.2f}",
                            "P&L": f"{emoji} ${pnl:+,.2f}",
                            "P&L %": f"{pnl_pct:+.2f}%",
                            "Reason": t.get("reason", "")[:30]
                        })
                    st.dataframe(pd.DataFrame(trade_data), use_container_width=True, hide_index=True)
                    st.caption(f"Showing {len(trade_data)} of {len(trades)} total trades")
                else:
                    st.info("No trades recorded yet. Trades will appear here after the bot sells positions.")
            except Exception as e:
                st.warning(f"Could not load trade history: {e}")
        else:
            st.info("Trade history not available yet.")


def show_realtime_summary():
    """Real-time P&L summary header with refresh button."""
    from datetime import datetime
    
    # Create header container
    header_col1, header_col2 = st.columns([4, 1])
    
    with header_col1:
        st.markdown("### 📊 Real-Time Summary")
    
    with header_col2:
        if st.button("🔄 Refresh", key="refresh_btn", type="primary"):
            st.rerun()
    
    # Get live data from Alpaca
    if ALPACA_AVAILABLE:
        try:
            api = tradeapi.REST(config.api_key, config.api_secret, config.base_url)
            account = api.get_account()
            positions = api.list_positions()
            
            # Calculate totals
            equity = float(account.equity)
            cash = float(account.cash)
            total_cost = sum(float(p.cost_basis) for p in positions) if positions else 0
            total_unrealized_pl = sum(float(p.unrealized_pl) for p in positions) if positions else 0
            total_unrealized_pl_pct = (total_unrealized_pl / total_cost * 100) if total_cost > 0 else 0
            
            # Display real-time metrics in a highlighted box
            st.markdown("""
            <style>
            .realtime-box {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 2px solid #0f3460;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("💰 Portfolio", f"${equity:,.2f}")
            
            with col2:
                st.metric("💵 Cash", f"${cash:,.2f}")
            
            with col3:
                st.metric("📈 Invested", f"${total_cost:,.2f}")
            
            with col4:
                # Color the P&L based on positive/negative
                pl_color = "normal" if total_unrealized_pl >= 0 else "inverse"
                st.metric(
                    "📊 Unrealized P&L", 
                    f"${total_unrealized_pl:+,.2f}", 
                    f"{total_unrealized_pl_pct:+.2f}%",
                    delta_color=pl_color
                )
            
            with col5:
                st.metric("📍 Positions", f"{len(positions)}")
            
            # Show last update time
            st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} | Bot checks every 5 seconds")
            
        except Exception as e:
            st.error(f"Could not fetch live data: {e}")
    else:
        st.warning("Alpaca API not available")
    
    st.divider()


def show_combined_dashboard():
    """Combined dashboard - Million Dollar Challenge focused."""
    
    # Sidebar - Trading Mode & Settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Auto-refresh option using streamlit-autorefresh (preserves state)
        st.subheader("🔄 Auto-Refresh")
        
        # Initialize session state
        if "auto_refresh_enabled" not in st.session_state:
            st.session_state.auto_refresh_enabled = True
        if "refresh_interval" not in st.session_state:
            st.session_state.refresh_interval = 15
        
        # Interval selection FIRST (before checkbox to avoid reset)
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
            # Use streamlit-autorefresh component (doesn't cause full page reload)
            count = st_autorefresh(interval=refresh_interval * 1000, limit=None, key="dashboard_autorefresh")
            st.caption(f"✅ Auto-refreshing every {interval_labels.get(refresh_interval, str(refresh_interval) + ' seconds')}")
        
        st.divider()
        
        # Trading Mode Toggle
        st.subheader("📝 Trading Mode")
        trading_mode = st.radio(
            "Select Mode",
            ["📝 Paper Trading", "💵 Real Trading"],
            index=0,
            help="Paper trading uses simulated money. Real trading uses actual funds."
        )
        
        if trading_mode == "💵 Real Trading":
            st.warning("⚠️ Real trading is not yet configured. You'll need to add real Alpaca API keys.")
            st.info("To enable real trading:\n1. Create a live Alpaca account\n2. Add APCA_API_KEY_ID_LIVE and APCA_API_SECRET_KEY_LIVE to .env\n3. Set APCA_API_BASE_URL to https://api.alpaca.markets")
        else:
            st.success("✅ Using Paper Trading (simulated)")
        
        st.divider()
        
        # Contribution button in sidebar
        if st.button("💵 Add $250 Contribution", key="sidebar_contrib"):
            if "million_challenge" in st.session_state:
                st.session_state.million_challenge.add_contribution(250.0)
                st.success("Contribution recorded!")
                st.rerun()
    
    # Main content - Million Dollar Challenge only
    st.title("💰 Million Dollar Challenge")
    
    # REAL-TIME SUMMARY AT TOP
    show_realtime_summary()
    
    # Trading mode indicator
    if trading_mode == "📝 Paper Trading":
        st.info("🎮 **Paper Trading Mode** - All trades are simulated")
    else:
        st.error("💰 **Real Trading Mode** - Using real money!")
    
    # Show Million Dollar dashboard directly
    show_million_dollar_dashboard()


def show_million_dollar_summary():
    """Compact summary of Million Dollar Challenge with ETA projections."""
    st.subheader("💰 Million Dollar Challenge")
    
    if not MILLION_CHALLENGE_AVAILABLE:
        st.error("Module not available")
        return
    
    if "million_challenge" not in st.session_state:
        st.session_state.million_challenge = MillionDollarChallenge(starting_capital=1000.0)
    
    challenge = st.session_state.million_challenge
    status = challenge.get_status()
    
    # Progress
    progress = status["challenge"]["progress_pct"] / 100
    st.progress(progress, text=f"{status['challenge']['progress_pct']:.4f}% to $1M")
    
    # Key metrics row 1
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Balance", f"${status['challenge']['current_balance']:,.2f}")
    with col2:
        gains = status['performance']['trading_gains']
        st.metric("Trading Gains", f"${gains:+,.2f}", f"{status['performance']['trading_gains_pct']:+.1f}%")
    with col3:
        st.metric("Contributed", f"${status['contributions']['total_contributed']:,.2f}")
    
    # ETA Section
    eta = status["eta"]
    st.write(f"**⏱️ ETA to $1M:** {eta['eta_string']} ({eta['eta_date']})")
    
    # Scenario table
    with st.expander("📊 ETA Scenarios"):
        scenario_data = []
        for s in status.get("scenarios", []):
            scenario_data.append({
                "Scenario": f"{s['color']} {s['name']}",
                "Monthly Return": f"{s['monthly_return']}%",
                "ETA": s["eta_string"],
                "Target Date": s["eta_date"]
            })
        if scenario_data:
            st.dataframe(pd.DataFrame(scenario_data), use_container_width=True, hide_index=True)
    
    # Next milestone
    nm = status["next_milestone"]
    if nm:
        st.caption(f"Next: {nm['emoji']} {nm['name']} (${nm['remaining']:,.0f} to go)")
    
    # Contribution button
    if st.button("💵 Add $250 Contribution", key="million_contrib"):
        challenge.add_contribution(250.0)
        st.success("Contribution recorded!")
        st.rerun()


def show_small_account_summary():
    """Compact summary of Small Account Challenge."""
    st.subheader("🎯 Small Account Challenge")
    
    if not CHALLENGE_AVAILABLE:
        st.error("Module not available")
        return
    
    if "challenge" not in st.session_state:
        st.session_state.challenge = SmallAccountChallenge(starting_capital=500.0, goal=1000.0)
    
    challenge = st.session_state.challenge
    status = challenge.get_status()
    
    # Progress
    progress = status["challenge"]["progress_pct"] / 100
    st.progress(progress, text=f"{status['challenge']['progress_pct']:.1f}% to $1K")
    
    # Goal reached celebration
    if status["challenge"]["goal_reached"]:
        st.success("🎉 GOAL REACHED!")
    
    # Key metrics
    col1, col2 = st.columns(2)
    with col1:
        delta = status["challenge"]["current_balance"] - status["challenge"]["starting_balance"]
        st.metric("Balance", f"${status['challenge']['current_balance']:,.2f}", f"${delta:+,.2f}")
        st.metric("Win Rate", f"{status['trades']['win_rate']:.0f}%", f"{status['trades']['total']} trades")
    with col2:
        st.metric("Total P&L", f"${status['performance']['total_pnl']:,.2f}", f"{status['performance']['total_pnl_pct']:+.1f}%")
        if status['projections']['projected_days_to_goal']:
            st.metric("Est. Days to Goal", status['projections']['projected_days_to_goal'])
        else:
            st.metric("Est. Days to Goal", "N/A")
    
    # Today's status
    st.caption(f"Today: ${status['today']['pnl']:+,.2f} P&L | {status['today']['trades']} trades")


def show_live_portfolio_section():
    """Shared live portfolio section with both bot targets."""
    st.subheader("💼 Live Portfolio (Alpaca)")
    
    if not ALPACA_AVAILABLE:
        st.warning("Alpaca API not available")
        return
    
    try:
        api = tradeapi.REST(config.api_key, config.api_secret, config.base_url)
        account = api.get_account()
        positions = api.list_positions()
        
        # Account overview
        col1, col2, col3, col4 = st.columns(4)
        
        equity = float(account.equity)
        cash = float(account.cash)
        total_cost = sum(float(p.cost_basis) for p in positions) if positions else 0
        total_unrealized_pl = sum(float(p.unrealized_pl) for p in positions) if positions else 0
        total_unrealized_pl_pct = (total_unrealized_pl / total_cost * 100) if total_cost > 0 else 0
        
        with col1:
            st.metric("Portfolio Value", f"${equity:,.2f}")
        with col2:
            st.metric("Cash Available", f"${cash:,.2f}")
        with col3:
            st.metric("Invested", f"${total_cost:,.2f}")
        with col4:
            st.metric("Unrealized P&L", f"${total_unrealized_pl:+,.2f}", f"{total_unrealized_pl_pct:+.2f}%")
        
        # Define which symbols belong to which challenge
        million_dollar_symbols = ["ETHUSD", "ETH/USD", "AVAXUSD", "AVAX/USD", "LINKUSD", "LINK/USD"]
        small_account_symbols = ["BTCUSD", "BTC/USD", "SOLUSD", "SOL/USD", "DOGEUSD", "DOGE/USD"]
        
        # Separate positions by challenge
        million_positions = []
        small_positions = []
        other_positions = []
        
        if positions:
            for p in positions:
                pos_dict = {
                    "Symbol": p.symbol,
                    "Qty": f"{float(p.qty):.6f}" if float(p.qty) < 1 else f"{float(p.qty):.2f}",
                    "Entry": f"${float(p.avg_entry_price):,.2f}",
                    "Current": f"${float(p.current_price):,.2f}",
                    "P&L": f"${float(p.unrealized_pl):+,.2f}",
                    "P&L %": f"{float(p.unrealized_plpc) * 100:+.2f}%"
                }
                
                if p.symbol in million_dollar_symbols:
                    million_positions.append(pos_dict)
                elif p.symbol in small_account_symbols:
                    small_positions.append(pos_dict)
                else:
                    other_positions.append(pos_dict)
        
        # Show positions grouped by challenge
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**💰 Million Dollar Bot Positions**")
            if million_positions:
                st.dataframe(pd.DataFrame(million_positions), use_container_width=True, hide_index=True)
            else:
                st.caption("No positions")
        
        with col2:
            st.write("**🎯 Small Account Bot Positions**")
            if small_positions:
                st.dataframe(pd.DataFrame(small_positions), use_container_width=True, hide_index=True)
            else:
                st.caption("No positions")
        
        if other_positions:
            st.write("**Other Positions**")
            st.dataframe(pd.DataFrame(other_positions), use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Bot Trading Targets - Both Bots
        show_bot_targets_section()
                
    except Exception as e:
        st.error(f"Could not connect to Alpaca: {e}")


def show_bot_targets_section():
    """Show trading targets for all bots."""
    st.subheader("🤖 Bot Trading Targets")
    
    col1, col2, col3 = st.columns(3)
    
    # Million Dollar Bot
    with col1:
        st.write("**💰 Million Dollar Bot**")
        million_state_file = Path("data/million_dollar_bot_state.json")
        if million_state_file.exists():
            try:
                with open(million_state_file) as f:
                    bot_state = json.load(f)
                
                bot_positions = bot_state.get("positions", {})
                if bot_positions:
                    target_data = []
                    for symbol, pos in bot_positions.items():
                        target_data.append({
                            "Symbol": symbol,
                            "Entry": f"${pos.get('entry_price', 0):,.2f}",
                            "Stop Loss": f"${pos.get('stop_loss', 0):,.2f}",
                            "Take Profit": f"${pos.get('take_profit', 0):,.2f}",
                        })
                    st.dataframe(pd.DataFrame(target_data), use_container_width=True, hide_index=True)
                    st.caption(f"Last update: {bot_state.get('last_update', 'N/A')[:19]}")
                else:
                    st.caption("No active positions")
            except Exception as e:
                st.error(f"Error loading state: {e}")
        else:
            st.caption("Bot not started yet")
        
        # Bot status indicator
        st.caption("🟢 Bot Active" if million_state_file.exists() else "🔴 Bot Inactive")
    
    # Small Account Bot
    with col2:
        st.write("**🎯 Small Account Bot**")
        small_state_file = Path("data/autonomous_bot_state.json")
        if small_state_file.exists():
            try:
                with open(small_state_file) as f:
                    bot_state = json.load(f)
                
                bot_positions = bot_state.get("positions", {})
                if bot_positions:
                    target_data = []
                    for symbol, pos in bot_positions.items():
                        target_data.append({
                            "Symbol": symbol,
                            "Entry": f"${pos.get('entry_price', 0):,.2f}",
                            "Stop Loss": f"${pos.get('stop_loss', 0):,.2f}",
                            "Take Profit": f"${pos.get('take_profit', 0):,.2f}",
                        })
                    st.dataframe(pd.DataFrame(target_data), use_container_width=True, hide_index=True)
                    st.caption(f"Last update: {bot_state.get('last_update', 'N/A')[:19]}")
                else:
                    st.caption("No active positions")
            except Exception as e:
                st.error(f"Error loading state: {e}")
        else:
            st.caption("Bot not started yet")
        
        # Bot status indicator
        st.caption("🟢 Bot Active" if small_state_file.exists() else "🔴 Bot Inactive")
    
    # Coinbase Bot (Long/Short)
    with col3:
        st.write("**🔄 Coinbase Bot** *(Long/Short)*")
        coinbase_state_file = Path("/opt/coinbase-trading-bot/data/trader_state.json")
        if coinbase_state_file.exists():
            try:
                with open(coinbase_state_file) as f:
                    bot_state = json.load(f)
                
                # Show balance
                balance = bot_state.get("current_balance", 0)
                st.metric("Balance", f"${balance:,.2f}")
                
                bot_positions = bot_state.get("positions", [])
                if bot_positions:
                    target_data = []
                    for pos in bot_positions:
                        side_emoji = "🟢" if pos.get('side') == 'long' else "🔴"
                        target_data.append({
                            "Symbol": pos.get('symbol', 'N/A'),
                            "Side": f"{side_emoji} {pos.get('side', 'N/A').upper()}",
                            "Entry": f"${pos.get('entry_price', 0):,.2f}",
                            "SL/TP": f"${pos.get('stop_loss', 0):,.2f} / ${pos.get('take_profit', 0):,.2f}",
                        })
                    st.dataframe(pd.DataFrame(target_data), use_container_width=True, hide_index=True)
                    st.caption(f"Last update: {bot_state.get('last_updated', 'N/A')[:19]}")
                else:
                    st.caption("No active positions")
                
                # Show recent trades
                trades = bot_state.get("trade_history", [])[-3:]
                if trades:
                    st.write("**Recent Trades:**")
                    for t in reversed(trades):
                        pnl = t.get('pnl', 0)
                        emoji = "🟢" if pnl >= 0 else "🔴"
                        side = t.get('side', 'long').upper()
                        st.caption(f"{emoji} {side} {t.get('symbol', 'N/A')}: ${pnl:+,.2f}")
                
                st.caption("🟢 Bot Active")
            except Exception as e:
                st.error(f"Error loading state: {e}")
        else:
            st.caption("Bot not started yet")
            st.caption("🔴 Bot Inactive")
            st.info("Set up Coinbase API keys to enable")


def main():
    """Main entry point."""
    st.set_page_config(page_title="Trading Challenges", page_icon="💰", layout="wide")
    show_combined_dashboard()


if __name__ == "__main__":
    main()
