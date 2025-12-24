"""
Stock Universe Management Page for Trading Dashboard

This module provides the interface for managing custom stock lists
and integrating them with the screening universe.
"""

import streamlit as st
import pandas as pd
import json
import os
from typing import List, Set, Dict, Any
from datetime import datetime
import re

class StockUniverseManager:
    """Stock universe management class."""
    
    def __init__(self):
        """Initialize stock universe manager."""
        self.manual_stocks_file = "manual_stocks.json"
        self.stock_lists_dir = "stock_lists"
        self.ensure_directories()
        self.load_manual_stocks()
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.stock_lists_dir, exist_ok=True)
    
    def load_manual_stocks(self):
        """Load manual stocks from file."""
        try:
            if os.path.exists(self.manual_stocks_file):
                with open(self.manual_stocks_file, 'r') as f:
                    data = json.load(f)
                    self.manual_stocks = set(data.get('stocks', []))
            else:
                self.manual_stocks = set()
        except Exception as e:
            st.error(f"Error loading manual stocks: {e}")
            self.manual_stocks = set()
    
    def save_manual_stocks(self):
        """Save manual stocks to file."""
        try:
            data = {
                'stocks': sorted(list(self.manual_stocks)),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.manual_stocks_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving manual stocks: {e}")
            return False
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format."""
        # Basic validation - alphanumeric, 1-5 characters
        pattern = r'^[A-Z]{1,5}$'
        return bool(re.match(pattern, symbol.upper()))
    
    def show_stock_universe_page(self):
        """Display the stock universe management page."""
        st.markdown('<h1 class="main-header">📋 Stock Universe Management</h1>', unsafe_allow_html=True)
        
        st.markdown("""
        Manage your custom stock lists and integrate them with the screening universe.
        Manual stocks are added to the curated universe for screening.
        """)
        
        # Tabs for different management functions
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Manual Stock Entry",
            "📤 Upload Stock Lists", 
            "📊 Current Universe",
            "📁 Saved Lists"
        ])
        
        with tab1:
            self._show_manual_entry()
        
        with tab2:
            self._show_file_upload()
        
        with tab3:
            self._show_current_universe()
        
        with tab4:
            self._show_saved_lists()
    
    def _show_manual_entry(self):
        """Show manual stock entry interface."""
        st.subheader("📝 Manual Stock Entry")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Single stock entry
            st.markdown("**Add Individual Stock**")
            new_symbol = st.text_input(
                "Stock Symbol",
                placeholder="e.g., AAPL",
                help="Enter a valid stock symbol (1-5 letters)"
            ).upper()
            
            if st.button("➕ Add Stock"):
                if new_symbol and self.validate_symbol(new_symbol):
                    if new_symbol not in self.manual_stocks:
                        self.manual_stocks.add(new_symbol)
                        if self.save_manual_stocks():
                            st.success(f"Added {new_symbol} to manual stocks!")
                            st.rerun()
                    else:
                        st.warning(f"{new_symbol} is already in the manual stocks list.")
                else:
                    st.error("Please enter a valid stock symbol (1-5 letters, A-Z).")
            
            # Bulk entry
            st.markdown("**Bulk Entry**")
            bulk_symbols = st.text_area(
                "Multiple Symbols",
                placeholder="Enter symbols separated by commas or new lines:\nAAPL, MSFT, GOOGL\nTSLA\nNVDA",
                help="Enter multiple symbols separated by commas, spaces, or new lines"
            )
            
            if st.button("➕ Add Multiple Stocks"):
                if bulk_symbols:
                    # Parse symbols from text
                    symbols = re.findall(r'[A-Z]{1,5}', bulk_symbols.upper())
                    valid_symbols = [s for s in symbols if self.validate_symbol(s)]
                    new_symbols = [s for s in valid_symbols if s not in self.manual_stocks]
                    
                    if new_symbols:
                        self.manual_stocks.update(new_symbols)
                        if self.save_manual_stocks():
                            st.success(f"Added {len(new_symbols)} new stocks: {', '.join(sorted(new_symbols))}")
                            st.rerun()
                    else:
                        st.warning("No new valid symbols found.")
        
        with col2:
            # Current manual stocks
            st.markdown("**Current Manual Stocks**")
            if self.manual_stocks:
                manual_list = sorted(list(self.manual_stocks))
                
                # Display as removable chips
                for symbol in manual_list:
                    col_symbol, col_remove = st.columns([3, 1])
                    with col_symbol:
                        st.text(symbol)
                    with col_remove:
                        if st.button("❌", key=f"remove_{symbol}"):
                            self.manual_stocks.remove(symbol)
                            if self.save_manual_stocks():
                                st.success(f"Removed {symbol}")
                                st.rerun()
                
                st.divider()
                
                # Bulk actions
                if st.button("🗑️ Clear All Manual Stocks"):
                    self.manual_stocks.clear()
                    if self.save_manual_stocks():
                        st.success("Cleared all manual stocks!")
                        st.rerun()
                
                # Export manual stocks
                if st.button("📥 Export Manual Stocks"):
                    self._export_stock_list(list(self.manual_stocks), "manual_stocks")
            else:
                st.info("No manual stocks added yet.")
    
    def _show_file_upload(self):
        """Show file upload interface."""
        st.subheader("📤 Upload Stock Lists")
        
        st.markdown("""
        Upload stock lists from various file formats:
        - **CSV**: One symbol per row or comma-separated
        - **TXT**: One symbol per line
        - **JSON**: Array of symbols or object with 'stocks' key
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'txt', 'json'],
            help="Upload a file containing stock symbols"
        )
        
        if uploaded_file is not None:
            try:
                file_type = uploaded_file.name.split('.')[-1].lower()
                symbols = self._parse_uploaded_file(uploaded_file, file_type)
                
                if symbols:
                    st.success(f"Found {len(symbols)} symbols in file:")
                    
                    # Preview symbols
                    preview_df = pd.DataFrame({
                        'Symbol': sorted(symbols),
                        'Status': ['New' if s not in self.manual_stocks else 'Existing' 
                                 for s in sorted(symbols)]
                    })
                    st.dataframe(preview_df, use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("✅ Add to Manual Stocks"):
                            new_symbols = [s for s in symbols if s not in self.manual_stocks]
                            self.manual_stocks.update(symbols)
                            if self.save_manual_stocks():
                                st.success(f"Added {len(new_symbols)} new symbols!")
                                st.rerun()
                    
                    with col2:
                        if st.button("💾 Save as Named List"):
                            list_name = st.text_input("List Name", value=uploaded_file.name.split('.')[0])
                            if list_name:
                                self._save_stock_list(symbols, list_name)
                else:
                    st.error("No valid symbols found in file.")
            except Exception as e:
                st.error(f"Error processing file: {e}")
    
    def _show_current_universe(self):
        """Show current screening universe."""
        st.subheader("📊 Current Screening Universe")
        
        # Get actual curated universe from screener (not just preview)
        try:
            from alpaca_trading.scripts.screener import StockScreener
            import alpaca_trade_api as tradeapi
            from alpaca_trading.core.config import config
            
            # Initialize API and screener to get actual universe
            api = tradeapi.REST(
                config.api_key,
                config.api_secret,
                base_url=config.base_url,
                api_version='v2'
            )
            screener = StockScreener(api, manual_stocks=list(self.manual_stocks))
            actual_curated_universe = screener.get_curated_stock_universe()
            
            # Since we now only use manual stocks, the universe IS the manual stocks
            total_universe_count = len(actual_curated_universe)
            curated_count = 0  # No curated stocks anymore, only manual
            
            st.success(f"✅ Connected to live screener - showing actual universe counts")
            
        except Exception as e:
            # Fallback to manual stocks only
            total_universe_count = len(self.manual_stocks)
            curated_count = 0
            st.warning(f"⚠️ Using manual stocks only (screener unavailable): {str(e)[:100]}...")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Universe Statistics**")
            st.metric("Manual Stocks", len(self.manual_stocks), help="All stocks are manually curated")
            st.metric("Total Universe", total_universe_count, help="Same as manual stocks (no hardcoded sets)")
            st.metric("Screening Coverage", "100%", help="All stocks in universe are processed")
        
        with col2:
            st.markdown("**Manual Stocks List**")
            if self.manual_stocks:
                manual_df = pd.DataFrame({
                    'Symbol': sorted(list(self.manual_stocks)),
                    'Status': ['Active' for _ in sorted(list(self.manual_stocks))]
                })
                st.dataframe(manual_df, use_container_width=True)
            else:
                st.info("No manual stocks to display. Add stocks using the form above.")
        
        # Combined universe preview (now just manual stocks)
        st.markdown("**Universe Preview**")
        
        if self.manual_stocks:
            combined_universe = sorted(list(self.manual_stocks))
            st.info(f"📊 Displaying complete universe ({len(combined_universe)} stocks)")
            
            # Show in columns for better display
            display_count = min(100, len(combined_universe))
            cols = st.columns(4)
            for i, symbol in enumerate(combined_universe[:display_count]):
                with cols[i % 4]:
                    st.text(f"🔵 {symbol}")
            
            if len(combined_universe) > 100:
                st.info(f"Showing first 100 of {len(combined_universe)} symbols. All stocks are manually curated.")
        else:
            st.info("No stocks in universe. Add manual stocks to get started.")
            
            # Add screening transparency info
            st.markdown("---")
            st.markdown("**📈 Screening Process Info**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"🎯 **Universe Size**: {len(combined_universe)} stocks total")
            with col_b:
                st.info(f"🔍 **Screening Coverage**: 100% of universe processed (no limits)")
    
    def _show_saved_lists(self):
        """Show saved stock lists management."""
        st.subheader("📁 Saved Stock Lists")
        
        # List saved files
        saved_lists = self._get_saved_lists()
        
        if saved_lists:
            for list_name in saved_lists:
                with st.expander(f"📄 {list_name}"):
                    try:
                        list_path = os.path.join(self.stock_lists_dir, f"{list_name}.json")
                        with open(list_path, 'r') as f:
                            list_data = json.load(f)
                        
                        symbols = list_data.get('stocks', [])
                        created = list_data.get('created', 'Unknown')
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.text(f"Symbols: {len(symbols)}")
                            st.text(f"Created: {created}")
                            
                            # Show first few symbols
                            preview = ', '.join(symbols[:10])
                            if len(symbols) > 10:
                                preview += f" ... (+{len(symbols) - 10} more)"
                            st.text(f"Preview: {preview}")
                        
                        with col2:
                            if st.button("📥 Load to Manual", key=f"load_{list_name}"):
                                self.manual_stocks.update(symbols)
                                if self.save_manual_stocks():
                                    st.success(f"Loaded {list_name} to manual stocks!")
                                    st.rerun()
                        
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{list_name}"):
                                os.remove(list_path)
                                st.success(f"Deleted {list_name}")
                                st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error loading {list_name}: {e}")
        else:
            st.info("No saved stock lists found.")
        
        # Create new list from manual stocks
        st.divider()
        if self.manual_stocks:
            st.markdown("**Save Current Manual Stocks**")
            new_list_name = st.text_input("List Name", placeholder="My Custom List")
            if st.button("💾 Save Current Manual Stocks as List"):
                if new_list_name:
                    self._save_stock_list(list(self.manual_stocks), new_list_name)
                    st.success(f"Saved manual stocks as '{new_list_name}'!")
                    st.rerun()
                else:
                    st.error("Please enter a list name.")
    
    def _parse_uploaded_file(self, uploaded_file, file_type: str) -> List[str]:
        """Parse uploaded file and extract stock symbols."""
        symbols = []
        
        if file_type == 'csv':
            df = pd.read_csv(uploaded_file)
            # Try to find symbol column
            for col in df.columns:
                if 'symbol' in col.lower() or 'ticker' in col.lower():
                    symbols.extend(df[col].astype(str).str.upper().tolist())
                    break
            else:
                # If no symbol column found, use first column
                symbols.extend(df.iloc[:, 0].astype(str).str.upper().tolist())
        
        elif file_type == 'txt':
            content = uploaded_file.read().decode('utf-8')
            # Extract symbols using regex
            symbols = re.findall(r'[A-Z]{1,5}', content.upper())
        
        elif file_type == 'json':
            data = json.load(uploaded_file)
            if isinstance(data, list):
                symbols = [str(s).upper() for s in data]
            elif isinstance(data, dict) and 'stocks' in data:
                symbols = [str(s).upper() for s in data['stocks']]
        
        # Validate and filter symbols
        valid_symbols = [s for s in symbols if self.validate_symbol(s)]
        return list(set(valid_symbols))  # Remove duplicates
    
    def _save_stock_list(self, symbols: List[str], list_name: str):
        """Save a stock list to file."""
        try:
            list_data = {
                'name': list_name,
                'stocks': sorted(symbols),
                'created': datetime.now().isoformat(),
                'count': len(symbols)
            }
            
            filename = f"{list_name.replace(' ', '_').lower()}.json"
            filepath = os.path.join(self.stock_lists_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(list_data, f, indent=2)
            
            st.success(f"Saved stock list '{list_name}' with {len(symbols)} symbols!")
            
        except Exception as e:
            st.error(f"Error saving stock list: {e}")
    
    def _export_stock_list(self, symbols: List[str], filename: str):
        """Export stock list as downloadable file."""
        list_data = {
            'stocks': sorted(symbols),
            'exported': datetime.now().isoformat(),
            'count': len(symbols)
        }
        
        json_data = json.dumps(list_data, indent=2)
        
        st.download_button(
            label="📥 Download Stock List",
            data=json_data,
            file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _get_saved_lists(self) -> List[str]:
        """Get list of saved stock lists."""
        try:
            files = os.listdir(self.stock_lists_dir)
            return [f.replace('.json', '') for f in files if f.endswith('.json')]
        except:
            return []
    
    def _get_curated_universe_preview(self) -> List[str]:
        """Get a preview of the curated universe (simplified version)."""
        # This is a simplified version - in practice, you'd get this from the screener
        return [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA',
            'NFLX', 'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'PYPL', 'UBER',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA', 'AXP',
            'JNJ', 'PFE', 'UNH', 'ABBV', 'TMO', 'DHR', 'BMY', 'MRK',
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PXD', 'MPC', 'VLO',
            'WMT', 'HD', 'PG', 'KO', 'PEP', 'COST', 'NKE', 'SBUX'
        ]

def show_stock_universe_page():
    """Show the stock universe management page."""
    universe_manager = StockUniverseManager()
    universe_manager.show_stock_universe_page()
