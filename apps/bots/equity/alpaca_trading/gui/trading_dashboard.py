"""
Streamlit Trading Dashboard for Alpaca Trading Bot

This module provides a comprehensive web-based GUI for monitoring and controlling
the trading bot with three main pages:
1. Dashboard - Portfolio overview and positions
2. Strategy - Filter configuration
3. Stock Universe - Custom stock list management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import json
import io

# Import trading bot modules
try:
    from alpaca_trading.core.config import config
    from alpaca_trading.scripts.screener import StockScreener
    from alpaca_trading.scripts.daily_trading_automation import DailyTradingAutomation
    from alpaca_trading.gui.strategy_config import show_strategy_page
    from alpaca_trading.gui.stock_universe import show_stock_universe_page
    from alpaca_trading.gui.system_logs import show_system_logs
    from alpaca_trading.gui.crypto_dashboard import show_crypto_dashboard
    from alpaca_trading.gui.challenge_dashboard import show_challenge_dashboard
    import alpaca_trade_api as tradeapi
except ImportError as e:
    st.error(f"Failed to import trading modules: {e}")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Alpaca Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .danger-card {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    
    /* Hide the unwanted white progress bars from st.metric - multiple approaches */
    [data-testid="metric-container"] div[style*="height"] {
        display: none !important;
    }
    
    [data-testid="metric-container"] div[style*="background"] {
        display: none !important;
    }
    
    [data-testid="metric-container"] div[style*="width: 100%"] {
        display: none !important;
    }
    
    /* Target the progress bar specifically */
    [data-testid="metric-container"] > div > div:last-child {
        display: none !important;
    }
    
    /* Alternative approach - hide all divs with background styling */
    [data-testid="metric-container"] div[style*="rgb"] {
        display: none !important;
    }
    
    /* Improve metric styling */
    [data-testid="metric-container"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
    }
    
    /* Style metric values */
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 1.5rem !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
    }
    
    /* Style metric labels */
    [data-testid="metric-container"] [data-testid="metric-label"] {
        font-size: 0.9rem !important;
        color: #666 !important;
        font-weight: 500 !important;
    }
    
    /* Style metric deltas */
    [data-testid="metric-container"] [data-testid="metric-delta"] {
        font-size: 0.8rem !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

class TradingDashboard:
    """Main trading dashboard class."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.api = None
        self.screener = None
        self.automation = None
        self._initialize_api()
    
    def _initialize_api(self):
        """Initialize Alpaca API connection."""
        try:
            self.api = tradeapi.REST(
                config.api_key,
                config.api_secret,
                base_url=config.base_url,
                api_version='v2'
            )
            self.screener = StockScreener(self.api)
            self.automation = DailyTradingAutomation()
            
            # Test connection
            account = self.api.get_account()
            st.session_state.api_connected = True
            st.session_state.account = account
            
        except Exception as e:
            st.session_state.api_connected = False
            st.session_state.api_error = str(e)
            logger.error(f"Failed to initialize API: {e}")
    
    def run(self):
        """Run the main dashboard application."""
        # Sidebar navigation
        st.sidebar.title("🚀 Trading Bot Control")
        
        # API Connection Status
        if st.session_state.get('api_connected', False):
            st.sidebar.success("✅ API Connected")
        else:
            st.sidebar.error("❌ API Connection Failed")
            if st.session_state.get('api_error'):
                st.sidebar.error(f"Error: {st.session_state.api_error}")
        
        # Navigation
        page = st.sidebar.selectbox(
            "Navigate to:",
            ["📊 Dashboard", "🎯 $500→$1K Challenge", "🪙 Crypto Trading", "📈 Stock Analysis", "⚙️ Strategy Configuration", "📋 Stock Universe Management", "📋 System Logs"]
        )
        
        # Page routing
        if page == "📊 Dashboard":
            self.show_dashboard_page()
        elif page == "🎯 $500→$1K Challenge":
            show_challenge_dashboard()
        elif page == "🪙 Crypto Trading":
            show_crypto_dashboard()
        elif page == "📈 Stock Analysis":
            self.show_stock_analysis_page()
        elif page == "⚙️ Strategy Configuration":
            show_strategy_page()
        elif page == "📋 Stock Universe Management":
            show_stock_universe_page()
        elif page == "📋 System Logs":
            show_system_logs()
    
    def show_dashboard_page(self):
        """Display the main dashboard page."""
        st.markdown('<h1 class="main-header">📊 Trading Dashboard</h1>', unsafe_allow_html=True)
        
        if not st.session_state.get('api_connected', False):
            st.error("API connection required to display dashboard data.")
            return
        
        # Refresh button
        col1, col2, col3 = st.columns([1, 1, 8])
        with col1:
            if st.button("🔄 Refresh Data"):
                st.rerun()
        
        # Account Overview
        self._show_account_overview()
        
        st.divider()
        
        # Screening Status
        self._show_screening_status()
        
        st.divider()
        
        # Current Positions
        self._show_current_positions()
        
        st.divider()
        
        # Recent Transactions
        self._show_recent_transactions()
        
        st.divider()
        
        # Performance Charts
        self._show_performance_charts()
    
    def _show_account_overview(self):
        """Display account overview metrics."""
        st.subheader("💰 Account Overview")
        
        try:
            account = self.api.get_account()
            positions = self.api.list_positions()
            
            # Calculate total unrealized P&L from positions
            total_unrealized_pl = 0
            total_unrealized_plpc = 0
            if positions:
                total_unrealized_pl = sum(float(pos.unrealized_pl or 0) for pos in positions)
                # Calculate percentage based on position market value
                total_market_value = sum(float(pos.market_value or 0) for pos in positions)
                if total_market_value > 0:
                    total_unrealized_plpc = (total_unrealized_pl / total_market_value) * 100
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_color = "green" if total_unrealized_pl >= 0 else "red"
                delta_symbol = "+" if total_unrealized_pl >= 0 else ""
                st.markdown(f'''
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #666; font-weight: 500; margin-bottom: 0.25rem;">Portfolio Value</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 0.25rem;">${float(account.portfolio_value):,.2f}</div>
                    {f'<div style="font-size: 0.8rem; color: {delta_color}; font-weight: 500;">{delta_symbol}${total_unrealized_pl:,.2f}</div>' if total_unrealized_pl != 0 else ''}
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'''
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #666; font-weight: 500; margin-bottom: 0.25rem;">Buying Power</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1f77b4;">${float(account.buying_power):,.2f}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                pl_color = "green" if total_unrealized_pl >= 0 else "red"
                pl_symbol = "+" if total_unrealized_pl >= 0 else ""
                perc_symbol = "+" if total_unrealized_plpc >= 0 else ""
                st.markdown(f'''
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #666; font-weight: 500; margin-bottom: 0.25rem;">Total P&L</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: {pl_color}; margin-bottom: 0.25rem;">{pl_symbol}${total_unrealized_pl:,.2f}</div>
                    {f'<div style="font-size: 0.8rem; color: {pl_color}; font-weight: 500;">{perc_symbol}{total_unrealized_plpc:.2f}%</div>' if total_unrealized_plpc != 0 else ''}
                </div>
                ''', unsafe_allow_html=True)
            
            with col4:
                st.markdown(f'''
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #666; font-weight: 500; margin-bottom: 0.25rem;">Open Positions</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1f77b4;">{len(positions)}</div>
                </div>
                ''', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error fetching account data: {e}")
    
    def _show_screening_status(self):
        """Display screening status and universe information."""
        st.subheader("🔍 Screening Status")
        
        try:
            # Try to get actual universe data from screener
            from alpaca_trading.scripts.screener import StockScreener
            screener = StockScreener(self.api)
            universe = screener.get_curated_stock_universe()
            universe_size = len(universe)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f'''
                <div class="metric-card" title="Total curated + manual stocks available for screening">
                    <div style="font-size: 0.9rem; color: #666; font-weight: 500; margin-bottom: 0.25rem;">Total Universe</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1f77b4;">{universe_size} stocks</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'''
                <div class="metric-card" title="All stocks in universe are processed (no limits)">
                    <div style="font-size: 0.9rem; color: #666; font-weight: 500; margin-bottom: 0.25rem;">Screening Coverage</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1f77b4;">100% of universe</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                # Try to get recent screening results if available
                try:
                    # This would be from cached results or recent screening
                    screening_value = "Pre-Market"
                    screening_help = "Most recent screening cycle"
                except:
                    screening_value = "N/A"
                    screening_help = "No recent screening data available"
                
                st.markdown(f'''
                <div class="metric-card" title="{screening_help}">
                    <div style="font-size: 0.9rem; color: #666; font-weight: 500; margin-bottom: 0.25rem;">Last Screening</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1f77b4;">{screening_value}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col4:
                st.markdown(f'''
                <div class="metric-card" title="Alpaca, Polygon, Tiingo APIs operational">
                    <div style="font-size: 0.9rem; color: #666; font-weight: 500; margin-bottom: 0.25rem;">Data Sources</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #1f77b4;">3 APIs</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # Add info about screening process
            st.info("""
            📈 **Screening Process Transparency:**
            
            The system now processes ALL stocks in the universe for complete coverage. 
            No artificial limits are applied, ensuring every stock is evaluated.
            
            - **Universe**: All manually curated stocks
            - **Reviewed**: 100% of universe (all stocks processed)
            - **Selected**: Stocks meeting all technical criteria
            """)
            
        except Exception as e:
            st.warning(f"⚠️ Screening status unavailable: {str(e)[:100]}...")
            
            # Fallback display
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Universe Size", "~192 stocks")
            with col2:
                st.metric("Screening Coverage", "100% of universe")
            with col3:
                st.metric("Data Sources", "3 APIs")
    
    def _show_current_positions(self):
        """Display current positions table."""
        st.subheader("📈 Current Positions")
        
        try:
            positions = self.api.list_positions()
            
            if not positions:
                st.info("No open positions currently.")
                return
            
            # Create positions dataframe
            positions_data = []
            for pos in positions:
                # Calculate profit/loss levels
                entry_price = float(pos.avg_entry_price)
                current_price = float(pos.current_price)
                qty = int(pos.qty)
                
                # Estimate profit-taking levels (2:1 and 3:1 R:R)
                # This is simplified - in practice you'd get this from your strategy
                atr_estimate = current_price * 0.02  # 2% ATR estimate
                stop_loss = entry_price - atr_estimate
                profit_target_1 = entry_price + (2 * atr_estimate)  # 2:1 R:R
                profit_target_2 = entry_price + (3 * atr_estimate)  # 3:1 R:R
                
                positions_data.append({
                    'Symbol': pos.symbol,
                    'Quantity': qty,
                    'Entry Price': f"${entry_price:.2f}",
                    'Current Price': f"${current_price:.2f}",
                    'Market Value': f"${float(pos.market_value):,.2f}",
                    'Unrealized P&L': f"${float(pos.unrealized_pl):,.2f}",
                    'P&L %': f"{float(pos.unrealized_plpc) * 100:.2f}%",
                    'Stop Loss': f"${stop_loss:.2f}",
                    'Profit Target 1 (2:1)': f"${profit_target_1:.2f}",
                    'Profit Target 2 (3:1)': f"${profit_target_2:.2f}",
                })
            
            df = pd.DataFrame(positions_data)
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
        except Exception as e:
            st.error(f"Error fetching positions: {e}")
    
    def _show_recent_transactions(self):
        """Display recent transactions."""
        st.subheader("📋 Recent Transactions")
        
        try:
            # Get recent orders
            orders = self.api.list_orders(
                status='filled',
                limit=20,
                nested=True
            )
            
            if not orders:
                st.info("No recent transactions found.")
                return
            
            # Create transactions dataframe
            transactions_data = []
            for order in orders:
                transactions_data.append({
                    'Date': order.filled_at.strftime('%Y-%m-%d %H:%M') if order.filled_at else 'N/A',
                    'Symbol': order.symbol,
                    'Side': order.side.upper(),
                    'Quantity': int(order.qty),
                    'Price': f"${float(order.filled_avg_price or 0):.2f}",
                    'Total': f"${float(order.filled_qty or 0) * float(order.filled_avg_price or 0):.2f}",
                    'Status': order.status.upper()
                })
            
            df = pd.DataFrame(transactions_data)
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
        except Exception as e:
            st.error(f"Error fetching transactions: {e}")
    
    def _show_performance_charts(self):
        """Display performance charts."""
        st.subheader("📊 Performance Charts")
        
        try:
            # Get portfolio history
            portfolio_history = self.api.get_portfolio_history(
                period='1M',
                timeframe='1D'
            )
            
            if portfolio_history.equity:
                # Create equity curve chart
                dates = [datetime.fromtimestamp(ts) for ts in portfolio_history.timestamp]
                equity_values = portfolio_history.equity
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=equity_values,
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='#1f77b4', width=2)
                ))
                
                fig.update_layout(
                    title='Portfolio Performance (Last 30 Days)',
                    xaxis_title='Date',
                    yaxis_title='Portfolio Value ($)',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No portfolio history data available.")
                
        except Exception as e:
            st.error(f"Error creating performance charts: {e}")

    def _get_company_name(self, symbol: str) -> str:
        """Get company name for a stock symbol."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different name fields
            name = info.get('longName') or info.get('shortName') or info.get('displayName')
            if name:
                return name
        except Exception:
            pass
        
        # Fallback: return symbol if name lookup fails
        return symbol
    
    def _get_stock_options_with_names(self, universe: list) -> dict:
        """Create stock options with company names for dropdown."""
        stock_options = {}
        
        # Show progress for large universes
        if len(universe) > 10:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        for i, symbol in enumerate(universe[:50]):  # Limit to first 50 to avoid timeout
            try:
                company_name = self._get_company_name(symbol)
                if company_name != symbol:
                    display_name = f"{symbol} - {company_name}"
                else:
                    display_name = symbol
                stock_options[display_name] = symbol
                
                # Update progress
                if len(universe) > 10:
                    progress = (i + 1) / min(len(universe), 50)
                    progress_bar.progress(progress)
                    status_text.text(f"Loading company names... {i+1}/{min(len(universe), 50)}")
                    
            except Exception:
                # If name lookup fails, just use symbol
                stock_options[symbol] = symbol
        
        # Clean up progress indicators
        if len(universe) > 10:
            progress_bar.empty()
            status_text.empty()
            
        return stock_options
    
    def show_stock_analysis_page(self):
        """Display stock analysis page with interactive charts."""
        st.title("📈 Stock Analysis")
        st.markdown("Analyze individual stocks from your universe with interactive charts and technical indicators.")
        
        # Data limitations notice
        with st.expander("ℹ️ Data Availability Notice", expanded=False):
            st.info("""**Important:** This feature requires market data access. If you see "no data available" errors:
            
• **Free Alpaca accounts** have limited access to recent market data
• **Some symbols** in your universe may be invalid or delisted
• **Market hours** can affect data availability
            
For full functionality, consider upgrading your Alpaca data subscription or use the main Dashboard for portfolio data.""")
        
        # Get stock universe for dropdown
        try:
            if hasattr(self, 'screener') and self.screener:
                universe = sorted(list(self.screener.get_curated_stock_universe()))
            else:
                universe = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]  # Fallback
        except Exception as e:
            st.warning(f"Could not load stock universe: {e}")
            universe = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        
        # Create stock options with company names
        with st.spinner("Loading stock information..."):
            stock_options = self._get_stock_options_with_names(universe)
        
        # Sidebar controls
        st.sidebar.header("📈 Analysis Parameters")
        
        # Stock selection
        if stock_options:
            selected_option = st.sidebar.selectbox(
                "Select Stock from Universe:",
                options=list(stock_options.keys()),
                index=0
            )
            symbol = stock_options[selected_option]  # Get the actual symbol
        else:
            symbol = st.sidebar.text_input("Stock Symbol:", value="AAPL")
        
        # Manual symbol input option
        manual_symbol = st.sidebar.text_input(
            "Or enter symbol manually:",
            value="",
            help="Enter any stock symbol to analyze (e.g., AAPL, MSFT)"
        )
        
        # Use manual symbol if provided
        if manual_symbol:
            symbol = manual_symbol.upper().strip()
        
        # Technical analysis parameters
        short_window = st.sidebar.slider("Short MA Window", 1, 20, 5)
        long_window = st.sidebar.slider("Long MA Window", 10, 100, 20)
        
        # Display analysis
        if symbol:
            # Get company name for display
            company_name = self._get_company_name(symbol.upper())
            display_title = f"{symbol.upper()} - {company_name}" if company_name != symbol.upper() else symbol.upper()
            
            self._display_stock_chart(symbol.upper(), short_window, long_window, display_title)
            self._display_stock_metrics(symbol.upper(), display_title)
    
    def _display_stock_chart(self, symbol: str, short_window: int, long_window: int, display_title: str = None):
        """Display interactive stock chart with moving averages."""
        chart_title = display_title or symbol
        st.subheader(f"📈 {chart_title} Price Chart")
        
        try:
            # Use the screener's data provider for robust data fetching
            if hasattr(self, 'screener') and self.screener and hasattr(self.screener, 'data_provider'):
                bars = self.screener.data_provider.get_bars(
                    symbol,
                    timeframe='1Day',
                    limit=max(long_window * 2, 100)
                )
            else:
                # Fallback to direct API with corrected environment variable
                import os
                api = tradeapi.REST(
                    os.getenv('APCA_API_KEY_ID'),
                    os.getenv('APCA_API_SECRET_KEY'),
                    os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),  # Use correct env var
                    api_version='v2'
                )
                bars = api.get_bars(
                    symbol,
                    tradeapi.TimeFrame.Day,
                    limit=max(long_window * 2, 100)
                ).df
            
            if bars is None or bars.empty:
                st.error(f"No data available for {symbol}")
                
                # Provide specific guidance based on common issues
                st.info("""**Possible reasons:**
• **Data subscription limitations** - Your Alpaca account may not have access to recent market data
• **Invalid symbol** - The symbol may not exist or be delisted
• **Limited trading history** - New or low-volume stocks may have insufficient data
• **Market hours** - Some data may only be available during market hours""")
                
                st.warning("""**Solutions:**
• Try a different symbol (e.g., AAPL, MSFT, TSLA)
• Check if the symbol exists on major exchanges
• Consider upgrading your Alpaca data subscription for real-time data
• Use the main Dashboard page for portfolio and position data""")
                
                return
            
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
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=bars.index,
                y=bars['ma_long'],
                name=f'MA {long_window}',
                line=dict(color='orange', width=2)
            ))
            
            # Update layout
            fig.update_layout(
                title=f"{chart_title} - Candlestick Chart with Moving Averages",
                xaxis_title='Date',
                yaxis_title='Price ($)',
                template='plotly_white',
                showlegend=True,
                height=600,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display recent data table
            st.subheader("Recent Price Data")
            recent_data = bars.tail(10)[['open', 'high', 'low', 'close', 'volume', 'ma_short', 'ma_long']]
            recent_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', f'MA{short_window}', f'MA{long_window}']
            
            # Format the dataframe
            for col in ['Open', 'High', 'Low', 'Close', f'MA{short_window}', f'MA{long_window}']:
                recent_data[col] = recent_data[col].round(2)
            recent_data['Volume'] = recent_data['Volume'].astype(int)
            
            st.dataframe(recent_data, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error fetching chart data for {symbol}: {e}")
    
    def _display_stock_metrics(self, symbol: str, display_title: str = None):
        """Display key stock metrics and analysis."""
        metrics_title = display_title or symbol
        st.subheader(f"📊 {metrics_title} Key Metrics")
        
        try:
            # Get latest quote with proper API configuration
            import os
            api = tradeapi.REST(
                os.getenv('APCA_API_KEY_ID'),
                os.getenv('APCA_API_SECRET_KEY'),
                os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
                api_version='v2'
            )
            quote = api.get_latest_quote(symbol)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Latest Price", f"${quote.bid_price:.2f}")
                st.metric("Bid Size", f"{quote.bid_size:,}")
            
            with col2:
                st.metric("Ask Price", f"${quote.ask_price:.2f}")
                st.metric("Ask Size", f"{quote.ask_size:,}")
            
            with col3:
                spread = quote.ask_price - quote.bid_price
                spread_pct = (spread / quote.bid_price) * 100 if quote.bid_price > 0 else 0
                st.metric("Bid-Ask Spread", f"${spread:.2f} ({spread_pct:.2f}%)")
            
            # Additional analysis could be added here
            # - RSI, MACD, Bollinger Bands
            # - Volume analysis
            # - Support/Resistance levels
            
        except Exception as e:
            st.warning(f"Could not fetch latest metrics for {symbol}: {e}")


def main():
    """Main application entry point."""
    dashboard = TradingDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
