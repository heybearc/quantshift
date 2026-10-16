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

from quantshift_core.candles import AttachedFrame, drop_forming_candle
from quantshift_core.strategies import BaseStrategy, Signal, SignalType, Account, Position
from quantshift_core.risk import PositionLimits
from quantshift_core.executors.kraken_public import kraken_public, kraken_result_value

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
            portfolio_value=equity,  # For dashboard display
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
            
            quantity = float(pos_data['quantity'])
            price = float(pos_data['current_price'])
            entry = float(pos_data['entry_price'])
            unrealized = float(pos_data['unrealized_pl'])
            position = Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=entry,
                current_price=price,
                market_value=abs(quantity) * price,
                unrealized_pl=unrealized,
                unrealized_plpc=(unrealized / (entry * abs(quantity))) if entry and quantity else 0.0,
                side=pos_data['side'],
                metadata={
                    "stop_loss": pos_data.get("stop_loss"),
                    "take_profit": pos_data.get("take_profit"),
                },
            )
            positions.append(position)
        
        return positions
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol."""
        try:
            response = kraken_public('Ticker', {'pair': symbol})
            
            if response.get('error'):
                logger.warning(f"Kraken ticker error for {symbol}: {response['error']}")
                return None
            
            result = response.get('result', {})
            ticker_data = kraken_result_value(result)
            
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
    
    def _cached_entry(self, symbol: str) -> Optional[pd.DataFrame]:
        """Hourly bars for the entry trigger. Reused for ten minutes."""
        cache = getattr(self, "_entry_cache", None)
        if cache is None:
            self._entry_cache = {}
            cache = self._entry_cache
        cached = cache.get(symbol)
        now = time.time()
        if cached and now - cached[0] < 600:
            return cached[1]
        frame = self.get_market_data(symbol, days=20, interval=60)
        cache[symbol] = (now, frame)
        return frame

    def get_market_data(self, symbol: str, days: int = 30, interval: int = 1440) -> Optional[pd.DataFrame]:
        """
        Fetch real historical market data from Kraken.
        
        Args:
            symbol: Trading symbol
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        if interval == 1440:
            cache = getattr(self, "_daily_cache", None)
            if cache is None:
                self._daily_cache = {}
                cache = self._daily_cache
            cached = cache.get(symbol)
            now = time.time()
            if cached and now - cached[0] < 3600 and cached[1] is not None and len(cached[1]):
                df = cached[1].copy()
                entry = self._cached_entry(symbol)
                if entry is not None and len(entry):
                    df.attrs["entry"] = AttachedFrame(entry)
                return df

        try:
            since = int((datetime.now() - timedelta(days=days)).timestamp())
            
            response = kraken_public('OHLC', {
                'pair': symbol,
                'interval': interval,
                'since': since
            })
            
            if response.get('error'):
                logger.error(f"Kraken OHLC error: {response['error']}")
                return None
            
            result = response.get('result', {})
            
            # Kraken returns data with internal symbol names (e.g., XXBTZUSD for XBTUSD)
            # Get the first key that's not 'last' (which is the timestamp)
            data_keys = [k for k in result.keys() if k != 'last']
            if not data_keys:
                logger.warning(f"No OHLC data returned for {symbol}")
                return None
            
            ohlc_data = result.get(data_keys[0], [])
            
            if not ohlc_data:
                logger.warning(f"No OHLC data in result for {symbol}")
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
            df = drop_forming_candle(df, interval * 60)
            if interval == 1440 and len(df):
                cache = getattr(self, "_daily_cache", None)
                if cache is None:
                    self._daily_cache = {}
                    cache = self._daily_cache
                cache[symbol] = (time.time(), df.copy())
                entry = self._cached_entry(symbol)
                if entry is not None and len(entry):
                    df.attrs["entry"] = AttachedFrame(entry)
            
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
    
    def _ensure_symbols_loaded(self) -> None:
        """Load the curated list, and reload it after the universe cache expires."""
        if not self.symbol_universe:
            return
        if self.symbols is not None and self.symbol_universe._is_cache_valid():
            return
        self.symbols = self.symbol_universe.get_symbols()
        logger.info("[SIMULATED] symbols loaded: %s", len(self.symbols or []))

    def get_symbols(self) -> List[str]:
        """
        Get list of symbols to trade.
        
        Returns:
            List of trading symbols
        """
        self._ensure_symbols_loaded()
        return self.symbols or []
    
    def place_stop_order(self, symbol: str, quantity: float, stop_price: float) -> Optional[str]:
        pos = self._positions.get(symbol)
        if pos is None:
            return None
        pos["stop_loss"] = float(stop_price)
        logger.info("[SIMULATED] stop recorded %s qty=%s stop=%s", symbol, quantity, stop_price)
        return f"sim-kraken-stop-{symbol}"

    def cancel_order(self, order_id: str) -> bool:
        logger.info("[SIMULATED] cancel ignored %s", order_id)
        return True

    def _close_paper_brackets(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        closed = []
        for symbol, pos in list(self._positions.items()):
            frame = market_data.get(symbol)
            if frame is None or len(frame) == 0:
                continue
            column = "close" if "close" in frame.columns else ("Close" if "Close" in frame.columns else None)
            if column is None:
                continue
            price = float(frame[column].iloc[-1])
            if price <= 0:
                continue
            pos["current_price"] = price
            stop = pos.get("stop_loss")
            target = pos.get("take_profit")
            reason = None
            if pos.get("side") == "short":
                if stop and price >= float(stop):
                    reason = "paper stop"
                elif target and price <= float(target):
                    reason = "paper take profit"
            else:
                if stop and price <= float(stop):
                    reason = "paper stop"
                elif target and price >= float(target):
                    reason = "paper take profit"
            if not reason:
                continue
            order = self._reduce_position(symbol, float(pos["quantity"]), price, "SELL" if pos.get("side") == "long" else "BUY", reason)
            if order:
                closed.append(order)
        return closed

    def _max_positions(self) -> int:
        return int(
            self.risk_config.get(
                'max_positions',
                self.risk_config.get('limits', {}).get('max_positions', 6),
            )
        )

    def _order_record(self, symbol: str, side: str, qty: float, price: float, reason: str) -> Dict[str, Any]:
        self._next_order_id += 1
        return {
            "id": f"sim-kraken-{self._next_order_id}",
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "market",
            "status": "SIMULATED",
            "fill_price": price,
            "submitted_at": datetime.utcnow().isoformat(),
            "signal_reason": reason,
        }

    def _open_position(self, signal: Signal, qty: float, price: float, side: str) -> Optional[Dict[str, Any]]:
        existing = self._positions.get(signal.symbol)
        if existing and existing.get("side") == side:
            logger.info("[SIMULATED] already open %s %s", side, signal.symbol)
            return None
        if signal.symbol not in self._positions and len(self._positions) >= self._max_positions():
            logger.warning("[SIMULATED] order blocked at max positions for %s", signal.symbol)
            return None
        leverage = max(1.0, float(self.max_leverage or 1.0))
        margin = qty * price / leverage
        if margin > self._cash + 1e-9:
            logger.warning(
                "[SIMULATED] rejected %s %s margin=%.2f cash=%.2f",
                side,
                signal.symbol,
                margin,
                self._cash,
            )
            return None
        self._cash -= margin
        self._positions[signal.symbol] = {
            "quantity": qty,
            "entry_price": price,
            "current_price": price,
            "unrealized_pl": 0.0,
            "side": side,
            "leverage": leverage,
            "margin": margin,
            "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
            "take_profit": float(signal.take_profit) if signal.take_profit else None,
        }
        logger.info("[SIMULATED] opened %s %s qty=%s @ %.4f", side, signal.symbol, qty, price)
        return self._order_record(signal.symbol, "BUY" if side == "long" else "SELL", qty, price, signal.reason or "")

    def _reduce_position(self, symbol: str, qty: float, price: float, order_side: str, reason: str) -> Optional[Dict[str, Any]]:
        pos = self._positions.get(symbol)
        if not pos or qty <= 0:
            return None
        held = float(pos["quantity"])
        qty = min(qty, held)
        fraction = qty / held if held else 1.0
        if pos["side"] == "long":
            pnl = (price - float(pos["entry_price"])) * qty
        else:
            pnl = (float(pos["entry_price"]) - price) * qty
        self._cash += float(pos.get("margin", 0.0)) * fraction + pnl
        pos["quantity"] = held - qty
        pos["margin"] = float(pos.get("margin", 0.0)) * (1.0 - fraction)
        pos["current_price"] = price
        if pos["quantity"] <= 1e-12:
            del self._positions[symbol]
        logger.info("[SIMULATED] reduced %s qty=%s @ %.4f pnl=%.2f", symbol, qty, price, pnl)
        return self._order_record(symbol, order_side, qty, price, reason)

    def execute_signal(self, signal: Signal) -> Optional[Dict[str, Any]]:
        """Fill a paper Kraken order. Shorts are allowed. Nothing is sent to Kraken."""
        if signal.signal_type == SignalType.HOLD:
            return None
        price = float(signal.price or 0) or float(self._get_current_price(signal.symbol) or 0)
        requested = abs(float(signal.position_size or 0))
        if price <= 0:
            logger.warning("[SIMULATED] order missing price for %s", signal.symbol)
            return None
        existing = self._positions.get(signal.symbol)
        if signal.signal_type == SignalType.BUY:
            if existing and existing.get("side") == "short":
                held = float(existing["quantity"])
                qty = held if requested <= 0 or requested == int(held) else min(requested, held)
                return self._reduce_position(signal.symbol, qty, price, "BUY", signal.reason or "cover")
            if requested <= 0:
                return None
            return self._open_position(signal, requested, price, "long")
        if existing and existing.get("side") == "long":
            held = float(existing["quantity"])
            qty = held if requested <= 0 or requested == int(held) else min(requested, held)
            return self._reduce_position(signal.symbol, qty, price, "SELL", signal.reason or "sell")
        if requested <= 0:
            return None
        return self._open_position(signal, requested, price, "short")

    def recover_positions_on_startup(self, db_session, bot_name: str) -> Dict[str, Any]:
        """Reload the paper book from the database and reserve margin from starting cash."""
        from quantshift_core.state_manager import StateManager

        db_positions = StateManager(bot_name).get_positions_atomic(bot_name)
        self._positions = {}
        margin_used = 0.0
        leverage = max(1.0, float(self.max_leverage or 1.0))
        for pos in db_positions:
            qty = abs(float(pos["quantity"]))
            entry = float(pos["entry_price"])
            margin = qty * entry / leverage
            margin_used += margin
            side = str(pos.get("side") or "long").lower()
            if side not in ("long", "short"):
                side = "long"
            self._positions[pos["symbol"]] = {
                "quantity": qty,
                "entry_price": entry,
                "current_price": float(pos["current_price"]),
                "unrealized_pl": float(pos.get("unrealized_pl") or 0),
                "side": side,
                "leverage": leverage,
                "margin": margin,
                "stop_loss": pos.get("stop_loss"),
                "take_profit": pos.get("take_profit"),
            }
        self._cash = max(0.0, float(self.simulated_capital) - margin_used)
        self._recovered_broker_count = len(self._positions)
        logger.info(
            "[SIMULATED] recovered %s positions, cash=%.2f",
            len(self._positions),
            self._cash,
        )
        return {
            "broker_positions": len(self._positions),
            "db_positions": len(db_positions),
            "orphaned_added": 0,
            "ghosts_removed": 0,
        }
    
    def run_strategy_cycle(self) -> List[Dict[str, Any]]:
        """
        Run one complete strategy cycle:
        1. Fetch account and positions
        2. Fetch market data
        3. Generate signals
        4. Execute signals (simulated)
        
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
                logger.warning("[SIMULATED] Circuit breaker is open, skipping strategy cycle")
                return []
            
            # 1. Get account and positions
            account = self.get_account()
            positions = self.get_positions()
            
            # 2. Ensure symbols are loaded. The curated list refreshes when its cache expires.
            self._ensure_symbols_loaded()
            if not self.symbols:
                logger.warning("[SIMULATED] No symbols configured, skipping cycle")
                return []
            
            logger.info(f"[SIMULATED] Fetching market data for {len(self.symbols)} symbols")
            
            # 3. Fetch market data for all symbols
            market_data = {}
            for symbol in self.symbols:
                try:
                    df = self.get_market_data(symbol, days=450)
                    if df is not None:
                        market_data[symbol] = df
                except Exception as e:
                    logger.error(f"[SIMULATED] Failed to fetch data for {symbol}: {e}")
            
            if not market_data:
                logger.warning("[SIMULATED] No market data available, skipping cycle")
                return []

            executed_orders = self._close_paper_brackets(market_data)
            positions = self.get_positions()
            account = self.get_account()
            
            # 4. Generate signals from strategy
            signals = self.strategy.generate_signals(market_data, account, positions)
            
            if not signals:
                logger.debug("[SIMULATED] No signals generated")
                return executed_orders
            
            # 5. Execute signals (simulated)
            for signal in signals:
                order = self.execute_signal(signal)
                if order:
                    executed_orders.append(order)
                    self._daily_trades += 1
            
            return executed_orders
            
        except Exception as e:
            logger.error(f"[SIMULATED] Error in strategy cycle: {e}", exc_info=True)
            return []
    
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
