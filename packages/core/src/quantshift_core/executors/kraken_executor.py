"""
Kraken Executor - Margin Trading & Shorting Support

This module handles Kraken-specific implementation with margin trading and short positions.
Supports both spot margin (up to 5x) and futures (up to 50x).
"""

import sys
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, '/opt/quantshift/packages/core/src')

from quantshift_core.strategies import BaseStrategy, Signal, SignalType, Account, Position
from quantshift_core.risk import PositionLimits

logger = logging.getLogger(__name__)


class KrakenExecutor:
    """
    Kraken-specific strategy executor with margin trading support.
    
    Responsibilities:
    1. Fetch market data from Kraken
    2. Convert Kraken account/position data to broker-agnostic format
    3. Pass data to strategy for signal generation
    4. Execute signals via Kraken API (spot margin + futures)
    5. Handle margin levels and liquidation monitoring
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        kraken_api_key: str,
        kraken_api_secret: str,
        symbols: Optional[List[str]] = None,
        simulated_capital: Optional[float] = None,
        risk_config: Optional[Dict[str, Any]] = None,
        use_dynamic_symbols: bool = False,
        symbol_universe_config: Optional[Dict[str, Any]] = None,
        max_leverage: float = 2.0
    ):
        """
        Initialize Kraken executor.
        
        Args:
            strategy: Broker-agnostic strategy instance
            kraken_api_key: Kraken API key
            kraken_api_secret: Kraken API secret
            symbols: List of symbols to trade (if not using dynamic)
            simulated_capital: Optional simulated capital for position sizing
            risk_config: Risk management configuration
            use_dynamic_symbols: If True, fetch symbols dynamically
            symbol_universe_config: Config for dynamic symbol fetching
            max_leverage: Maximum leverage to use (default 2.0x, max 5.0x for margin)
        """
        self.strategy = strategy
        self.simulated_capital = simulated_capital
        self.risk_config = risk_config or {}
        self.max_leverage = min(max_leverage, 5.0)  # Cap at 5x for safety
        
        # Initialize Kraken API client
        try:
            import krakenex
            self.kraken_client = krakenex.API(key=kraken_api_key, secret=kraken_api_secret)
            logger.info("Kraken API client initialized")
        except ImportError:
            logger.error("krakenex library not installed. Install with: pip install krakenex")
            raise
        
        # Initialize hard position limits
        self.position_limits = PositionLimits()
        
        # Initialize circuit breaker tracking
        self._daily_trades = 0
        self._daily_loss = 0.0
        self._circuit_breaker_open = False
        self._last_reset_date = datetime.utcnow().date()
        
        # Initialize symbol universe
        if use_dynamic_symbols:
            from quantshift_core.symbol_universe import SymbolUniverse
            self.symbol_universe = SymbolUniverse('kraken', symbol_universe_config, self.kraken_client)
            self.symbols = None
            logger.info("Dynamic symbol universe enabled (lazy loading)")
        else:
            self.symbol_universe = None
            self.symbols = symbols or ['XXBTZUSD', 'XETHZUSD']  # BTC-USD, ETH-USD in Kraken format
        
        symbol_info = "dynamic (lazy loading)" if use_dynamic_symbols else f"{len(self.symbols)} symbols"
        logger.info(
            f"KrakenExecutor initialized with {strategy.name} strategy for {symbol_info}, max_leverage={self.max_leverage}x"
        )
        if simulated_capital:
            logger.info(f"Using simulated capital: ${simulated_capital:,.2f}")
    
    def _ensure_symbols_loaded(self) -> None:
        """Lazy load symbols on first use if using dynamic symbols."""
        if self.use_dynamic_symbols and self.symbols is None:
            self.symbols = self.symbol_universe.get_symbols()
            logger.info(f"Symbols lazy loaded: {len(self.symbols)} symbols")
    
    def get_account(self) -> Account:
        """
        Get account information from Kraken.
        
        Returns:
            Account object with balance and margin info
        """
        try:
            # Get account balance
            balance_response = self.kraken_client.query_private('Balance')
            
            if balance_response.get('error'):
                logger.error(f"Kraken balance error: {balance_response['error']}")
                raise Exception(f"Kraken API error: {balance_response['error']}")
            
            balances = balance_response.get('result', {})
            
            # Get USD balance (ZUSD in Kraken)
            usd_balance = float(balances.get('ZUSD', 0))
            
            # Get trade balance for margin info
            trade_balance_response = self.kraken_client.query_private('TradeBalance', {'asset': 'ZUSD'})
            
            if trade_balance_response.get('error'):
                logger.warning(f"Kraken trade balance error: {trade_balance_response['error']}")
                trade_balance = {}
            else:
                trade_balance = trade_balance_response.get('result', {})
            
            # Extract margin info
            equity = float(trade_balance.get('eb', usd_balance))  # Equivalent balance
            margin_used = float(trade_balance.get('m', 0))  # Margin amount of open positions
            free_margin = float(trade_balance.get('mf', equity))  # Free margin
            
            return Account(
                equity=equity,
                cash=usd_balance,
                buying_power=free_margin * self.max_leverage,  # Available margin * leverage
                margin_used=margin_used,
                maintenance_margin=margin_used * 0.4  # Kraken uses ~40% maintenance margin
            )
            
        except Exception as e:
            logger.error(f"Error fetching Kraken account: {e}", exc_info=True)
            raise
    
    def get_positions(self) -> List[Position]:
        """
        Get open positions from Kraken.
        
        Returns:
            List of Position objects
        """
        try:
            # Get open positions
            positions_response = self.kraken_client.query_private('OpenPositions')
            
            if positions_response.get('error'):
                logger.error(f"Kraken positions error: {positions_response['error']}")
                return []
            
            kraken_positions = positions_response.get('result', {})
            
            positions = []
            for position_id, pos_data in kraken_positions.items():
                try:
                    symbol = pos_data.get('pair')
                    quantity = float(pos_data.get('vol', 0))
                    entry_price = float(pos_data.get('cost', 0)) / quantity if quantity > 0 else 0
                    current_price = float(pos_data.get('value', 0)) / quantity if quantity > 0 else 0
                    
                    # Calculate P&L
                    unrealized_pl = (current_price - entry_price) * quantity
                    
                    # Determine if short (negative volume in Kraken means short)
                    is_short = pos_data.get('type') == 'sell'
                    if is_short:
                        quantity = -abs(quantity)
                        unrealized_pl = -unrealized_pl
                    
                    position = Position(
                        symbol=symbol,
                        quantity=quantity,
                        entry_price=entry_price,
                        current_price=current_price,
                        unrealized_pl=unrealized_pl,
                        side='short' if is_short else 'long'
                    )
                    positions.append(position)
                    
                except Exception as e:
                    logger.error(f"Error parsing Kraken position {position_id}: {e}")
                    continue
            
            return positions
            
        except Exception as e:
            logger.error(f"Error fetching Kraken positions: {e}", exc_info=True)
            return []
    
    def place_stop_order(self, symbol: str, quantity: float, stop_price: float) -> Optional[str]:
        """
        Place a stop-loss order (for trailing stop updates).
        
        Args:
            symbol: Trading symbol (Kraken format, e.g., XXBTZUSD)
            quantity: Order quantity (positive for long, negative for short)
            stop_price: Stop price
            
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Determine order side (sell for long positions, buy for short positions)
            side = 'sell' if quantity > 0 else 'buy'
            
            order_params = {
                'pair': symbol,
                'type': side,
                'ordertype': 'stop-loss',
                'price': str(stop_price),
                'volume': str(abs(quantity))
            }
            
            response = self.kraken_client.query_private('AddOrder', order_params)
            
            if response.get('error'):
                logger.error(f"Kraken stop order error: {response['error']}")
                return None
            
            result = response.get('result', {})
            order_id = result.get('txid', [None])[0]
            
            logger.info(
                f"Stop order placed: {symbol} qty={quantity} stop=${stop_price:.2f} order_id={order_id}"
            )
            return order_id
            
        except Exception as e:
            logger.error(f"Failed to place stop order for {symbol}: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.kraken_client.query_private('CancelOrder', {'txid': order_id})
            
            if response.get('error'):
                logger.warning(f"Kraken cancel order error: {response['error']}")
                return False
            
            logger.info(f"Order cancelled: {order_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def place_margin_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        leverage: float = 2.0,
        order_type: str = 'market',
        limit_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place a margin order (long or short).
        
        Args:
            symbol: Trading symbol (Kraken format)
            side: 'buy' for long, 'sell' for short
            quantity: Order quantity
            leverage: Leverage to use (default 2.0x, max 5.0x)
            order_type: 'market' or 'limit'
            limit_price: Limit price (required if order_type='limit')
            stop_loss: Optional stop-loss price
            take_profit: Optional take-profit price
            
        Returns:
            Order details if successful, None otherwise
        """
        try:
            # Cap leverage at configured max
            leverage = min(leverage, self.max_leverage)
            
            order_params = {
                'pair': symbol,
                'type': side,
                'ordertype': order_type,
                'volume': str(quantity),
                'leverage': str(leverage)
            }
            
            if order_type == 'limit' and limit_price:
                order_params['price'] = str(limit_price)
            
            # Add stop-loss if provided
            if stop_loss:
                order_params['close[ordertype]'] = 'stop-loss'
                order_params['close[price]'] = str(stop_loss)
            
            # Add take-profit if provided (can't have both stop-loss and take-profit in same order)
            elif take_profit:
                order_params['close[ordertype]'] = 'take-profit'
                order_params['close[price]'] = str(take_profit)
            
            response = self.kraken_client.query_private('AddOrder', order_params)
            
            if response.get('error'):
                logger.error(f"Kraken margin order error: {response['error']}")
                return None
            
            result = response.get('result', {})
            order_ids = result.get('txid', [])
            
            logger.info(
                f"Margin order placed: {side.upper()} {quantity} {symbol} @ {order_type} "
                f"leverage={leverage}x order_ids={order_ids}"
            )
            
            return {
                'order_ids': order_ids,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'leverage': leverage,
                'order_type': order_type
            }
            
        except Exception as e:
            logger.error(f"Failed to place margin order for {symbol}: {e}", exc_info=True)
            return None
    
    def close_position(self, symbol: str, quantity: float, reason: str = "Position closure") -> Optional[Dict[str, Any]]:
        """
        Close a position by submitting a market order.
        
        Args:
            symbol: Symbol to close
            quantity: Quantity to close (positive for long, negative for short)
            reason: Reason for closure (for logging)
            
        Returns:
            Order details if successful, None otherwise
        """
        try:
            # Determine close side (opposite of position)
            side = 'sell' if quantity > 0 else 'buy'
            
            order_params = {
                'pair': symbol,
                'type': side,
                'ordertype': 'market',
                'volume': str(abs(quantity))
            }
            
            response = self.kraken_client.query_private('AddOrder', order_params)
            
            if response.get('error'):
                logger.error(f"Kraken close position error: {response['error']}")
                return None
            
            result = response.get('result', {})
            order_ids = result.get('txid', [])
            
            logger.info(
                f"Position closed: {side.upper()} {abs(quantity)} {symbol} @ market - {reason}"
            )
            
            return {
                'order_ids': order_ids,
                'symbol': symbol,
                'quantity': quantity,
                'side': side,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}", exc_info=True)
            return None
    
    def get_market_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Fetch historical market data for a symbol.
        
        Args:
            symbol: Trading symbol (Kraken format)
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Kraken uses 1440 minute (1 day) intervals
            interval = 1440
            since = int((datetime.now() - timedelta(days=days)).timestamp())
            
            response = self.kraken_client.query_public('OHLC', {
                'pair': symbol,
                'interval': interval,
                'since': since
            })
            
            if response.get('error'):
                logger.error(f"Kraken OHLC error: {response['error']}")
                return None
            
            result = response.get('result', {})
            ohlc_data = result.get(symbol, [])
            
            if not ohlc_data:
                logger.warning(f"No OHLC data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlc_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            for col in ['open', 'high', 'low', 'close', 'vwap', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}", exc_info=True)
            return None
    
    def is_market_open(self) -> bool:
        """
        Check if market is open.
        
        For crypto, market is always open.
        
        Returns:
            True (crypto markets are 24/7)
        """
        return True
