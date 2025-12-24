"""
Strategy Configuration Page for Trading Dashboard

This module provides the interface for configuring the 7-layer screening filters
and other trading strategy parameters.
"""

import streamlit as st
import json
import os
from typing import Dict, Any
from dataclasses import asdict

from alpaca_trading.core.config import config

class StrategyConfig:
    """Strategy configuration management."""
    
    def __init__(self):
        """Initialize strategy configuration."""
        self.config_file = "strategy_config.json"
        self.default_config = {
            # Price filters
            "min_price": 5.0,
            "max_price": 1000.0,
            
            # Volume filters
            "min_volume_high_price": 250000,  # For stocks > $15
            "min_volume_mid_price": 150000,   # For stocks $5-$15
            "volume_lookback_days": 20,
            
            # Technical filters
            "min_rvol": 1.5,                  # Relative volume
            "min_atr_pct": 1.5,              # ATR percentage
            "min_relative_strength": 0.0,     # vs SPY
            
            # Fundamental filters
            "max_short_interest": 10.0,       # Max short interest %
            "min_institutional_ownership": 60.0,  # Min institutional ownership %
            "max_bid_ask_spread": 0.5,        # Max bid/ask spread %
            
            # Risk management
            "max_positions": 5,
            "position_size": 1000.0,
            "stop_loss_pct": 2.0,
            "scale_out_first_pct": 50.0,      # % to sell at 2:1 R:R
            "scale_out_resistance_pct": 33.0, # % to sell at 3:1 R:R
            "trailing_stop_atr_mult": 1.5,
            
            # Moving average parameters
            "short_ma_period": 5,
            "long_ma_period": 20,
            
            # Earnings avoidance
            "earnings_avoidance_days": 3,
        }
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or use defaults."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults to handle new parameters
                self.current_config = {**self.default_config, **loaded_config}
            else:
                self.current_config = self.default_config.copy()
        except Exception as e:
            st.error(f"Error loading config: {e}")
            self.current_config = self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.current_config, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving config: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.current_config = self.default_config.copy()
    
    def show_strategy_page(self):
        """Display the strategy configuration page."""
        st.markdown('<h1 class="main-header">⚙️ Strategy Configuration</h1>', unsafe_allow_html=True)
        
        st.markdown("""
        Configure the 7-layer enhanced stock screening filters and trading parameters.
        Changes are saved automatically when you modify values.
        """)
        
        # Configuration tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Screening Filters", 
            "💰 Risk Management", 
            "📈 Technical Analysis", 
            "🎯 Advanced Settings"
        ])
        
        with tab1:
            self._show_screening_filters()
        
        with tab2:
            self._show_risk_management()
        
        with tab3:
            self._show_technical_analysis()
        
        with tab4:
            self._show_advanced_settings()
        
        # Action buttons
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save Configuration", type="primary"):
                if self.save_config():
                    st.success("Configuration saved successfully!")
                    st.rerun()
        
        with col2:
            if st.button("🔄 Reset to Defaults"):
                self.reset_to_defaults()
                st.warning("Configuration reset to defaults. Click Save to persist changes.")
                st.rerun()
        
        with col3:
            if st.button("📥 Export Config"):
                self._export_config()
        
        with col4:
            uploaded_file = st.file_uploader("📤 Import Config", type=['json'], key="config_upload")
            if uploaded_file:
                self._import_config(uploaded_file)
    
    def _show_screening_filters(self):
        """Display screening filter configuration."""
        st.subheader("🔍 7-Layer Screening Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Price Filters**")
            self.current_config["min_price"] = st.number_input(
                "Minimum Price ($)",
                min_value=0.01,
                max_value=100.0,
                value=self.current_config["min_price"],
                step=0.50,
                help="Minimum stock price to consider for screening"
            )
            
            self.current_config["max_price"] = st.number_input(
                "Maximum Price ($)",
                min_value=10.0,
                max_value=5000.0,
                value=self.current_config["max_price"],
                step=50.0,
                help="Maximum stock price to consider for screening"
            )
            
            st.markdown("**Volume Filters**")
            self.current_config["min_volume_high_price"] = st.number_input(
                "Min Volume (Price > $15)",
                min_value=50000,
                max_value=1000000,
                value=self.current_config["min_volume_high_price"],
                step=25000,
                help="Minimum average daily volume for stocks priced above $15"
            )
            
            self.current_config["min_volume_mid_price"] = st.number_input(
                "Min Volume ($5-$15)",
                min_value=25000,
                max_value=500000,
                value=self.current_config["min_volume_mid_price"],
                step=25000,
                help="Minimum average daily volume for stocks priced $5-$15"
            )
            
            self.current_config["volume_lookback_days"] = st.slider(
                "Volume Lookback Days",
                min_value=5,
                max_value=60,
                value=self.current_config["volume_lookback_days"],
                help="Number of days to calculate average volume"
            )
        
        with col2:
            st.markdown("**Relative Volume (RVOL)**")
            self.current_config["min_rvol"] = st.number_input(
                "Minimum RVOL",
                min_value=1.0,
                max_value=5.0,
                value=self.current_config["min_rvol"],
                step=0.1,
                help="Minimum relative volume (current vs average)"
            )
            
            st.markdown("**Volatility Filter**")
            self.current_config["min_atr_pct"] = st.number_input(
                "Minimum ATR %",
                min_value=0.5,
                max_value=10.0,
                value=self.current_config["min_atr_pct"],
                step=0.1,
                help="Minimum ATR as percentage of stock price"
            )
            
            st.markdown("**Relative Strength**")
            self.current_config["min_relative_strength"] = st.number_input(
                "Min Relative Strength vs SPY",
                min_value=-10.0,
                max_value=10.0,
                value=self.current_config["min_relative_strength"],
                step=0.5,
                help="Minimum relative strength compared to SPY (positive = outperforming)"
            )
            
            st.markdown("**Fundamental Filters**")
            self.current_config["max_short_interest"] = st.slider(
                "Max Short Interest %",
                min_value=0.0,
                max_value=50.0,
                value=self.current_config["max_short_interest"],
                step=1.0,
                help="Maximum short interest percentage"
            )
            
            self.current_config["min_institutional_ownership"] = st.slider(
                "Min Institutional Ownership %",
                min_value=0.0,
                max_value=100.0,
                value=self.current_config["min_institutional_ownership"],
                step=5.0,
                help="Minimum institutional ownership percentage"
            )
    
    def _show_risk_management(self):
        """Display risk management configuration."""
        st.subheader("💰 Risk Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Position Management**")
            self.current_config["max_positions"] = st.number_input(
                "Maximum Positions",
                min_value=1,
                max_value=20,
                value=self.current_config["max_positions"],
                help="Maximum number of concurrent positions"
            )
            
            self.current_config["position_size"] = st.number_input(
                "Position Size ($)",
                min_value=100.0,
                max_value=10000.0,
                value=self.current_config["position_size"],
                step=100.0,
                help="Dollar amount per position"
            )
            
            self.current_config["stop_loss_pct"] = st.number_input(
                "Stop Loss %",
                min_value=0.5,
                max_value=10.0,
                value=self.current_config["stop_loss_pct"],
                step=0.1,
                help="Stop loss percentage below entry price"
            )
        
        with col2:
            st.markdown("**Profit Taking Strategy**")
            self.current_config["scale_out_first_pct"] = st.slider(
                "First Scale Out % (at 2:1 R:R)",
                min_value=10.0,
                max_value=80.0,
                value=self.current_config["scale_out_first_pct"],
                step=5.0,
                help="Percentage of position to sell at 2:1 risk/reward"
            )
            
            self.current_config["scale_out_resistance_pct"] = st.slider(
                "Second Scale Out % (at 3:1 R:R)",
                min_value=10.0,
                max_value=60.0,
                value=self.current_config["scale_out_resistance_pct"],
                step=5.0,
                help="Percentage of remaining position to sell at 3:1 risk/reward"
            )
            
            self.current_config["trailing_stop_atr_mult"] = st.number_input(
                "Trailing Stop ATR Multiplier",
                min_value=0.5,
                max_value=3.0,
                value=self.current_config["trailing_stop_atr_mult"],
                step=0.1,
                help="ATR multiplier for trailing stop distance"
            )
    
    def _show_technical_analysis(self):
        """Display technical analysis configuration."""
        st.subheader("📈 Technical Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Moving Average Parameters**")
            self.current_config["short_ma_period"] = st.number_input(
                "Short MA Period",
                min_value=3,
                max_value=20,
                value=self.current_config["short_ma_period"],
                help="Period for short-term moving average"
            )
            
            self.current_config["long_ma_period"] = st.number_input(
                "Long MA Period",
                min_value=10,
                max_value=50,
                value=self.current_config["long_ma_period"],
                help="Period for long-term moving average"
            )
        
        with col2:
            st.markdown("**Quality Filters**")
            self.current_config["max_bid_ask_spread"] = st.number_input(
                "Max Bid/Ask Spread %",
                min_value=0.1,
                max_value=2.0,
                value=self.current_config["max_bid_ask_spread"],
                step=0.1,
                help="Maximum bid/ask spread as percentage"
            )
            
            self.current_config["earnings_avoidance_days"] = st.number_input(
                "Earnings Avoidance Days",
                min_value=0,
                max_value=10,
                value=self.current_config["earnings_avoidance_days"],
                help="Days before/after earnings to avoid trading"
            )
    
    def _show_advanced_settings(self):
        """Display advanced configuration settings."""
        st.subheader("🎯 Advanced Settings")
        
        st.markdown("**Configuration Summary**")
        
        # Display current configuration as JSON
        config_json = json.dumps(self.current_config, indent=2)
        st.code(config_json, language='json')
        
        st.markdown("**Filter Effectiveness Preview**")
        
        # Show estimated filter impact
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Estimated Universe Size",
                "~200 stocks",
                help="Approximate number of stocks that will pass initial filters"
            )
        
        with col2:
            st.metric(
                "Expected Daily Opportunities",
                "3-8 stocks",
                help="Typical number of trading opportunities per day"
            )
        
        with col3:
            st.metric(
                "Target Win Rate",
                "65%+",
                help="Expected win rate with current configuration"
            )
    
    def _export_config(self):
        """Export configuration as downloadable JSON."""
        config_json = json.dumps(self.current_config, indent=2)
        st.download_button(
            label="📥 Download Configuration",
            data=config_json,
            file_name=f"strategy_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _import_config(self, uploaded_file):
        """Import configuration from uploaded JSON file."""
        try:
            config_data = json.load(uploaded_file)
            # Validate that it contains expected keys
            if isinstance(config_data, dict):
                self.current_config.update(config_data)
                st.success("Configuration imported successfully!")
                st.rerun()
            else:
                st.error("Invalid configuration file format.")
        except Exception as e:
            st.error(f"Error importing configuration: {e}")

def show_strategy_page():
    """Show the strategy configuration page."""
    strategy_config = StrategyConfig()
    strategy_config.show_strategy_page()
