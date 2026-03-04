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
from quantshift_core.risk import PositionLimits

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
        risk_config: Optional[Dict[str, Any]] = None,
        use_dynamic_symbols: bool = False,
        symbol_universe_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Coinbase executor.
        
        Args:
            strategy: Broker-agnostic strategy instance
            coinbase_client: Coinbase REST client
            symbols: List of symbols to trade (if not using dynamic)
            simulated_capital: Optional simulated capital for position sizing
            risk_config: Risk management configuration
            use_dynamic_symbols: If True, fetch symbols dynamically
            symbol_universe_config: Config for dynamic symbol fetching
        """
        self.strategy = strategy
        self.coinbase_client = coinbase_client
        self.use_dynamic_symbols = use_dynamic_symbols
        self.simulated_capital = simulated_capital
        self.risk_config = risk_config or {}
        
        # Initialize hard position limits
        self.position_limits = PositionLimits()
        
        # Initialize symbol universe
        if use_dynamic_symbols:
            from quantshift_core.symbol_universe import SymbolUniverse
            self.symbol_universe = SymbolUniverse('coinbase', symbol_universe_config, coinbase_client)
            # Lazy load symbols on first use (after client is ready)
            self.symbols = None
            logger.info(f"Dynamic symbol universe enabled (lazy loading)")
        else:
            self.symbol_universe = None
            self.symbols = symbols or ['BTC-USD']
        
        symbol_info = "dynamic (lazy loading)" if use_dynamic_symbols else f"{len(self.symbols)} symbols"
        logger.info(
            f"CoinbaseExecutor initialized with {strategy.name} strategy for {symbol_info}"
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
        Fetch account information from Coinbase and convert to broker-agnostic format.
        Uses simulated capital if configured.
        """
        try:
            # Use simulated capital if configured (for paper trading)
            if self.simulated_capital:
                logger.debug(
                    "using_simulated_capital",
                    capital=self.simulated_capital
                )
                return Account(
                    equity=self.simulated_capital,
                    cash=self.simulated_capital,
                    buying_power=self.simulated_capital,
                    portfolio_value=self.simulated_capital,
                    positions_count=0
                )
            
            # Get all accounts from Coinbase
            accounts_response = self.coinbase_client.get_accounts()
            
            # Find USD/USDC balance for spot trading
            total_balance = 0.0
            if hasattr(accounts_response, 'accounts'):
                for account in accounts_response.accounts:
                    if hasattr(account, 'currency') and account.currency in ['USD', 'USDC']:
                        if hasattr(account, 'available_balance'):
                            available = float(account.available_balance.value)
                            total_balance += available
                            logger.debug(
                                "account_balance_found",
                                currency=account.currency,
                                balance=available
                            )
            
            logger.info(
                "account_fetched",
                total_balance=total_balance,
                buying_power=total_balance
            )
            
            return Account(
                equity=total_balance,
                cash=total_balance,
                buying_power=total_balance,
                portfolio_value=total_balance,
                positions_count=0
            )
        except Exception as e:
            logger.error(f"Error fetching account: {e}", exc_info=True)
            # Return simulated capital as fallback
            if self.simulated_capital:
                logger.warning("Falling back to simulated capital due to API error")
                return Account(
                    equity=self.simulated_capital,
                    cash=self.simulated_capital,
                    buying_power=self.simulated_capital,
                    portfolio_value=self.simulated_capital,
                    positions_count=0
                )
            raise
    
    def get_positions(self) -> List[Position]:
        """
        Fetch positions from Coinbase and convert to broker-agnostic format.
        For spot trading, positions are crypto holdings with non-zero balance.
        """
        try:
            # Get all accounts (spot holdings)
            accounts_response = self.coinbase_client.get_accounts()
            
            positions = []
            if hasattr(accounts_response, 'accounts'):
                for account in accounts_response.accounts:
                    if not hasattr(account, 'currency') or not hasattr(account, 'available_balance'):
                        continue
                    
                    currency = account.currency
                    
                    # Skip USD/USDC (these are cash, not positions)
                    if currency in ['USD', 'USDC']:
                        continue
                    
                    quantity = float(account.available_balance.value)
                    if quantity == 0:
                        continue
                    
                    # Construct symbol (e.g., BTC-USD)
                    symbol = f"{currency}-USD"
                    
                    # Skip if not in our trading symbols
                    if self.symbols and symbol not in self.symbols:
                        continue
                    
                    # Get current price
                    try:
                        product = self.coinbase_client.get_product(symbol)
                        current_price = float(product.price) if hasattr(product, 'price') else 0.0
                    except:
                        current_price = 0.0
                    
                    # We don't have entry price for existing holdings, use current price
                    entry_price = current_price
                    market_value = quantity * current_price
                    
                    positions.append(Position(
                        symbol=symbol,
                        quantity=quantity,
                        entry_price=entry_price,
                        current_price=current_price,
                        market_value=market_value,
                        unrealized_pl=0.0,  # Unknown for existing holdings
                        unrealized_plpc=0.0,
                        side='long'
                    ))
                    
                    logger.debug(
                        "position_found",
                        symbol=symbol,
                        quantity=quantity,
                        value=market_value
                    )
            
            logger.info(
                "positions_fetched",
                count=len(positions)
            )
            return positions
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}", exc_info=True)
            return []
    
    def get_market_data(
        self,
        symbol: str,
        granularity: str = 'ONE_HOUR',
        num_candles: int = 300
    ) -> pd.DataFrame:
        """
        Fetch historical market data from Coinbase.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC-USD')
            granularity: Candle granularity (ONE_MINUTE, FIVE_MINUTE, ONE_HOUR, ONE_DAY)
            num_candles: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        # Lazy load symbols on first market data fetch
        self._ensure_symbols_loaded()
        
        try:
            # Calculate start and end times
            end_time = int(datetime.utcnow().timestamp())
            start_time = int((datetime.utcnow() - timedelta(days=30)).timestamp())
            
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
            logger.info(
                "execute_signal_called",
                symbol=signal.symbol,
                signal_type=signal.signal_type.value,
                position_size=signal.position_size,
                price=signal.price
            )
            
            if signal.signal_type == SignalType.HOLD:
                return None
            
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
                        "position_limit_violation",
                        symbol=signal.symbol,
                        limit_type=violation.limit_type,
                        current_value=violation.current_value,
                        limit_value=violation.limit_value,
                        message=violation.message,
                        severity=violation.severity
                    )
                    
                    # Reject trade if critical violation
                    if violation.severity == 'critical':
                        logger.critical(
                            "trade_rejected_limit_violation",
                            symbol=signal.symbol,
                            violation=violation.message
                        )
                        return None
            
            # Determine order side
            side = 'BUY' if signal.signal_type == SignalType.BUY else 'SELL'
            
            # For BUY signals with stop_loss and take_profit: use bracket order pattern
            if signal.signal_type == SignalType.BUY and signal.stop_loss and signal.take_profit:
                # Calculate stop loss and take profit prices
                stop_loss_price = round(signal.stop_loss, 8)  # Crypto needs more precision
                take_profit_price = round(signal.take_profit, 8)
                
                # Calculate risk/reward for logging
                entry_price = signal.price
                risk_pct = ((entry_price - stop_loss_price) / entry_price * 100) if entry_price > 0 else 0
                reward_pct = ((take_profit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                reward_risk_ratio = (reward_pct / risk_pct) if risk_pct > 0 else 0
                
                # Submit entry order
                order_config = {
                    'product_id': signal.symbol,
                    'side': 'BUY',
                    'order_configuration': {
                        'market_market_ioc': {
                            'base_size': str(signal.position_size or 1)
                        }
                    }
                }
                
                response = self.coinbase_client.market_order(**order_config)
                order = response.get('order', {})
                order_id = order.get('order_id')
                
                logger.info(
                    f"Bracket order entry submitted: BUY {signal.position_size} {signal.symbol} @ market | "
                    f"SL: ${stop_loss_price} (-{risk_pct:.2f}%) | "
                    f"TP: ${take_profit_price} (+{reward_pct:.2f}%) | "
                    f"R:R = {reward_risk_ratio:.2f}:1"
                )
                
                fill_price = signal.price  # fallback
                
                # Wait for fill to get actual fill price
                filled_order = self._wait_for_fill(order_id, timeout=15)
                if filled_order:
                    fills = filled_order.get('fills', [])
                    if fills:
                        fill_price = float(fills[0].get('price', signal.price))
                
                # Immediately place stop-loss and take-profit (bracket pattern)
                sl_success = False
                tp_success = False
                
                try:
                    sl_order = self._place_stop_loss_order(
                        signal.symbol,
                        signal.position_size or 1,
                        stop_loss_price
                    )
                    sl_success = True
                    logger.info(
                        "bracket_stop_loss_placed",
                        symbol=signal.symbol,
                        qty=signal.position_size,
                        stop_price=stop_loss_price,
                        order_id=sl_order.get('order_id')
                    )
                except Exception as e:
                    logger.error("bracket_stop_loss_failed", symbol=signal.symbol, error=str(e), exc_info=True)
                
                try:
                    tp_order = self._place_take_profit_order(
                        signal.symbol,
                        signal.position_size or 1,
                        take_profit_price
                    )
                    tp_success = True
                    logger.info(
                        "bracket_take_profit_placed",
                        symbol=signal.symbol,
                        qty=signal.position_size,
                        limit_price=take_profit_price,
                        order_id=tp_order.get('order_id')
                    )
                except Exception as e:
                    logger.error("bracket_take_profit_failed", symbol=signal.symbol, error=str(e), exc_info=True)
                
                # Log bracket order completion status
                if sl_success and tp_success:
                    logger.info("bracket_order_complete", symbol=signal.symbol, status="fully_protected")
                elif sl_success:
                    logger.warning("bracket_order_partial", symbol=signal.symbol, status="stop_loss_only")
                elif tp_success:
                    logger.warning("bracket_order_partial", symbol=signal.symbol, status="take_profit_only")
                else:
                    logger.critical("bracket_order_failed", symbol=signal.symbol, status="unprotected")
                
            else:
                # Non-bracket order (SELL signals or missing SL/TP)
                order_config = {
                    'product_id': signal.symbol,
                    'side': side,
                    'order_configuration': {
                        'market_market_ioc': {
                            'base_size': str(signal.position_size or 1)
                        }
                    }
                }
                
                response = self.coinbase_client.market_order(**order_config)
                order = response.get('order', {})
                order_id = order.get('order_id')
                
                logger.info(
                    f"Order submitted: {side} {signal.position_size} {signal.symbol} @ market"
                )
                
                fill_price = signal.price  # fallback
                
                # For BUY signals without bracket: place SL/TP separately (legacy behavior)
                if signal.signal_type == SignalType.BUY:
                    filled_order = self._wait_for_fill(order_id, timeout=15)
                    if filled_order:
                        fills = filled_order.get('fills', [])
                        if fills:
                            fill_price = float(fills[0].get('price', signal.price))
                    
                    if signal.stop_loss:
                        try:
                            sl_order = self._place_stop_loss_order(
                                signal.symbol,
                                signal.position_size or 1,
                                signal.stop_loss
                            )
                            logger.info(
                                "stop_loss_placed",
                                symbol=signal.symbol,
                                qty=signal.position_size,
                                stop_price=signal.stop_loss,
                                order_id=sl_order.get('order_id')
                            )
                        except Exception as e:
                            logger.error("stop_loss_placement_failed", error=str(e))
                    
                    if signal.take_profit:
                        try:
                            tp_order = self._place_take_profit_order(
                                signal.symbol,
                                signal.position_size or 1,
                                signal.take_profit
                            )
                            logger.info(
                                "take_profit_placed",
                                symbol=signal.symbol,
                                qty=signal.position_size,
                                limit_price=signal.take_profit,
                                order_id=tp_order.get('order_id')
                            )
                        except Exception as e:
                            logger.error("take_profit_placement_failed", error=str(e))
            
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
    
    def _place_stop_loss_order(self, symbol: str, quantity: float, stop_price: float) -> dict:
        """
        Place a stop-loss order for a position.
        
        Args:
            symbol: Trading symbol
            quantity: Position size to protect
            stop_price: Stop-loss trigger price
            
        Returns:
            Order response from Coinbase API
        """
        import time
        
        order_config = {
            "client_order_id": f"sl_{symbol}_{int(time.time())}",
            "product_id": symbol,
            "side": "SELL",
            "order_configuration": {
                "stop_limit_stop_limit_gtc": {
                    "base_size": str(quantity),
                    "limit_price": str(stop_price * 0.995),
                    "stop_price": str(stop_price),
                    "stop_direction": "STOP_DIRECTION_STOP_DOWN"
                }
            }
        }
        
        response = self.coinbase_client.create_order(**order_config)
        return response
    
    def close_position(self, symbol: str, quantity: float, reason: str = "Position closure") -> Optional[Dict[str, Any]]:
        """
        Close a position by submitting a market sell order.
        
        Args:
            symbol: Symbol to close
            quantity: Quantity to close (absolute value)
            reason: Reason for closure (for logging)
            
        Returns:
            Order details if successful, None otherwise
        """
        try:
            # Submit market sell order to close position
            order_config = {
                'product_id': symbol,
                'side': 'SELL',
                'order_configuration': {
                    'market_market_ioc': {
                        'base_size': str(abs(quantity))
                    }
                }
            }
            
            response = self.coinbase_client.market_order(**order_config)
            order = response.get('order', {})
            
            logger.info(
                f"Position closed: SELL {quantity} {symbol} @ market - {reason}"
            )
            
            return {
                'id': order.get('order_id'),
                'symbol': symbol,
                'qty': quantity,
                'side': 'SELL',
                'type': 'market',
                'status': order.get('status', 'UNKNOWN'),
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}", exc_info=True)
            return None
    
    def _place_take_profit_order(self, symbol: str, quantity: float, limit_price: float) -> dict:
        """
        Place a take-profit limit order for a position.
        
        Args:
            symbol: Trading symbol
            quantity: Position size to close
            limit_price: Take-profit limit price
            
        Returns:
            Order response from Coinbase API
        """
        import time
        
        order_config = {
            "client_order_id": f"tp_{symbol}_{int(time.time())}",
            "product_id": symbol,
            "side": "SELL",
            "order_configuration": {
                "limit_limit_gtc": {
                    "base_size": str(quantity),
                    "limit_price": str(limit_price),
                    "post_only": False
                }
            }
        }
        
        response = self.coinbase_client.create_order(**order_config)
        return response
    
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
            
            # 2. Ensure symbols are loaded (lazy loading)
            self._ensure_symbols_loaded()
            
            if not self.symbols:
                logger.warning("No symbols loaded after lazy load attempt, skipping cycle")
                return []
            
            logger.info(f"Fetching market data for {len(self.symbols)} symbols")
            
            # 3. Fetch market data for all symbols
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
    
    def recover_positions_on_startup(self, db_session, bot_name: str) -> Dict[str, Any]:
        """
        Sync positions from broker to database on bot startup.
        
        Compares broker positions with database positions and:
        - Adds orphaned positions (in broker but not in DB)
        - Removes ghost positions (in DB but not in broker)
        
        Args:
            db_session: SQLAlchemy database session
            bot_name: Name of the bot (e.g., 'quantshift-crypto')
            
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
            # Get all positions from broker (Coinbase accounts)
            accounts_response = self.coinbase_client.get_accounts()
            broker_positions = []
            
            if hasattr(accounts_response, 'accounts'):
                for account in accounts_response.accounts:
                    # Only include accounts with non-zero balance
                    if hasattr(account, 'available_balance') and float(account.available_balance.value) > 0:
                        # Convert to position format (symbol is currency-USD)
                        symbol = f"{account.currency}-USD"
                        broker_positions.append({
                            'symbol': symbol,
                            'quantity': float(account.available_balance.value),
                            'currency': account.currency
                        })
            
            recovery_stats['broker_positions'] = len(broker_positions)
            
            # Get all positions from database for this bot
            state_manager = StateManager(db_session)
            db_positions = state_manager.get_positions(bot_name)
            recovery_stats['db_positions'] = len(db_positions)
            
            # Create sets of symbols for comparison
            broker_symbols = {pos['symbol'] for pos in broker_positions}
            db_symbols = {pos.symbol for pos in db_positions}
            
            # Find orphaned positions (in broker but not in DB)
            orphaned_symbols = broker_symbols - db_symbols
            recovery_stats['symbols_orphaned'] = list(orphaned_symbols)
            
            for symbol in orphaned_symbols:
                broker_pos = next(p for p in broker_positions if p['symbol'] == symbol)
                
                # Get current price for this symbol
                try:
                    product = self.coinbase_client.get_product(symbol)
                    current_price = float(product.price) if hasattr(product, 'price') else 0.0
                except:
                    current_price = 0.0
                
                # Add to database (we don't know entry price, use current price as estimate)
                state_manager.update_position(
                    bot_name=bot_name,
                    symbol=symbol,
                    quantity=broker_pos['quantity'],
                    entry_price=current_price,
                    current_price=current_price,
                    unrealized_pl=0.0,
                    strategy_name='RECOVERED'
                )
                recovery_stats['orphaned_added'] += 1
                logger.warning(
                    f"Position recovery: Added orphaned position {symbol} "
                    f"(qty={broker_pos['quantity']}, price=${current_price:.2f})"
                )
            
            # Find ghost positions (in DB but not in broker)
            ghost_symbols = db_symbols - broker_symbols
            recovery_stats['symbols_ghost'] = list(ghost_symbols)
            
            for symbol in ghost_symbols:
                # Remove from database
                state_manager.delete_position(bot_name, symbol)
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
