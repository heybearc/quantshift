"""
Coinbase Executor - Broker-Specific Strategy Execution

This module handles the Coinbase-specific implementation of strategy execution.
It bridges the gap between broker-agnostic strategies and Coinbase Advanced Trade API.
"""

import sys
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, '/opt/quantshift/packages/core/src')

from coinbase.rest import RESTClient

from quantshift_core.strategies import BaseStrategy, Signal, SignalType, Account, Position

logger = logging.getLogger(__name__)


class CoinbaseExecutor:
    """
    Coinbase-specific strategy executor.
    
    Responsibilities:
    1. Fetch market data from Coinbase
    2. Convert Coinbase account/position data to broker-agnostic format
    3. Pass data to strategy for signal generation
    4. Execute signals via Coinbase API
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        coinbase_client: RESTClient,
        symbols: Optional[List[str]] = None,
        simulated_capital: Optional[float] = None,
        risk_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Coinbase executor.
        
        Args:
            strategy: Broker-agnostic strategy instance
            coinbase_client: Coinbase REST client
            symbols: List of symbols to trade (e.g., ['BTC-PERP-INTX', 'ETH-PERP-INTX'])
            simulated_capital: Optional simulated capital for position sizing
            risk_config: Risk management configuration
        """
        self.strategy = strategy
        self.coinbase_client = coinbase_client
        self.symbols = symbols or ['BTC-PERP-INTX']
        self.simulated_capital = simulated_capital
        self.risk_config = risk_config or {}
        
        # Circuit breaker state (reset daily)
        self._daily_trades = 0
        self._daily_loss = 0.0
        self._circuit_breaker_open = False
        self._last_reset_date = datetime.utcnow().date()
        
        logger.info(
            f"CoinbaseExecutor initialized with {strategy.name} strategy for symbols: {self.symbols}"
        )
        if simulated_capital:
            logger.info(f"Using simulated capital: ${simulated_capital:,.2f}")
    
    def get_account(self) -> Account:
        """
        Fetch account information from Coinbase and convert to broker-agnostic format.
        Uses simulated capital if configured.
        """
        try:
            # For Coinbase perpetuals, we need to get futures account balance
            accounts = self.coinbase_client.get_accounts()
            
            # Use simulated capital if configured
            if self.simulated_capital:
                return Account(
                    equity=self.simulated_capital,
                    cash=self.simulated_capital,
                    buying_power=self.simulated_capital,
                    portfolio_value=self.simulated_capital,
                    positions_count=0
                )
            
            # Find USDC or USD balance for perpetuals
            total_balance = 0.0
            for account in accounts.get('accounts', []):
                if account.get('currency') in ['USDC', 'USD']:
                    available = float(account.get('available_balance', {}).get('value', 0))
                    total_balance += available
            
            # For perpetuals, buying power is typically leveraged
            leverage = 10  # Coinbase perpetuals typically offer 10x leverage
            buying_power = total_balance * leverage
            
            return Account(
                equity=total_balance,
                cash=total_balance,
                buying_power=buying_power,
                portfolio_value=total_balance,
                positions_count=0  # Will be updated when we fetch positions
            )
        except Exception as e:
            logger.error(f"Error fetching account: {e}", exc_info=True)
            raise
    
    def get_positions(self) -> List[Position]:
        """
        Fetch positions from Coinbase and convert to broker-agnostic format.
        """
        try:
            # Get perpetual futures positions
            positions_response = self.coinbase_client.get_futures_positions()
            
            positions = []
            for pos in positions_response.get('positions', []):
                product_id = pos.get('product_id')
                
                # Skip if not one of our trading symbols
                if product_id not in self.symbols:
                    continue
                
                quantity = float(pos.get('number_of_contracts', 0))
                if quantity == 0:
                    continue
                
                entry_price = float(pos.get('entry_vwap', 0))
                current_price = float(pos.get('mark_price', entry_price))
                unrealized_pl = float(pos.get('unrealized_pnl', 0))
                
                # Determine side
                side = pos.get('side', 'UNKNOWN').lower()
                
                positions.append(Position(
                    symbol=product_id,
                    quantity=quantity,
                    entry_price=entry_price,
                    current_price=current_price,
                    market_value=quantity * current_price,
                    unrealized_pl=unrealized_pl,
                    unrealized_plpc=(unrealized_pl / (entry_price * quantity)) if (entry_price * quantity) > 0 else 0,
                    side=side
                ))
            
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}", exc_info=True)
            return []
    
    def get_market_data(
        self,
        symbol: str,
        days: int = 90,
        granularity: str = '86400'  # 1 day in seconds
    ) -> pd.DataFrame:
        """
        Fetch historical market data from Coinbase.
        
        Args:
            symbol: Product ID (e.g., 'BTC-PERP-INTX')
            days: Number of days of historical data
            granularity: Candle granularity in seconds (86400 = 1 day, 3600 = 1 hour)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Calculate start and end times
            end_time = int(datetime.utcnow().timestamp())
            start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp())
            
            # Fetch candles from Coinbase
            candles = self.coinbase_client.get_candles(
                product_id=symbol,
                start=start_time,
                end=end_time,
                granularity=granularity
            )
            
            # Convert to DataFrame
            # Coinbase returns: [timestamp, low, high, open, close, volume]
            df = pd.DataFrame(
                candles.get('candles', []),
                columns=['timestamp', 'low', 'high', 'open', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by date (oldest first)
            df = df.sort_index()
            
            # Add symbol as attribute for strategy to access
            df.symbol = symbol
            
            logger.debug(f"Fetched {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}", exc_info=True)
            raise
    
    def _wait_for_fill(self, order_id: str, timeout: int = 10) -> Optional[Any]:
        """
        Poll Coinbase until an order is filled or timeout is reached.
        Returns the filled order object, or None if not filled in time.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                order = self.coinbase_client.get_order(order_id)
                status = order.get('order', {}).get('status', '').upper()
                if status in ('FILLED', 'PARTIALLY_FILLED'):
                    return order.get('order')
            except Exception:
                pass
            time.sleep(1)
        return None

    def execute_signal(self, signal: Signal) -> Optional[Dict[str, Any]]:
        """
        Execute a trading signal via Coinbase API.
        
        Args:
            signal: Trading signal to execute
            
        Returns:
            Order details if successful, None otherwise
        """
        try:
            if signal.signal_type == SignalType.HOLD:
                return None
            
            # Determine order side
            side = 'BUY' if signal.signal_type == SignalType.BUY else 'SELL'
            
            # Create market order
            order_config = {
                'product_id': signal.symbol,
                'side': side,
                'order_configuration': {
                    'market_market_ioc': {
                        'base_size': str(signal.position_size or 1)
                    }
                }
            }
            
            # Submit order
            response = self.coinbase_client.market_order(**order_config)
            order = response.get('order', {})
            order_id = order.get('order_id')
            
            logger.info(
                f"Order submitted: {side} {signal.position_size} {signal.symbol} @ market"
            )
            
            fill_price = signal.price  # fallback
            
            # For BUY signals: wait for fill then place SL/TP orders
            if signal.signal_type == SignalType.BUY:
                filled_order = self._wait_for_fill(order_id, timeout=15)
                if filled_order:
                    # Extract fill price from filled order
                    fills = filled_order.get('fills', [])
                    if fills:
                        fill_price = float(fills[0].get('price', signal.price))
                
                # Note: Coinbase perpetuals use stop-loss and take-profit via separate orders
                # This would require additional API calls to set up bracket orders
                # For now, we'll log that SL/TP would be placed
                if signal.stop_loss:
                    logger.info(f"Stop loss target: SELL {signal.position_size} {signal.symbol} @ ${signal.stop_loss:.2f}")
                    # TODO: Implement stop-loss order via Coinbase API
                
                if signal.take_profit:
                    logger.info(f"Take profit target: SELL {signal.position_size} {signal.symbol} @ ${signal.take_profit:.2f}")
                    # TODO: Implement take-profit order via Coinbase API
            
            return {
                'id': order_id,
                'symbol': signal.symbol,
                'qty': signal.position_size or 1,
                'side': side,
                'type': 'market',
                'status': order.get('status', 'UNKNOWN'),
                'fill_price': fill_price,
                'submitted_at': order.get('created_time'),
                'signal_reason': signal.reason
            }
            
        except Exception as e:
            logger.error(f"Error executing signal for {signal.symbol}: {e}", exc_info=True)
            return None
    
    def is_market_open(self) -> bool:
        """
        Check if crypto market is open.
        Crypto markets are always open (24/7).
        """
        return True
    
    def run_strategy_cycle(self) -> List[Dict[str, Any]]:
        """
        Run one complete strategy cycle:
        1. Fetch account and positions
        2. Fetch market data
        3. Generate signals
        4. Execute signals
        
        Returns:
            List of executed orders
        """
        try:
            # Check circuit breaker
            current_date = datetime.utcnow().date()
            if current_date != self._last_reset_date:
                self._daily_trades = 0
                self._daily_loss = 0.0
                self._circuit_breaker_open = False
                self._last_reset_date = current_date
            
            if self._circuit_breaker_open:
                logger.warning("Circuit breaker is open, skipping strategy cycle")
                return []
            
            # 1. Get account and positions
            account = self.get_account()
            positions = self.get_positions()
            
            # 2. Fetch market data for all symbols
            market_data = {}
            for symbol in self.symbols:
                try:
                    df = self.get_market_data(symbol)
                    market_data[symbol] = df
                except Exception as e:
                    logger.error(f"Failed to fetch data for {symbol}: {e}")
            
            if not market_data:
                logger.warning("No market data available, skipping cycle")
                return []
            
            # 3. Generate signals from strategy
            signals = self.strategy.generate_signals(market_data, account, positions)
            
            if not signals:
                logger.debug("No signals generated")
                return []
            
            # 4. Execute signals
            executed_orders = []
            for signal in signals:
                order = self.execute_signal(signal)
                if order:
                    executed_orders.append(order)
                    self._daily_trades += 1
            
            return executed_orders
            
        except Exception as e:
            logger.error(f"Error in strategy cycle: {e}", exc_info=True)
            return []
