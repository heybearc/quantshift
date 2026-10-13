"""
Alpaca Executor - Broker-Specific Strategy Execution

This module handles the Alpaca-specific implementation of strategy execution.
It bridges the gap between broker-agnostic strategies and Alpaca's API.
"""

import sys
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

# Add core package to path
sys.path.insert(0, '/opt/quantshift/packages/core/src')

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    ClosePositionRequest,
    GetOrderByIdRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    StopOrderRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, OrderStatus, OrderClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from quantshift_core.equity_exits import (
    add_stop,
    broker_side,
    exit_instruction,
    qty_text,
    signed_quantity,
    stop_for_position,
)
from quantshift_core.strategies import BaseStrategy, Signal, SignalType, Account, Position
from quantshift_core.risk import PositionLimits

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
        symbols: Optional[List[str]] = None,
        simulated_capital: Optional[float] = None,
        risk_config: Optional[Dict[str, Any]] = None,
        use_dynamic_symbols: bool = False,
        symbol_universe_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Alpaca executor.
        
        Args:
            strategy: Broker-agnostic strategy instance
            alpaca_client: Alpaca trading client
            data_client: Alpaca data client (optional, will create if not provided)
            symbols: List of symbols to trade (if not using dynamic)
            simulated_capital: Optional simulated capital for position sizing
            use_dynamic_symbols: If True, fetch symbols dynamically
            symbol_universe_config: Config for dynamic symbol fetching
        """
        self.strategy = strategy
        self.alpaca_client = alpaca_client
        self.data_client = data_client
        self.use_dynamic_symbols = use_dynamic_symbols
        self.simulated_capital = simulated_capital
        self.risk_config = risk_config or {}
        
        # Honor risk_management from config. The class default of 5 trimmed the equity book.
        self.position_limits = PositionLimits(
            max_position_pct=self.risk_config.get('max_position_size', 0.10),
            max_positions=self.risk_config.get('max_positions', 10),
            max_daily_loss_pct=self.risk_config.get('daily_loss_limit', 0.03),
            max_total_risk_pct=self.risk_config.get('max_portfolio_heat', 0.15),
        )
        
        # Initialize symbol universe
        if use_dynamic_symbols:
            from quantshift_core.symbol_universe import SymbolUniverse
            self.symbol_universe = SymbolUniverse('alpaca', symbol_universe_config, alpaca_client)
            # Lazy load symbols on first use (after client is ready)
            self.symbols = None
            logger.info(f"Dynamic symbol universe enabled (lazy loading)")
        else:
            self.symbol_universe = None
            self.symbols = symbols or ['SPY']
        
        # Circuit breaker state (reset daily)
        self._daily_trades = 0
        self._daily_loss = 0.0
        self._circuit_breaker_open = False
        self._last_reset_date = datetime.utcnow().date()
        
        symbol_info = "dynamic (lazy loading)" if use_dynamic_symbols else f"{len(self.symbols)} symbols"
        logger.info(
            f"AlpacaExecutor initialized with {strategy.name} strategy for {symbol_info}"
        )
        if simulated_capital:
            logger.info(f"Using simulated capital: ${simulated_capital:,.2f}")
    
    def _ensure_symbols_loaded(self) -> None:
        """Lazy load symbols on first use if using dynamic symbols."""
        if self.use_dynamic_symbols and self.symbols is None:
            self.symbols = self.symbol_universe.get_symbols()
            logger.info(f"Symbols lazy loaded: {len(self.symbols)} symbols")
    
    def refresh_symbols(self) -> None:
        """Refresh symbol universe if using dynamic symbols."""
        if self.use_dynamic_symbols and self.symbol_universe:
            old_count = len(self.symbols) if self.symbols else 0
            self.symbols = self.symbol_universe.get_symbols(force_refresh=True)
            logger.info(
                f"Symbols refreshed: {old_count} -> {len(self.symbols)}"
            )
    
    def get_account(self) -> Account:
        """
        Fetch account information from Alpaca and convert to broker-agnostic format.
        Uses simulated capital if configured.
        """
        try:
            alpaca_account = self.alpaca_client.get_account()
            
            # Use simulated capital if configured
            if self.simulated_capital:
                return Account(
                    equity=self.simulated_capital,
                    cash=self.simulated_capital,
                    buying_power=self.simulated_capital,
                    portfolio_value=self.simulated_capital,
                    positions_count=0
                )
            
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
        alpaca_positions = self.alpaca_client.get_all_positions()
        stops = self._protective_stops()
        
        positions = []
        for pos in alpaca_positions:
            side = broker_side(pos.qty, getattr(pos, "side", None))
            stop = stop_for_position(stops, pos.symbol, side)
            positions.append(Position(
                symbol=pos.symbol,
                quantity=signed_quantity(pos.qty, side),
                entry_price=float(pos.avg_entry_price),
                current_price=float(pos.current_price),
                market_value=float(pos.market_value),
                unrealized_pl=float(pos.unrealized_pl),
                unrealized_plpc=float(pos.unrealized_plpc),
                side=side,
                metadata={"stop_loss": stop} if stop is not None else None,
            ))
        
        self._positions_cache = {pos.symbol: pos for pos in positions}
        return positions

    def _protective_stops(self) -> Dict[str, Dict[str, float]]:
        """Open stop orders keyed by symbol. A missing read leaves stops unset."""
        book: Dict[str, Dict[str, float]] = {}
        try:
            orders = self.alpaca_client.get_orders(
                filter=GetOrdersRequest(status=QueryOrderStatus.OPEN, nested=True, limit=500)
            ) or []
        except Exception as e:
            logger.warning("Could not read open orders for stops: %s", e)
            return book
        for order in orders:
            self._collect_stop(book, order, getattr(order, "symbol", None))
        return book

    def _collect_stop(self, book: Dict[str, Dict[str, float]], order: Any, symbol: Optional[str]) -> None:
        symbol = getattr(order, "symbol", None) or symbol
        add_stop(book, symbol, getattr(order, "side", None), getattr(order, "stop_price", None))
        for leg in getattr(order, "legs", None) or []:
            self._collect_stop(book, leg, symbol)

    def _held(self, symbol: str) -> Optional[Position]:
        cache = getattr(self, "_positions_cache", None)
        if cache is None:
            self.get_positions()
            cache = self._positions_cache or {}
        return cache.get(symbol)

    def _cancel_open_orders(self, symbol: str) -> None:
        """Pull resting bracket legs before an exit so a later stop cannot open a short."""
        try:
            orders = self.alpaca_client.get_orders(
                filter=GetOrdersRequest(
                    status=QueryOrderStatus.OPEN,
                    symbols=[symbol],
                    nested=True,
                    limit=100,
                )
            ) or []
        except Exception as e:
            logger.warning("Could not list open orders for %s: %s", symbol, e)
            return
        for order in orders:
            order_symbol = getattr(order, "symbol", symbol)
            order_id = getattr(order, "id", None)
            if order_id and order_symbol in (symbol, None):
                self.cancel_order(str(order_id))

    def _submit_reduce_only(self, symbol: str, qty: float, side: str):
        """Close shares already held. Never send a market order that can flip the position."""
        client = self.alpaca_client
        if hasattr(client, "close_position"):
            try:
                return client.close_position(
                    symbol,
                    close_options=ClosePositionRequest(qty=qty_text(qty)),
                )
            except Exception as e:
                logger.warning("Reduce-only close failed for %s qty=%s: %s", symbol, qty, e)
                return None
        order_side = OrderSide.SELL if side == "sell" else OrderSide.BUY
        return client.submit_order(
            MarketOrderRequest(
                symbol=symbol,
                qty=float(qty),
                side=order_side,
                time_in_force=TimeInForce.DAY,
            )
        )
    
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
        # Lazy load symbols on first market data fetch
        self._ensure_symbols_loaded()
        
        try:
            # Create data client if not provided
            if not self.data_client:
                from alpaca.data.historical import StockHistoricalDataClient
                import os
                api_key = os.getenv('APCA_API_KEY_ID')
                secret_key = os.getenv('APCA_API_SECRET_KEY')
                self.data_client = StockHistoricalDataClient(api_key, secret_key)
            
            # Fetch data using data client (use IEX feed for paper trading)
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.enums import DataFeed
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=datetime.utcnow() - timedelta(days=days),
                end=datetime.utcnow(),
                feed=DataFeed.IEX  # Use IEX feed for paper trading (free)
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
    
    def _wait_for_fill(self, order_id: str, timeout: int = 10) -> Optional[Any]:
        """
        Poll Alpaca until an order is filled or timeout is reached.
        Returns the filled order object, or None if not filled in time.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                o = self.alpaca_client.get_order_by_id(order_id)
                if o.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED):
                    return o
            except Exception:
                pass
            time.sleep(1)
        return None

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

            if signal.signal_type == SignalType.SELL:
                return self._execute_exit(signal)

            held = self._held(signal.symbol)
            if held is not None and held.side == "short":
                logger.warning(
                    "BUY blocked while %s is short; covering the short instead",
                    signal.symbol,
                )
                return self._execute_exit(signal, cover_all=True)
            
            # Validate position limits for BUY signals
            if signal.signal_type == SignalType.BUY:
                account = self.get_account()
                positions = self.get_positions()
                
                # Calculate position value
                position_value = signal.price * signal.position_size if signal.price and signal.position_size else 0
                
                # Calculate total risk (sum of all stop-loss distances)
                total_risk = 0.0
                for pos in positions:
                    if hasattr(pos, 'unrealized_pl'):
                        # Estimate risk as unrealized P&L if negative
                        total_risk += abs(min(0, float(pos.unrealized_pl)))
                
                # Add risk from new position
                if signal.stop_loss and signal.price:
                    new_position_risk = abs(signal.price - signal.stop_loss) * signal.position_size
                    total_risk += new_position_risk
                
                # Validate against limits
                violation = self.position_limits.validate_new_position(
                    position_value=position_value,
                    portfolio_value=float(account.portfolio_value),
                    current_positions=len(positions),
                    total_risk=total_risk
                )
                
                if violation:
                    logger.warning(
                        "position limit violation %s %s: %s > %s (%s) %s",
                        signal.symbol,
                        violation.limit_type,
                        violation.current_value,
                        violation.limit_value,
                        violation.severity,
                        violation.message,
                    )
                    
                    # Reject trade if critical violation
                    if violation.severity == 'critical':
                        logger.critical(
                            "trade rejected for %s: %s",
                            signal.symbol,
                            violation.message,
                        )
                        return None
            
            # Determine order side
            side = OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL
            
            # For BUY signals with stop_loss and take_profit: use atomic bracket order
            if signal.signal_type == SignalType.BUY and signal.stop_loss and signal.take_profit:
                # Calculate stop loss and take profit prices
                stop_loss_price = round(signal.stop_loss, 2)
                take_profit_price = round(signal.take_profit, 2)
                
                # Create atomic bracket order (entry + SL + TP in one request)
                order_request = MarketOrderRequest(
                    symbol=signal.symbol,
                    qty=signal.position_size or 1,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.BRACKET,
                    stop_loss={'stop_price': stop_loss_price},
                    take_profit={'limit_price': take_profit_price}
                )
                
                order = self.alpaca_client.submit_order(order_request)
                
                # Calculate risk/reward for logging
                entry_price = signal.price
                risk_pct = ((entry_price - stop_loss_price) / entry_price * 100) if entry_price > 0 else 0
                reward_pct = ((take_profit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                reward_risk_ratio = (reward_pct / risk_pct) if risk_pct > 0 else 0
                
                logger.info(
                    f"Bracket order submitted: BUY {signal.position_size} {signal.symbol} @ market | "
                    f"SL: ${stop_loss_price} (-{risk_pct:.2f}%) | "
                    f"TP: ${take_profit_price} (+{reward_pct:.2f}%) | "
                    f"R:R = {reward_risk_ratio:.2f}:1"
                )
                
                fill_price = signal.price  # Will be updated when filled
                
            else:
                # Non-bracket order (SELL signals or missing SL/TP)
                order_request = MarketOrderRequest(
                    symbol=signal.symbol,
                    qty=signal.position_size or 1,
                    side=side,
                    time_in_force=TimeInForce.DAY
                )
                order = self.alpaca_client.submit_order(order_request)
                logger.info(
                    f"Order submitted: {side.value} {signal.position_size} {signal.symbol} @ market"
                )
                
                fill_price = signal.price  # fallback
                
                # For BUY signals without bracket: place SL/TP separately (legacy behavior)
                if signal.signal_type == SignalType.BUY:
                    filled_order = self._wait_for_fill(str(order.id), timeout=15)
                    if filled_order and filled_order.filled_avg_price:
                        fill_price = float(filled_order.filled_avg_price)
                        filled_qty = float(filled_order.filled_qty)
                    else:
                        filled_qty = float(order.qty)

                    # Stop loss — use StopOrderRequest (GTC sell stop)
                    if signal.stop_loss:
                        try:
                            sl_request = StopOrderRequest(
                                symbol=signal.symbol,
                                qty=filled_qty,
                                side=OrderSide.SELL,
                                time_in_force=TimeInForce.GTC,
                                stop_price=round(signal.stop_loss, 2)
                            )
                            self.alpaca_client.submit_order(sl_request)
                            logger.info(f"Stop loss placed: SELL {filled_qty} {signal.symbol} stop @ ${signal.stop_loss:.2f}")
                        except Exception as e:
                            logger.warning(f"Failed to place stop loss for {signal.symbol}: {e}")

                    # Take profit — limit order after confirmed fill
                    if signal.take_profit:
                        try:
                            tp_request = LimitOrderRequest(
                                symbol=signal.symbol,
                                qty=filled_qty,
                                side=OrderSide.SELL,
                                time_in_force=TimeInForce.GTC,
                                limit_price=round(signal.take_profit, 2)
                            )
                            self.alpaca_client.submit_order(tp_request)
                            logger.info(f"Take profit placed: SELL {filled_qty} {signal.symbol} limit @ ${signal.take_profit:.2f}")
                        except Exception as e:
                            logger.warning(f"Failed to place take profit for {signal.symbol}: {e}")

            from quantshift_core.decision_log import decision_reason, decision_snapshot
            decision = decision_snapshot(signal)
            return {
                'id': str(order.id),
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'status': order.status.value,
                'fill_price': fill_price,
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                'signal_reason': signal.reason,
                'strategy': decision['strategy'],
                'entry_reason': decision_reason(signal),
                'regime': decision['regime'],
                'regime_confidence': decision['regime_confidence'],
                'sentiment_score': decision['sentiment_score'],
            }
            
        except Exception as e:
            logger.error(f"Error executing signal for {signal.symbol}: {e}", exc_info=True)
            return None
    
    def is_market_open(self) -> bool:
        """Check if the US stock market is currently open via Alpaca clock API."""
        try:
            clock = self.alpaca_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.warning(f"Could not check market clock: {e} — assuming closed")
            return False
    
    def place_stop_order(self, symbol: str, quantity: float, stop_price: float) -> Optional[str]:
        """
        Place a stop-loss order (for trailing stop updates).
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            stop_price: Stop price
            
        Returns:
            Order ID if successful, None otherwise
        """
        held = self._held(symbol)
        if held is not None and held.side == "short":
            logger.warning("Refusing a sell-stop on short %s", symbol)
            return None
        try:
            sl_request = StopOrderRequest(
                symbol=symbol,
                qty=abs(float(quantity)),
                side=OrderSide.SELL,
                time_in_force=TimeInForce.GTC,
                stop_price=round(stop_price, 2)
            )
            order = self.alpaca_client.submit_order(sl_request)
            logger.info(
                f"Stop order placed: {symbol} qty={quantity} stop=${stop_price:.2f} order_id={order.id}"
            )
            return str(order.id)
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
            self.alpaca_client.cancel_order_by_id(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cancel order {order_id}: {e}")
            return False

    def _reset_daily_counters_if_needed(self):
        """Reset daily circuit breaker counters at the start of each trading day."""
        today = datetime.utcnow().date()
        if today != self._last_reset_date:
            self._daily_trades = 0
            self._daily_loss = 0.0
            self._circuit_breaker_open = False
            self._last_reset_date = today
            logger.info("Daily circuit breaker counters reset")

    def _check_circuit_breakers(self, account: Any) -> Optional[str]:
        """
        Check all circuit breaker conditions.
        Returns a reason string if trading should be halted, None if clear.
        """
        limits = self.risk_config.get('limits', {})
        max_daily_trades = limits.get('max_daily_trades', 10)
        max_daily_loss = self.risk_config.get('max_daily_loss', 0.05)
        max_drawdown = self.risk_config.get('max_drawdown', 0.15)
        max_positions = limits.get('max_positions', 5)

        if self._circuit_breaker_open:
            return "Circuit breaker already open from earlier this session"

        if self._daily_trades >= max_daily_trades:
            return f"Max daily trades reached ({self._daily_trades}/{max_daily_trades})"

        # Daily loss check: unrealized + realized vs equity
        if account.equity > 0:
            daily_loss_pct = self._daily_loss / account.equity
            if daily_loss_pct >= max_daily_loss:
                return f"Max daily loss breached ({daily_loss_pct:.1%} >= {max_daily_loss:.1%})"

        # Drawdown check: unrealized P&L vs portfolio value
        if hasattr(account, 'unrealized_pl') and account.portfolio_value > 0:
            drawdown = -account.unrealized_pl / account.portfolio_value
            if drawdown >= max_drawdown:
                return f"Max drawdown breached ({drawdown:.1%} >= {max_drawdown:.1%})"

        return None

    def run_strategy_cycle(self) -> Dict[str, Any]:
        """
        Run one complete strategy cycle:
        1. Check market hours — skip execution if market is closed
        2. Reset daily counters if new day
        3. Check circuit breakers — halt if limits breached
        4. Enforce max positions cap
        5. Fetch market data, generate signals, execute
        
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

        # Guard: only execute orders during market hours
        if not self.is_market_open():
            logger.debug("Market is closed — skipping signal execution this cycle")
            return results

        # Reset daily counters if it's a new trading day
        self._reset_daily_counters_if_needed()
        
        try:
            # Get account and positions
            account = self.get_account()
            positions = self.get_positions()
            covers = self._cover_shorts(positions)
            if covers:
                results['orders_executed'].extend(covers)
                positions = self.get_positions()
            account.positions_count = len(positions)
            
            # Ensure symbols are loaded (lazy loading)
            self._ensure_symbols_loaded()
            
            if not self.symbols:
                logger.warning("No symbols loaded after lazy load attempt, skipping cycle")
                results['errors'].append("No symbols loaded")
                return results

            # Circuit breaker check
            halt_reason = self._check_circuit_breakers(account)
            if halt_reason:
                self._circuit_breaker_open = True
                logger.warning(f"CIRCUIT BREAKER OPEN — halting strategy: {halt_reason}")
                results['errors'].append(f"Circuit breaker: {halt_reason}")
                return results

            # Block new buys when the book is full or leveraged. Do not sell
            # the excess here; a failed position read used to look empty and
            # the next cycle opened another batch.
            max_positions = int(
                self.risk_config.get(
                    'max_positions',
                    self.risk_config.get('limits', {}).get('max_positions', 10),
                )
            )
            max_leverage = float(self.risk_config.get('max_leverage', 1.0) or 1.0)
            gross_value = sum(abs(float(pos.market_value or 0)) for pos in positions)
            equity = float(account.equity or 0)
            leverage = (gross_value / equity) if equity > 0 else 0.0
            recovered = getattr(self, "_recovered_broker_count", None)
            unread_book = recovered not in (None, 0) and len(positions) == 0
            at_max_positions = (
                len(positions) >= max_positions
                or leverage > max_leverage
                or unread_book
            )
            
            if at_max_positions:
                logger.warning(
                    "Blocking BUY signals positions=%s/%s leverage=%.2f max_leverage=%.2f unread_book=%s",
                    len(positions),
                    max_positions,
                    leverage,
                    max_leverage,
                    unread_book,
                )
            
            logger.info(
                f"Strategy cycle started - Account: ${account.equity:.2f}, "
                f"Positions: {len(positions)}, Symbols: {len(self.symbols)}"
            )
            
            # Fetch market data for all symbols. Regime detection needs 200 daily bars,
            # so SPY is loaded with a longer history than the trading symbols.
            market_data_dict = {}
            for symbol in self.symbols:
                try:
                    results['symbols_checked'].append(symbol)
                    history_days = 450 if symbol == 'SPY' else 90
                    market_data_dict[symbol] = self.get_market_data(symbol, days=history_days)
                except Exception as e:
                    error_msg = f"Error fetching data for {symbol}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results['errors'].append(error_msg)

            spy_frame = market_data_dict.get('SPY')
            if spy_frame is None or len(spy_frame) < 200:
                try:
                    long_spy = self.get_market_data('SPY', days=450)
                    if long_spy is not None and len(long_spy) >= 200:
                        if 'SPY' in self.symbols:
                            market_data_dict['SPY'] = long_spy
                        else:
                            market_data_dict['_regime_SPY'] = long_spy
                except Exception as e:
                    logger.error("Error fetching SPY history for regime detection: %s", e)
            
            # Generate signals for all symbols
            if market_data_dict:
                try:
                    signals = self.strategy.generate_signals(
                        market_data=market_data_dict,
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

                        # Skip BUY signals if at max positions
                        if signal.signal_type == SignalType.BUY and at_max_positions:
                            logger.warning(
                                "BUY blocked at max positions for %s (%s/%s): %s",
                                signal.symbol,
                                len(positions),
                                max_positions,
                                signal.reason,
                            )
                            continue

                        # Execute the signal
                        order = self.execute_signal(signal)
                        if order:
                            results['orders_executed'].append(order)
                            self._daily_trades += 1
                    
                except Exception as e:
                    error_msg = f"Error generating signals: {str(e)}"
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
    
    def _execute_exit(self, signal: Signal, cover_all: bool = False) -> Optional[Dict[str, Any]]:
        """Sell a long or buy to cover a short. A sell while flat is skipped."""
        requested = None if cover_all else signal.position_size
        order = self.close_position(
            signal.symbol,
            0 if requested is None else requested,
            reason=signal.reason or "strategy exit",
        )
        if not order:
            return None
        from quantshift_core.decision_log import decision_reason, decision_snapshot
        decision = decision_snapshot(signal)
        order['fill_price'] = order.get('fill_price') or signal.price
        order['signal_reason'] = signal.reason
        order['strategy'] = decision['strategy']
        order['entry_reason'] = decision_reason(signal)
        order['regime'] = decision['regime']
        order['regime_confidence'] = decision['regime_confidence']
        order['sentiment_score'] = decision['sentiment_score']
        return order

    def _cover_shorts(self, positions: List[Position]) -> List[Dict[str, Any]]:
        """Equity is long-only. Buy back any open short before new signals."""
        orders = []
        for pos in positions:
            if pos.side != "short":
                continue
            logger.warning(
                "Covering equity short %s qty=%s",
                pos.symbol,
                abs(float(pos.quantity)),
            )
            order = self.close_position(
                pos.symbol,
                abs(float(pos.quantity)),
                reason="cover short; equity bot is long-only",
            )
            if order:
                order['strategy'] = order.get('strategy') or 'equity-long-only'
                order['entry_reason'] = order.get('entry_reason') or order.get('reason')
                orders.append(order)
        return orders

    def close_position(self, symbol: str, quantity: float, reason: str = "Position closure") -> Optional[Dict[str, Any]]:
        """
        Reduce a position without opening the other side.

        A long is sold, up to the shares held. A short is bought back.
        Resting bracket orders are cancelled first, then the size is read again.
        """
        try:
            self._cancel_open_orders(symbol)
            self._positions_cache = None
            held = self._held(symbol)
            instruction = exit_instruction(
                held.side if held else None,
                held.quantity if held else 0,
                quantity,
            )
            if instruction is None:
                logger.info("Not closing %s: no open position (%s)", symbol, reason)
                return None

            order = self._submit_reduce_only(symbol, instruction["qty"], instruction["side"])
            if order is None:
                return None
            self._positions_cache = None

            logger.info(
                "Position reduced: %s %s %s @ market - %s",
                instruction["side"],
                instruction["qty"],
                symbol,
                reason,
            )

            return {
                'id': str(order.id),
                'symbol': getattr(order, "symbol", symbol),
                'qty': float(getattr(order, "qty", instruction["qty"])),
                'side': order.side.value if hasattr(order.side, "value") else str(order.side),
                'type': order.type.value if hasattr(getattr(order, "type", None), "value") else "market",
                'status': order.status.value if hasattr(getattr(order, "status", None), "value") else "accepted",
                'reason': reason,
                'signal_reason': reason,
                'entry_reason': reason,
            }

        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}", exc_info=True)
            return None
    
    def recover_positions_on_startup(self, db_session, bot_name: str) -> Dict[str, Any]:
        """
        Sync positions from broker to database on bot startup.
        
        Compares broker positions with database positions and:
        - Adds orphaned positions (in broker but not in DB)
        - Removes ghost positions (in DB but not in broker)
        
        Args:
            db_session: SQLAlchemy database session
            bot_name: Name of the bot (e.g., 'quantshift-equity')
            
        Returns:
            Dict with recovery statistics
        """
        from quantshift_core.state_manager import StateManager
        
        recovery_stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'broker_positions': 0,
            'db_positions': 0,
            'orphaned_added': 0,
            'ghosts_removed': 0,
            'symbols_orphaned': [],
            'symbols_ghost': []
        }
        
        try:
            # Get all positions from broker
            broker_positions = self.alpaca_client.get_all_positions()
            recovery_stats['broker_positions'] = len(broker_positions)
            self._recovered_broker_count = len(broker_positions)
            
            # Get all positions from database for this bot
            state_manager = StateManager(bot_name)
            db_positions = state_manager.get_positions_atomic(bot_name)
            recovery_stats['db_positions'] = len(db_positions)
            
            # Create sets of symbols for comparison
            broker_symbols = {pos.symbol for pos in broker_positions}
            db_symbols = {pos["symbol"] for pos in db_positions}
            
            # Find orphaned positions (in broker but not in DB)
            orphaned_symbols = broker_symbols - db_symbols
            recovery_stats['symbols_orphaned'] = list(orphaned_symbols)
            
            for symbol in orphaned_symbols:
                broker_pos = next(p for p in broker_positions if p.symbol == symbol)
                
                # Add to database
                state_manager.update_position_atomic(
                    bot_name=bot_name,
                    symbol=symbol,
                    quantity=float(broker_pos.qty),
                    entry_price=float(broker_pos.avg_entry_price),
                    current_price=float(broker_pos.current_price),
                    unrealized_pl=float(broker_pos.unrealized_pl),
                    strategy_name='RECOVERED'
                )
                recovery_stats['orphaned_added'] += 1
                logger.warning(
                    f"Position recovery: Added orphaned position {symbol} "
                    f"(qty={broker_pos.qty}, entry=${broker_pos.avg_entry_price:.2f})"
                )
            
            # Find ghost positions (in DB but not in broker).
            # An empty broker read must not wipe the book.
            ghost_symbols = set()
            if broker_positions:
                ghost_symbols = db_symbols - broker_symbols
            elif db_positions:
                logger.warning(
                    "Position recovery skipped ghost removal: broker returned no positions "
                    "while the database has %s",
                    len(db_positions),
                )
            recovery_stats['symbols_ghost'] = list(ghost_symbols)
            
            for symbol in ghost_symbols:
                # Remove from database
                state_manager.delete_position_atomic(bot_name, symbol)
                recovery_stats['ghosts_removed'] += 1
                logger.warning(
                    f"Position recovery: Removed ghost position {symbol} "
                    f"(existed in DB but not in broker)"
                )
            
            # Log summary
            if recovery_stats['orphaned_added'] > 0 or recovery_stats['ghosts_removed'] > 0:
                logger.warning(
                    f"Position recovery complete: "
                    f"{recovery_stats['orphaned_added']} orphaned added, "
                    f"{recovery_stats['ghosts_removed']} ghosts removed"
                )
            else:
                logger.info("Position recovery: Database matches broker (no discrepancies)")
            
            return recovery_stats
            
        except Exception as e:
            logger.error(f"Position recovery failed: {e}", exc_info=True)
            recovery_stats['error'] = str(e)
            return recovery_stats
    
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
