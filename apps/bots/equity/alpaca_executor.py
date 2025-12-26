"""
Alpaca Executor - Broker-Specific Strategy Execution

This module handles the Alpaca-specific implementation of strategy execution.
It bridges the gap between broker-agnostic strategies and Alpaca's API.
"""

import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

# Add core package to path
sys.path.insert(0, '/opt/quantshift/packages/core/src')

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from quantshift_core.strategies import BaseStrategy, Signal, SignalType, Account, Position

logger = logging.getLogger(__name__)


class AlpacaExecutor:
    """
    Alpaca-specific strategy executor.
    
    Responsibilities:
    1. Fetch market data from Alpaca
    2. Convert Alpaca account/position data to broker-agnostic format
    3. Pass data to strategy for signal generation
    4. Execute signals via Alpaca API
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        alpaca_client: TradingClient,
        data_client: Optional[StockHistoricalDataClient] = None,
        symbols: Optional[List[str]] = None
    ):
        """
        Initialize Alpaca executor.
        
        Args:
            strategy: Broker-agnostic strategy instance
            alpaca_client: Alpaca trading client
            data_client: Alpaca data client (optional, will create if not provided)
            symbols: List of symbols to trade
        """
        self.strategy = strategy
        self.alpaca_client = alpaca_client
        self.data_client = data_client
        self.symbols = symbols or ['SPY']
        
        logger.info(
            f"AlpacaExecutor initialized with {strategy.name} strategy for symbols: {self.symbols}"
        )
    
    def get_account(self) -> Account:
        """
        Fetch account information from Alpaca and convert to broker-agnostic format.
        """
        try:
            alpaca_account = self.alpaca_client.get_account()
            
            return Account(
                equity=float(alpaca_account.equity),
                cash=float(alpaca_account.cash),
                buying_power=float(alpaca_account.buying_power),
                portfolio_value=float(alpaca_account.portfolio_value),
                positions_count=0  # Will be updated when we fetch positions
            )
        except Exception as e:
            logger.error(f"Error fetching account: {e}", exc_info=True)
            raise
    
    def get_positions(self) -> List[Position]:
        """
        Fetch positions from Alpaca and convert to broker-agnostic format.
        """
        try:
            alpaca_positions = self.alpaca_client.get_all_positions()
            
            positions = []
            for pos in alpaca_positions:
                positions.append(Position(
                    symbol=pos.symbol,
                    quantity=float(pos.qty),
                    entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    market_value=float(pos.market_value),
                    unrealized_pl=float(pos.unrealized_pl),
                    unrealized_plpc=float(pos.unrealized_plpc),
                    side='long' if float(pos.qty) > 0 else 'short'
                ))
            
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}", exc_info=True)
            return []
    
    def get_market_data(
        self,
        symbol: str,
        days: int = 90,
        timeframe: TimeFrame = TimeFrame.Day
    ) -> pd.DataFrame:
        """
        Fetch historical market data from Alpaca.
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data
            timeframe: Data timeframe (Day, Hour, Minute)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Create data client if not provided
            if not self.data_client:
                from alpaca.data.historical import StockHistoricalDataClient
                import os
                api_key = os.getenv('APCA_API_KEY_ID')
                secret_key = os.getenv('APCA_API_SECRET_KEY')
                self.data_client = StockHistoricalDataClient(api_key, secret_key)
            
            # Fetch data using data client
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=datetime.utcnow() - timedelta(days=days),
                end=datetime.utcnow()
            )
            bars = self.data_client.get_stock_bars(request)
            df = bars.df
            
            # Normalize DataFrame structure
            if hasattr(df.index, 'get_level_values'):
                if 'symbol' in df.index.names:
                    df = df.xs(symbol, level='symbol')
            
            # Ensure we have the required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # Sort by date
            df = df.sort_index()
            
            # Add symbol as attribute for strategy to access
            df.symbol = symbol
            
            logger.debug(f"Fetched {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}", exc_info=True)
            raise
    
    def execute_signal(self, signal: Signal) -> Optional[Dict[str, Any]]:
        """
        Execute a trading signal via Alpaca API.
        
        Args:
            signal: Trading signal to execute
            
        Returns:
            Order details if successful, None otherwise
        """
        try:
            if signal.signal_type == SignalType.HOLD:
                return None
            
            # Determine order side
            side = OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL
            
            # Create market order
            order_request = MarketOrderRequest(
                symbol=signal.symbol,
                qty=signal.position_size or 1,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit order
            order = self.alpaca_client.submit_order(order_request)
            
            logger.info(
                f"Order submitted: {side.value} {signal.position_size} {signal.symbol} @ market"
            )
            
            # Submit stop loss if provided
            if signal.stop_loss and signal.signal_type == SignalType.BUY:
                try:
                    stop_order = MarketOrderRequest(
                        symbol=signal.symbol,
                        qty=signal.position_size,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.GTC,
                        stop_price=signal.stop_loss
                    )
                    self.alpaca_client.submit_order(stop_order)
                    logger.info(f"Stop loss order placed at ${signal.stop_loss:.2f}")
                except Exception as e:
                    logger.warning(f"Failed to place stop loss: {e}")
            
            # Submit take profit if provided
            if signal.take_profit and signal.signal_type == SignalType.BUY:
                try:
                    tp_order = LimitOrderRequest(
                        symbol=signal.symbol,
                        qty=signal.position_size,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.GTC,
                        limit_price=signal.take_profit
                    )
                    self.alpaca_client.submit_order(tp_order)
                    logger.info(f"Take profit order placed at ${signal.take_profit:.2f}")
                except Exception as e:
                    logger.warning(f"Failed to place take profit: {e}")
            
            return {
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'status': order.status.value,
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                'signal_reason': signal.reason
            }
            
        except Exception as e:
            logger.error(f"Error executing signal for {signal.symbol}: {e}", exc_info=True)
            return None
    
    def run_strategy_cycle(self) -> Dict[str, Any]:
        """
        Run one complete strategy cycle:
        1. Fetch account and positions
        2. Fetch market data for all symbols
        3. Generate signals from strategy
        4. Execute valid signals
        
        Returns:
            Summary of cycle execution
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbols_checked': [],
            'signals_generated': [],
            'orders_executed': [],
            'errors': []
        }
        
        try:
            # Get account and positions
            account = self.get_account()
            positions = self.get_positions()
            account.positions_count = len(positions)
            
            logger.info(
                f"Strategy cycle started - Account: ${account.equity:.2f}, "
                f"Positions: {len(positions)}"
            )
            
            # Check each symbol
            for symbol in self.symbols:
                try:
                    results['symbols_checked'].append(symbol)
                    
                    # Fetch market data
                    market_data = self.get_market_data(symbol, days=90)
                    
                    # Generate signals
                    signals = self.strategy.generate_signals(
                        market_data=market_data,
                        account=account,
                        positions=positions
                    )
                    
                    # Execute signals
                    for signal in signals:
                        results['signals_generated'].append({
                            'symbol': signal.symbol,
                            'type': signal.signal_type.value,
                            'price': signal.price,
                            'reason': signal.reason
                        })
                        
                        # Execute the signal
                        order = self.execute_signal(signal)
                        if order:
                            results['orders_executed'].append(order)
                    
                except Exception as e:
                    error_msg = f"Error processing {symbol}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results['errors'].append(error_msg)
            
            logger.info(
                f"Strategy cycle completed - Signals: {len(results['signals_generated'])}, "
                f"Orders: {len(results['orders_executed'])}"
            )
            
        except Exception as e:
            error_msg = f"Error in strategy cycle: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        return results
    
    def get_strategy_state(self) -> Dict[str, Any]:
        """
        Get current strategy state for monitoring.
        """
        return {
            'strategy_name': self.strategy.name,
            'strategy_config': self.strategy.config,
            'symbols': self.symbols,
            'last_update': datetime.utcnow().isoformat()
        }
