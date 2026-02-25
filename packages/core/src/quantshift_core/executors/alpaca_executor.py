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
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest, LimitOrderRequest, StopOrderRequest, GetOrderByIdRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, OrderStatus
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
            
            # Determine order side
            side = OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL
            
            # Create and submit market order
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

            # For BUY signals: wait for fill then place SL/TP bracket orders
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

            return {
                'id': str(order.id),
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'status': order.status.value,
                'fill_price': fill_price,
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                'signal_reason': signal.reason
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

            # Max positions cap — skip BUY signals if at limit
            max_positions = self.risk_config.get('limits', {}).get('max_positions', 5)
            at_max_positions = len(positions) >= max_positions
            
            logger.info(
                f"Strategy cycle started - Account: ${account.equity:.2f}, "
                f"Positions: {len(positions)}, Symbols: {len(self.symbols)}"
            )
            
            # Fetch market data for all symbols
            market_data_dict = {}
            for symbol in self.symbols:
                try:
                    results['symbols_checked'].append(symbol)
                    market_data_dict[symbol] = self.get_market_data(symbol, days=90)
                except Exception as e:
                    error_msg = f"Error fetching data for {symbol}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results['errors'].append(error_msg)
            
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
                            logger.info(f"Skipping BUY {signal.symbol} — at max positions ({max_positions})")
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
