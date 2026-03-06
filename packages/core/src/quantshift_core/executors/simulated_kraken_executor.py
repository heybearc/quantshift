"""
Simulated Kraken Executor - Paper Trading Mode

This module provides a simulated Kraken executor for testing without real money.
Uses real market data but simulates order execution and position tracking.
"""

import sys
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from decimal import Decimal

sys.path.insert(0, '/opt/quantshift/packages/core/src')

from quantshift_core.strategies import BaseStrategy, Signal, SignalType, Account, Position
from quantshift_core.risk import PositionLimits

logger = logging.getLogger(__name__)


class SimulatedKrakenExecutor:
    """
    Simulated Kraken executor for paper trading.
    
    Uses real Kraken market data but simulates all trading operations.
    Tracks positions, P&L, and account balance in memory.
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        kraken_api_key: str,
        kraken_api_secret: str,
        symbols: Optional[List[str]] = None,
        simulated_capital: float = 5000.0,
        risk_config: Optional[Dict[str, Any]] = None,
        use_dynamic_symbols: bool = False,
        symbol_universe_config: Optional[Dict[str, Any]] = None,
        max_leverage: float = 2.0
    ):
        """
        Initialize simulated Kraken executor.
        
        Args:
            strategy: Broker-agnostic strategy instance
            kraken_api_key: Kraken API key (for market data only)
            kraken_api_secret: Kraken API secret (for market data only)
            symbols: List of symbols to trade
            simulated_capital: Starting capital for simulation
            risk_config: Risk management configuration
            use_dynamic_symbols: If True, fetch symbols dynamically
            symbol_universe_config: Config for dynamic symbol fetching
            max_leverage: Maximum leverage to use
        """
        self.strategy = strategy
        self.simulated_capital = simulated_capital
        self.risk_config = risk_config or {}
        self.max_leverage = min(max_leverage, 5.0)
        
        # Initialize Kraken API client (for market data only)
        try:
            import krakenex
            self.kraken_client = krakenex.API(key=kraken_api_key, secret=kraken_api_secret)
            logger.info("Kraken API client initialized (SIMULATION MODE - market data only)")
        except ImportError:
            logger.error("krakenex library not installed. Install with: pip install krakenex")
            raise
        
        # Initialize hard position limits
        self.position_limits = PositionLimits()
        
        # Simulation state
        self._cash = simulated_capital
        self._positions: Dict[str, Dict[str, Any]] = {}  # symbol -> position data
        self._orders: Dict[str, Dict[str, Any]] = {}  # order_id -> order data
        self._trades: List[Dict[str, Any]] = []
        self._next_order_id = 1
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
            self.symbols = symbols or ['XXBTZUSD', 'XETHZUSD']
        
        symbol_info = "dynamic (lazy loading)" if use_dynamic_symbols else f"{len(self.symbols)} symbols"
        logger.info(
            f"SimulatedKrakenExecutor initialized with {strategy.name} strategy for {symbol_info}, "
            f"starting capital=${simulated_capital:,.2f}, max_leverage={self.max_leverage}x"
        )
    
    def get_account(self) -> Account:
        """
        Get simulated account information.
        
        Returns:
            Account object with simulated balance and margin info
        """
        # Calculate total position value
        position_value = sum(
            abs(pos['quantity']) * pos['current_price']
            for pos in self._positions.values()
        )
        
        # Calculate unrealized P&L
        unrealized_pl = sum(pos['unrealized_pl'] for pos in self._positions.values())
        
        # Calculate equity
        equity = self._cash + unrealized_pl
        
        # Calculate margin used (for leveraged positions)
        margin_used = sum(
            abs(pos['quantity']) * pos['entry_price'] / pos.get('leverage', 1.0)
            for pos in self._positions.values()
        )
        
        # Free margin
        free_margin = equity - margin_used
        
        return Account(
            equity=equity,
            cash=self._cash,
            buying_power=free_margin * self.max_leverage,
            margin_used=margin_used,
            maintenance_margin=margin_used * 0.4  # 40% maintenance margin
        )
    
    def get_positions(self) -> List[Position]:
        """
        Get simulated open positions.
        
        Returns:
            List of Position objects
        """
        positions = []
        
        for symbol, pos_data in self._positions.items():
            # Update current price from market
            current_price = self._get_current_price(symbol)
            if current_price:
                pos_data['current_price'] = current_price
                
                # Recalculate unrealized P&L
                if pos_data['side'] == 'long':
                    pos_data['unrealized_pl'] = (current_price - pos_data['entry_price']) * pos_data['quantity']
                else:  # short
                    pos_data['unrealized_pl'] = (pos_data['entry_price'] - current_price) * abs(pos_data['quantity'])
            
            position = Position(
                symbol=symbol,
                quantity=pos_data['quantity'],
                entry_price=pos_data['entry_price'],
                current_price=pos_data['current_price'],
                unrealized_pl=pos_data['unrealized_pl'],
                side=pos_data['side']
            )
            positions.append(position)
        
        return positions
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol."""
        try:
            response = self.kraken_client.query_public('Ticker', {'pair': symbol})
            
            if response.get('error'):
                logger.warning(f"Kraken ticker error for {symbol}: {response['error']}")
                return None
            
            result = response.get('result', {})
            ticker_data = result.get(symbol)
            
            if ticker_data:
                # Use last trade price
                last_price = float(ticker_data['c'][0])
                return last_price
            
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching price for {symbol}: {e}")
            return None
    
    def place_stop_order(self, symbol: str, quantity: float, stop_price: float) -> Optional[str]:
        """
        Place a simulated stop-loss order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity (positive for long, negative for short)
            stop_price: Stop price
            
        Returns:
            Order ID if successful
        """
        order_id = f"SIM-{self._next_order_id}"
        self._next_order_id += 1
        
        side = 'sell' if quantity > 0 else 'buy'
        
        self._orders[order_id] = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': abs(quantity),
            'stop_price': stop_price,
            'order_type': 'stop',
            'status': 'open',
            'created_at': datetime.utcnow()
        }
        
        logger.info(
            f"[SIMULATED] Stop order placed: {symbol} qty={quantity} stop=${stop_price:.2f} order_id={order_id}"
        )
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a simulated order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful
        """
        if order_id in self._orders:
            self._orders[order_id]['status'] = 'cancelled'
            logger.info(f"[SIMULATED] Order cancelled: {order_id}")
            return True
        
        logger.warning(f"[SIMULATED] Order not found: {order_id}")
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
        Place a simulated margin order.
        
        Args:
            symbol: Trading symbol
            side: 'buy' for long, 'sell' for short
            quantity: Order quantity
            leverage: Leverage to use
            order_type: 'market' or 'limit'
            limit_price: Limit price (if order_type='limit')
            stop_loss: Optional stop-loss price
            take_profit: Optional take-profit price
            
        Returns:
            Order details if successful
        """
        # Cap leverage
        leverage = min(leverage, self.max_leverage)
        
        # Get current price
        current_price = self._get_current_price(symbol)
        if not current_price:
            logger.error(f"[SIMULATED] Cannot get price for {symbol}")
            return None
        
        # Determine execution price
        if order_type == 'market':
            execution_price = current_price
        elif order_type == 'limit' and limit_price:
            execution_price = limit_price
        else:
            logger.error(f"[SIMULATED] Invalid order type or missing limit price")
            return None
        
        # Calculate position value and required margin
        position_value = quantity * execution_price
        required_margin = position_value / leverage
        
        # Check if we have enough margin
        account = self.get_account()
        if required_margin > account.buying_power / leverage:
            logger.error(f"[SIMULATED] Insufficient margin: need ${required_margin:.2f}, have ${account.buying_power/leverage:.2f}")
            return None
        
        # Create order
        order_id = f"SIM-{self._next_order_id}"
        self._next_order_id += 1
        
        # Execute immediately (market order simulation)
        if symbol in self._positions:
            # Update existing position
            existing = self._positions[symbol]
            
            if side == 'buy':
                new_quantity = existing['quantity'] + quantity
            else:  # sell
                new_quantity = existing['quantity'] - quantity
            
            # If position flips or closes
            if new_quantity == 0:
                # Position closed - realize P&L
                realized_pl = existing['unrealized_pl']
                self._cash += realized_pl
                del self._positions[symbol]
                
                logger.info(f"[SIMULATED] Position closed: {symbol} P&L=${realized_pl:.2f}")
            else:
                # Position updated
                avg_price = (existing['entry_price'] * abs(existing['quantity']) + execution_price * quantity) / abs(new_quantity)
                existing['quantity'] = new_quantity
                existing['entry_price'] = avg_price
                existing['side'] = 'long' if new_quantity > 0 else 'short'
                existing['leverage'] = leverage
        else:
            # New position
            self._positions[symbol] = {
                'symbol': symbol,
                'quantity': quantity if side == 'buy' else -quantity,
                'entry_price': execution_price,
                'current_price': execution_price,
                'unrealized_pl': 0.0,
                'side': 'long' if side == 'buy' else 'short',
                'leverage': leverage,
                'opened_at': datetime.utcnow()
            }
        
        # Deduct margin from cash
        self._cash -= required_margin
        
        # Record trade
        self._trades.append({
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': execution_price,
            'leverage': leverage,
            'timestamp': datetime.utcnow()
        })
        
        logger.info(
            f"[SIMULATED] Margin order executed: {side.upper()} {quantity} {symbol} @ ${execution_price:.2f} "
            f"leverage={leverage}x order_id={order_id}"
        )
        
        return {
            'order_ids': [order_id],
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'leverage': leverage,
            'order_type': order_type,
            'execution_price': execution_price
        }
    
    def close_position(self, symbol: str, quantity: float, reason: str = "Position closure") -> Optional[Dict[str, Any]]:
        """
        Close a simulated position.
        
        Args:
            symbol: Symbol to close
            quantity: Quantity to close
            reason: Reason for closure
            
        Returns:
            Order details if successful
        """
        if symbol not in self._positions:
            logger.warning(f"[SIMULATED] No position to close for {symbol}")
            return None
        
        pos = self._positions[symbol]
        side = 'sell' if quantity > 0 else 'buy'
        
        # Use market order to close
        return self.place_margin_order(
            symbol=symbol,
            side=side,
            quantity=abs(quantity),
            leverage=pos.get('leverage', 1.0),
            order_type='market'
        )
    
    def get_market_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Fetch real historical market data from Kraken.
        
        Args:
            symbol: Trading symbol
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            interval = 1440  # 1 day
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
        
        Returns:
            True (crypto markets are 24/7)
        """
        return True
    
    def get_symbols(self) -> List[str]:
        """
        Get list of symbols to trade.
        
        Returns:
            List of trading symbols
        """
        if self.symbol_universe:
            return self.symbol_universe.get_symbols()
        return self.symbols or []
    
    def recover_positions_on_startup(self, db_session, bot_name: str) -> Dict[str, Any]:
        """
        Recover positions on startup (no-op for simulation).
        
        Args:
            db_session: Database session (unused in simulation)
            bot_name: Name of the bot (unused in simulation)
            
        Returns:
            Empty recovery stats
        """
        logger.info("[SIMULATED] Position recovery not needed - simulation mode")
        return {
            'orphaned_positions': 0,
            'ghost_positions': 0,
            'recovered_positions': []
        }
    
    def run_strategy_cycle(self):
        """
        Run strategy cycle (delegated to orchestrator).
        
        This is a no-op - the bot framework handles strategy execution.
        """
        pass
    
    def get_simulation_stats(self) -> Dict[str, Any]:
        """
        Get simulation statistics.
        
        Returns:
            Dictionary with simulation stats
        """
        account = self.get_account()
        total_pl = account.equity - self.simulated_capital
        
        return {
            'starting_capital': self.simulated_capital,
            'current_equity': account.equity,
            'cash': self._cash,
            'total_pl': total_pl,
            'total_pl_pct': (total_pl / self.simulated_capital) * 100,
            'open_positions': len(self._positions),
            'total_trades': len(self._trades),
            'margin_used': account.margin_used,
            'free_margin': account.equity - account.margin_used,
            'positions': list(self._positions.keys())
        }
