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


def _client_order_id(prefix: str, symbol: str) -> str:
    safe = "".join(ch for ch in symbol if ch.isalnum()) or "order"
    return f"{prefix}_{safe}_{int(time.time() * 1000)}"


def _order_attr(response: Any, key: str, default=None):
    """Read a field from a Coinbase SDK response or a plain dict."""
    if response is None:
        return default
    if isinstance(response, dict):
        if key in response:
            return response.get(key, default)
        nested = response.get("order") or {}
        return nested.get(key, default)
    value = getattr(response, key, None)
    if value is not None:
        return value
    success = getattr(response, "success_response", None)
    if success is not None:
        nested = success.get(key) if isinstance(success, dict) else getattr(success, key, None)
        if nested is not None:
            return nested
    return default


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
        self._sim_cash = float(simulated_capital) if simulated_capital else 0.0
        self._sim_positions: Dict[str, Dict[str, float]] = {}
        
        # Initialize position limits with config values
        self.position_limits = PositionLimits(
            max_position_pct=self.risk_config.get('max_position_size', 0.10),
            max_positions=self.risk_config.get('max_positions', 5),
            max_daily_loss_pct=self.risk_config.get('daily_loss_limit', 0.03),
            max_total_risk_pct=self.risk_config.get('max_portfolio_heat', 0.15)
        )
        
        # Initialize circuit breaker tracking
        self._daily_trades = 0
        self._daily_loss = 0.0
        self._circuit_breaker_open = False
        self._last_reset_date = datetime.utcnow().date()
        
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
            logger.info(f"Using simulated capital: ${simulated_capital:,.2f} (orders stay off the live Coinbase account)")

    def _is_paper(self) -> bool:
        return bool(self.simulated_capital and self.simulated_capital > 0)

    def _paper_account(self) -> Account:
        market_value = sum(
            pos["quantity"] * pos["current_price"] for pos in self._sim_positions.values()
        )
        equity = self._sim_cash + market_value
        return Account(
            equity=equity,
            cash=self._sim_cash,
            buying_power=self._sim_cash,
            portfolio_value=equity,
            positions_count=len(self._sim_positions),
        )

    def _paper_positions(self) -> List[Position]:
        positions = []
        for symbol, pos in self._sim_positions.items():
            qty = pos["quantity"]
            entry = pos["entry_price"]
            price = pos["current_price"]
            unrealized = (price - entry) * qty
            positions.append(Position(
                symbol=symbol,
                quantity=qty,
                entry_price=entry,
                current_price=price,
                market_value=qty * price,
                unrealized_pl=unrealized,
                unrealized_plpc=(unrealized / (entry * qty)) if entry and qty else 0.0,
                side="long",
            ))
        return positions

    def _simulate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        reason: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Fill a paper order against simulated cash. Never calls Coinbase."""
        qty = abs(float(quantity or 0))
        price = float(price or 0)
        side = side.upper()
        if qty <= 0 or price <= 0:
            logger.error("simulated order missing size or price for %s", symbol)
            return None

        if side == "BUY":
            cost = qty * price
            if cost > self._sim_cash:
                logger.warning(
                    "simulated BUY rejected %s cost=%.2f cash=%.2f",
                    symbol,
                    cost,
                    self._sim_cash,
                )
                return None
            existing = self._sim_positions.get(symbol)
            if existing:
                new_qty = existing["quantity"] + qty
                existing["entry_price"] = (
                    (existing["entry_price"] * existing["quantity"]) + (price * qty)
                ) / new_qty
                existing["quantity"] = new_qty
                existing["current_price"] = price
            else:
                self._sim_positions[symbol] = {
                    "quantity": qty,
                    "entry_price": price,
                    "current_price": price,
                }
            self._sim_cash -= cost
        else:
            existing = self._sim_positions.get(symbol)
            if not existing or existing["quantity"] <= 0:
                logger.warning("simulated SELL rejected %s: no position", symbol)
                return None
            sell_qty = min(qty, existing["quantity"])
            self._sim_cash += sell_qty * price
            existing["quantity"] -= sell_qty
            existing["current_price"] = price
            if existing["quantity"] <= 1e-12:
                del self._sim_positions[symbol]
            qty = sell_qty

        order_id = _client_order_id("sim", symbol)
        logger.info(
            "[SIMULATED] %s %s %s @ %.4f cash=%.2f reason=%s",
            side,
            qty,
            symbol,
            price,
            self._sim_cash,
            reason,
        )
        return {
            "id": order_id,
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "market",
            "status": "SIMULATED",
            "fill_price": price,
            "submitted_at": datetime.utcnow().isoformat(),
            "signal_reason": reason,
        }
    
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
            # DEBUG: Log simulated_capital value
            logger.info(
                "get_account called simulated_capital=%s",
                self.simulated_capital,
            )
            
            if self._is_paper():
                account = self._paper_account()
                logger.info(
                    "using simulated capital cash=%.2f equity=%.2f positions=%s",
                    account.cash,
                    account.equity,
                    account.positions_count,
                )
                return account
            
            # Get all accounts from Coinbase (live trading mode)
            logger.info("fetching_real_coinbase_balance")
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
                                "account balance %s=%s",
                                account.currency,
                                available,
                            )
            
            logger.info("account fetched balance=%s", total_balance)
            
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
        if self._is_paper():
            positions = self._paper_positions()
            logger.info("simulated positions count=%s", len(positions))
            return positions

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
                    
                    # Handle both dict and object formats for available_balance
                    if isinstance(account.available_balance, dict):
                        quantity = float(account.available_balance.get('value', 0))
                    else:
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
                        "position %s qty=%s value=%s",
                        symbol,
                        quantity,
                        market_value,
                    )
            
            logger.info("positions fetched count=%s", len(positions))
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
            # Coinbase limits to 350 candles max, so 14 days × 24 hours = 336 candles (safe)
            end_time = int(datetime.utcnow().timestamp())
            start_time = int((datetime.utcnow() - timedelta(days=14)).timestamp())
            
            # Fetch candles from Coinbase
            logger.debug(
                "fetching candles %s start=%s end=%s granularity=%s",
                symbol,
                start_time,
                end_time,
                granularity,
            )
            
            candles = self.coinbase_client.get_candles(
                product_id=symbol,
                start=start_time,
                end=end_time,
                granularity=granularity
            )
            
            # Convert to DataFrame
            # Coinbase SDK returns a response object with 'candles' attribute
            # Each candle is an object with: start, low, high, open, close, volume
            candles_list = candles.candles if hasattr(candles, 'candles') else []
            
            logger.debug("candles received %s count=%s", symbol, len(candles_list))
            
            # Convert candle objects to list of dicts
            data = []
            for candle in candles_list:
                # Handle both object attributes and dict format
                if hasattr(candle, '__dict__'):
                    candle_dict = candle.__dict__
                else:
                    candle_dict = candle
                
                data.append({
                    'timestamp': int(candle_dict.get('start', candle_dict.get('timestamp', 0))),
                    'open': float(candle_dict.get('open', 0)),
                    'high': float(candle_dict.get('high', 0)),
                    'low': float(candle_dict.get('low', 0)),
                    'close': float(candle_dict.get('close', 0)),
                    'volume': float(candle_dict.get('volume', 0))
                })
            
            df = pd.DataFrame(data)
            
            if len(df) == 0:
                logger.warning("Coinbase returned 0 candles for %s", symbol)
                return pd.DataFrame()
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            
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
                inner = getattr(order, "order", None) or order
                status = str(getattr(inner, "status", "") or "").upper()
                if status in ("FILLED", "PARTIALLY_FILLED"):
                    return inner
            except Exception:
                pass
            time.sleep(1)
        return None

    def _submit_market_order(self, symbol: str, side: str, base_size: str):
        """Submit a Coinbase market IOC order. SDK requires client_order_id."""
        if self._is_paper():
            raise RuntimeError(f"refusing live Coinbase order for paper bot: {side} {symbol}")
        response = self.coinbase_client.market_order(
            client_order_id=_client_order_id("mkt", symbol),
            product_id=symbol,
            side=side,
            base_size=str(base_size),
        )
        if getattr(response, "success", True) is False:
            reason = getattr(response, "error_response", None) or getattr(response, "failure_reason", None)
            raise RuntimeError(f"Coinbase rejected {side} {symbol}: {reason}")
        return response

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
                "execute_signal %s %s size=%s price=%s",
                signal.symbol,
                signal.signal_type.value,
                signal.position_size,
                signal.price,
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
                        f"position_limit_violation: {signal.symbol} - {violation.limit_type}: "
                        f"{violation.current_value} > {violation.limit_value} ({violation.severity})"
                    )
                    
                    # Reject trade if critical violation
                    if violation.severity == 'critical':
                        logger.critical(
                            f"trade_rejected_limit_violation: {signal.symbol} - {violation.message}"
                        )
                        return None
            
            # Determine order side
            side = 'BUY' if signal.signal_type == SignalType.BUY else 'SELL'

            if self._is_paper():
                return self._simulate_order(
                    signal.symbol,
                    side,
                    signal.position_size or 1,
                    signal.price or 0,
                    signal.reason or "",
                )
            
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
                
                response = self._submit_market_order(
                    signal.symbol, "BUY", signal.position_size or 1
                )
                order_id = _order_attr(response, "order_id")
                order_status = _order_attr(response, "status", "UNKNOWN")
                order_created = _order_attr(response, "created_time")
                
                logger.info(
                    f"Bracket order entry submitted: BUY {signal.position_size} {signal.symbol} @ market | "
                    f"SL: ${stop_loss_price} (-{risk_pct:.2f}%) | "
                    f"TP: ${take_profit_price} (+{reward_pct:.2f}%) | "
                    f"R:R = {reward_risk_ratio:.2f}:1"
                )
                
                fill_price = signal.price  # fallback
                
                # Wait for fill to get actual fill price
                filled_order = self._wait_for_fill(order_id, timeout=15)
                filled_price = _order_attr(filled_order, "average_filled_price")
                if filled_price:
                    fill_price = float(filled_price)
                
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
                        "bracket stop loss placed %s qty=%s stop=%s order=%s",
                        signal.symbol,
                        signal.position_size,
                        stop_loss_price,
                        _order_attr(sl_order, "order_id"),
                    )
                except Exception as e:
                    logger.error("bracket_stop_loss_failed for %s: %s", signal.symbol, e, exc_info=True)
                
                try:
                    tp_order = self._place_take_profit_order(
                        signal.symbol,
                        signal.position_size or 1,
                        take_profit_price
                    )
                    tp_success = True
                    logger.info(
                        "bracket take profit placed %s qty=%s limit=%s order=%s",
                        signal.symbol,
                        signal.position_size,
                        take_profit_price,
                        _order_attr(tp_order, "order_id"),
                    )
                except Exception as e:
                    logger.error(f"bracket_take_profit_failed for {signal.symbol}: {e}", exc_info=True)
                
                # Log bracket order completion status
                if sl_success and tp_success:
                    logger.info(f"bracket_order_complete for {signal.symbol}: fully_protected")
                elif sl_success:
                    logger.warning(f"bracket_order_partial for {signal.symbol}: stop_loss_only")
                elif tp_success:
                    logger.warning(f"bracket_order_partial for {signal.symbol}: take_profit_only")
                else:
                    logger.critical(f"bracket_order_failed for {signal.symbol}: unprotected")
                
            else:
                response = self._submit_market_order(
                    signal.symbol, side, signal.position_size or 1
                )
                order_id = _order_attr(response, "order_id")
                order_status = _order_attr(response, "status", "UNKNOWN")
                order_created = _order_attr(response, "created_time")
                
                logger.info(
                    f"Order submitted: {side} {signal.position_size} {signal.symbol} @ market"
                )
                
                fill_price = signal.price  # fallback
                
                # For BUY signals without bracket: place SL/TP separately (legacy behavior)
                if signal.signal_type == SignalType.BUY:
                    filled_order = self._wait_for_fill(order_id, timeout=15)
                    filled_price = _order_attr(filled_order, "average_filled_price")
                    if filled_price:
                        fill_price = float(filled_price)
                    
                    if signal.stop_loss:
                        try:
                            sl_order = self._place_stop_loss_order(
                                signal.symbol,
                                signal.position_size or 1,
                                signal.stop_loss
                            )
                            logger.info(
                                "stop loss placed %s qty=%s stop=%s order=%s",
                                signal.symbol,
                                signal.position_size,
                                signal.stop_loss,
                                _order_attr(sl_order, "order_id"),
                            )
                        except Exception as e:
                            logger.error("stop loss placement failed for %s: %s", signal.symbol, e)
                    
                    if signal.take_profit:
                        try:
                            tp_order = self._place_take_profit_order(
                                signal.symbol,
                                signal.position_size or 1,
                                signal.take_profit
                            )
                            logger.info(
                                "take profit placed %s qty=%s limit=%s order=%s",
                                signal.symbol,
                                signal.position_size,
                                signal.take_profit,
                                _order_attr(tp_order, "order_id"),
                            )
                        except Exception as e:
                            logger.error("take profit placement failed for %s: %s", signal.symbol, e)
            
            from quantshift_core.decision_log import decision_reason, decision_snapshot
            decision = decision_snapshot(signal)
            return {
                'id': order_id,
                'symbol': signal.symbol,
                'qty': signal.position_size or 1,
                'side': side,
                'type': 'market',
                'status': order_status,
                'fill_price': fill_price,
                'submitted_at': order_created,
                'signal_reason': signal.reason,
                'strategy': decision['strategy'],
                'entry_reason': decision_reason(signal),
                'regime': decision['regime'],
                'regime_confidence': decision['regime_confidence'],
                'sentiment_score': decision['sentiment_score'],
            }
            
        except RuntimeError as e:
            logger.error("signal execution failed for %s: %s", signal.symbol, e)
            return None
        except Exception as e:
            logger.error("signal execution failed for %s: %s", signal.symbol, e, exc_info=True)
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
            if self._is_paper():
                pos = self._sim_positions.get(symbol)
                price = pos["current_price"] if pos else 0
                return self._simulate_order(symbol, "SELL", quantity, price, reason)
            response = self._submit_market_order(symbol, "SELL", abs(quantity))
            
            logger.info(
                f"Position closed: SELL {quantity} {symbol} @ market - {reason}"
            )
            
            return {
                'id': _order_attr(response, "order_id"),
                'symbol': symbol,
                'qty': quantity,
                'side': 'SELL',
                'type': 'market',
                'status': _order_attr(response, "status", "UNKNOWN"),
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}", exc_info=True)
            return None
    
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
        try:
            if self._is_paper():
                order_id = _client_order_id("simsl", symbol)
                logger.info("[SIMULATED] stop recorded %s qty=%s stop=%s", symbol, quantity, stop_price)
                return order_id
            import time
            
            order_config = {
                "client_order_id": f"trailing_sl_{symbol}_{int(time.time())}",
                "product_id": symbol,
                "side": "SELL",
                "order_configuration": {
                    "stop_limit_stop_limit_gtc": {
                        "base_size": str(quantity),
                        "limit_price": str(stop_price * 0.995),  # 0.5% slippage buffer
                        "stop_price": str(stop_price),
                        "stop_direction": "STOP_DIRECTION_STOP_DOWN"
                    }
                }
            }
            
            response = self.coinbase_client.create_order(**order_config)
            order_id = _order_attr(response, "order_id")
            
            logger.info(
                f"Stop order placed: {symbol} qty={quantity} stop=${stop_price:.2f} order_id={order_id}"
            )
            return str(order_id) if order_id else None
            
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
            response = self.coinbase_client.cancel_orders([order_id])
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cancel order {order_id}: {e}")
            return False
    
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
            
            # Check max positions limit
            max_positions = int(
                self.risk_config.get(
                    'max_positions',
                    self.risk_config.get('limits', {}).get('max_positions', 8),
                )
            )
            at_max_positions = len(positions) >= max_positions
            
            if at_max_positions:
                logger.warning(
                    "At max positions (%s/%s) - blocking BUY signals",
                    len(positions),
                    max_positions,
                )
            
            # 4. Execute signals
            executed_orders = []
            for signal in signals:
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
            state_manager = StateManager(bot_name)

            # Paper fills live in the database. Reload them into the simulator
            # instead of treating the live Coinbase account as the book.
            if self._is_paper():
                db_positions = state_manager.get_positions_atomic(bot_name)
                self._sim_positions = {
                    pos["symbol"]: {
                        "quantity": float(pos["quantity"]),
                        "entry_price": float(pos["entry_price"]),
                        "current_price": float(pos["current_price"]),
                    }
                    for pos in db_positions
                }
                recovery_stats['broker_positions'] = len(self._sim_positions)
                recovery_stats['db_positions'] = len(db_positions)
                logger.info(
                    "paper position recovery loaded %s positions from the database",
                    len(db_positions),
                )
                return recovery_stats

            # Get all positions from broker (Coinbase accounts)
            accounts_response = self.coinbase_client.get_accounts()
            broker_positions = []
            quote_currencies = {"USD", "USDC", "USDT", "EUR", "GBP"}
            
            if hasattr(accounts_response, 'accounts'):
                for account in accounts_response.accounts:
                    # Only include accounts with non-zero balance
                    if hasattr(account, 'available_balance') and float(account.available_balance.value) > 0:
                        if account.currency in quote_currencies:
                            continue
                        # Convert to position format (symbol is currency-USD)
                        symbol = f"{account.currency}-USD"
                        broker_positions.append({
                            'symbol': symbol,
                            'quantity': float(account.available_balance.value),
                            'currency': account.currency
                        })
            
            recovery_stats['broker_positions'] = len(broker_positions)
            
            # Get all positions from database for this bot
            db_positions = state_manager.get_positions_atomic(bot_name)
            recovery_stats['db_positions'] = len(db_positions)
            
            # Create sets of symbols for comparison
            broker_symbols = {pos['symbol'] for pos in broker_positions}
            db_symbols = {pos["symbol"] for pos in db_positions}
            
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
                state_manager.update_position_atomic(
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
            
            # An empty broker read must not wipe the paper or live book.
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
