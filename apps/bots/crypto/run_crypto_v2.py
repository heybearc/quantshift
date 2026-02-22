#!/usr/bin/env python3
"""
QuantShift Crypto Bot V2 - Coinbase Perpetuals

Uses Coinbase Advanced Trade API perpetual futures for true long/short trading.
Products: BTC-PERP-INTX, ETH-PERP-INTX, SOL-PERP-INTX
Strategy: MA Crossover + RSI + MACD on hourly candles.
"""
import os
import sys
import time
import signal
import logging
import yaml
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

sys.path.insert(0, '/opt/quantshift/apps/bots/crypto/src')

from quantshift_crypto.strategy import CryptoStrategy
from quantshift_crypto.database_writer import CryptoDatabaseWriter

from coinbase.rest import RESTClient

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

STRATEGY_NAME = "CRYPTO_MA_RSI_MACD"
CONFIG_PATH = '/opt/quantshift/config/crypto_strategy.yaml'


# ---------------------------------------------------------------------------
# Strategy (ported from existing CryptoStrategy, extended with ATR sizing)
# ---------------------------------------------------------------------------

class CryptoSignalStrategy:
    """
    Multi-indicator crypto strategy: MA crossover + RSI + MACD.
    Returns 'BUY', 'SELL', or None.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.short_window = config.get('short_window', 20)
        self.long_window = config.get('long_window', 50)
        self.rsi_period = config.get('rsi_period', 14)
        self.atr_period = config.get('atr_period', 14)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.rsi_oversold = config.get('rsi_oversold', 30)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy().sort_index()
        df['sma_short'] = df['close'].rolling(self.short_window).mean()
        df['sma_long'] = df['close'].rolling(self.long_window).mean()
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
        rs = gain / loss.replace(0, float('nan'))
        df['rsi'] = 100 - (100 / (1 + rs))
        tr = pd.concat([
            df['high'] - df['low'],
            (df['high'] - df['close'].shift()).abs(),
            (df['low'] - df['close'].shift()).abs(),
        ], axis=1).max(axis=1)
        df['atr'] = tr.rolling(self.atr_period).mean()
        return df

    def generate_signal(self, df: pd.DataFrame) -> Optional[str]:
        if len(df) < self.long_window + 2:
            return None
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # MA crossover
        ma_cross_up = (latest['sma_short'] > latest['sma_long'] and
                       prev['sma_short'] <= prev['sma_long'])
        ma_cross_down = (latest['sma_short'] < latest['sma_long'] and
                         prev['sma_short'] >= prev['sma_long'])

        # MACD crossover
        macd_cross_up = (latest['macd'] > latest['macd_signal'] and
                         prev['macd'] <= prev['macd_signal'])
        macd_cross_down = (latest['macd'] < latest['macd_signal'] and
                           prev['macd'] >= prev['macd_signal'])

        # RSI extremes
        rsi_oversold = latest['rsi'] < self.rsi_oversold and prev['rsi'] >= self.rsi_oversold
        rsi_overbought = latest['rsi'] > self.rsi_overbought and prev['rsi'] <= self.rsi_overbought

        if (ma_cross_up or macd_cross_up or rsi_oversold) and latest['rsi'] < self.rsi_overbought:
            reason = 'ma_cross' if ma_cross_up else ('macd_cross' if macd_cross_up else 'rsi_oversold')
            logger.info(f"BUY signal: {reason} | RSI={latest['rsi']:.1f}")
            return 'BUY'

        if (ma_cross_down or macd_cross_down or rsi_overbought) and latest['rsi'] > self.rsi_oversold:
            reason = 'ma_cross' if ma_cross_down else ('macd_cross' if macd_cross_down else 'rsi_overbought')
            logger.info(f"SELL signal: {reason} | RSI={latest['rsi']:.1f}")
            return 'SELL'

        return None

    def calculate_position_size(
        self, equity: float, price: float, atr: float, risk_pct: float = 0.01
    ) -> float:
        """ATR-based position sizing: risk_pct of equity per trade."""
        if atr <= 0 or price <= 0:
            return 0.0
        risk_amount = equity * risk_pct
        stop_distance = atr * 2.0
        units = risk_amount / stop_distance
        notional = units * price
        max_notional = equity * 0.20  # max 20% per position
        if notional > max_notional:
            units = max_notional / price
        return round(units, 6)


# ---------------------------------------------------------------------------
# Crypto Bot V2
# ---------------------------------------------------------------------------

class CryptoBotV2:

    def __init__(self, config_path: str = CONFIG_PATH):
        self.bot_name = "crypto-bot"
        self.running = True
        self.config = self._load_config(config_path)

        # Alpaca clients (same paper account as equity bot)
        api_key = os.getenv('APCA_API_KEY_ID')
        secret_key = os.getenv('APCA_API_SECRET_KEY')
        self.trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=True)
        self.data_client = CryptoHistoricalDataClient(api_key=api_key, secret_key=secret_key)

        # Strategy per symbol
        strategy_cfg = self.config.get('strategy', {}).get('parameters', {})
        self.symbols: List[str] = self.config.get('strategy', {}).get('symbols', ['BTC/USD', 'ETH/USD'])
        self.strategies: Dict[str, CryptoSignalStrategy] = {
            s: CryptoSignalStrategy(strategy_cfg) for s in self.symbols
        }

        # Risk config
        self.risk_config = self.config.get('risk_management', {})
        self.risk_pct = self.risk_config.get('risk_per_trade', 0.01)
        self.atr_multiplier = self.risk_config.get('stop_loss', {}).get('atr_multiplier', 2.0)
        self.rr_ratio = self.risk_config.get('take_profit', {}).get('risk_reward_ratio', 2.0)

        # Circuit breaker state
        self._daily_trades = 0
        self._circuit_breaker_open = False
        self._last_reset_date = datetime.utcnow().date()

        # Track open positions: symbol -> {'qty': float, 'entry': float, 'atr': float}
        self.open_positions: Dict[str, Dict] = {}

        # Database writer
        self.db_writer = DatabaseWriter(bot_name=self.bot_name)
        try:
            self.db_writer.connect()
            self._seed_bot_config()
            logger.info("Connected to admin platform database")
        except Exception as e:
            logger.warning(f"Could not connect to database: {e}")
            self.db_writer = None

        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        logger.info(f"CryptoBotV2 initialized — symbols: {self.symbols}, paper=True")

    def _load_config(self, path: str) -> Dict:
        try:
            with open(path) as f:
                cfg = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {path}")
            return cfg
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def _seed_bot_config(self):
        try:
            cursor = self.db_writer.conn.cursor()
            cursor.execute("""
                INSERT INTO bot_configs (id, bot_name, strategy_name, symbols, config, created_at, updated_at)
                VALUES (gen_random_uuid()::text, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (bot_name) DO UPDATE SET
                    strategy_name = EXCLUDED.strategy_name,
                    symbols = EXCLUDED.symbols,
                    updated_at = NOW()
            """, (
                self.bot_name, STRATEGY_NAME,
                ','.join(self.symbols),
                str(self.config)
            ))
            self.db_writer.conn.commit()
            logger.info(f"Bot config seeded: strategy={STRATEGY_NAME}")
        except Exception as e:
            logger.warning(f"Could not seed bot config: {e}")
            try:
                self.db_writer.conn.rollback()
            except Exception:
                pass

    def _handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.db_writer:
            self.db_writer.disconnect()

    def _ensure_db(self) -> bool:
        if not self.db_writer:
            return False
        try:
            if self.db_writer.conn.closed:
                self.db_writer.connect()
            self.db_writer.conn.cursor().execute('SELECT 1')
            return True
        except Exception:
            try:
                self.db_writer.connect()
                return True
            except Exception:
                return False

    # -----------------------------------------------------------------------
    # Market data
    # -----------------------------------------------------------------------

    def get_market_data(self, symbol: str, hours: int = 300) -> pd.DataFrame:
        """Fetch hourly bars for a crypto symbol."""
        request = CryptoBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Hour,
            start=datetime.now(timezone.utc) - timedelta(hours=hours),
            end=datetime.now(timezone.utc),
        )
        bars = self.data_client.get_crypto_bars(request)
        df = bars.df
        if hasattr(df.index, 'names') and 'symbol' in df.index.names:
            df = df.xs(symbol, level='symbol')
        df = df.sort_index()
        return df

    # -----------------------------------------------------------------------
    # Account
    # -----------------------------------------------------------------------

    def get_account(self) -> Dict[str, float]:
        acct = self.trading_client.get_account()
        return {
            'equity': float(acct.equity),
            'cash': float(acct.cash),
            'buying_power': float(acct.buying_power),
            'portfolio_value': float(acct.portfolio_value),
        }

    def get_alpaca_positions(self) -> List[Any]:
        try:
            return [p for p in self.trading_client.get_all_positions()
                    if str(p.asset_class) == 'AssetClass.CRYPTO']
        except Exception:
            return []

    # -----------------------------------------------------------------------
    # Order execution
    # -----------------------------------------------------------------------

    def _wait_for_fill(self, order_id: str, timeout: int = 20) -> Optional[Any]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                o = self.trading_client.get_order_by_id(order_id)
                if o.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED):
                    return o
            except Exception:
                pass
            time.sleep(1)
        return None

    def execute_buy(self, symbol: str, qty: float, stop_loss: float, take_profit: float) -> bool:
        """Submit market buy + SL stop + TP limit after fill confirmation."""
        try:
            order = self.trading_client.submit_order(MarketOrderRequest(
                symbol=symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.GTC
            ))
            logger.info(f"BUY submitted: {qty} {symbol}")

            filled = self._wait_for_fill(str(order.id), timeout=20)
            fill_price = float(filled.filled_avg_price) if filled and filled.filled_avg_price else 0.0
            filled_qty = float(filled.filled_qty) if filled and filled.filled_qty else qty

            if stop_loss and stop_loss > 0:
                try:
                    self.trading_client.submit_order(StopOrderRequest(
                        symbol=symbol, qty=filled_qty, side=OrderSide.SELL,
                        time_in_force=TimeInForce.GTC, stop_price=round(stop_loss, 2)
                    ))
                    logger.info(f"Stop loss placed @ ${stop_loss:.2f}")
                except Exception as e:
                    logger.warning(f"Stop loss failed for {symbol}: {e}")

            if take_profit and take_profit > 0:
                try:
                    self.trading_client.submit_order(LimitOrderRequest(
                        symbol=symbol, qty=filled_qty, side=OrderSide.SELL,
                        time_in_force=TimeInForce.GTC, limit_price=round(take_profit, 2)
                    ))
                    logger.info(f"Take profit placed @ ${take_profit:.2f}")
                except Exception as e:
                    logger.warning(f"Take profit failed for {symbol}: {e}")

            self.open_positions[symbol] = {
                'qty': filled_qty, 'entry': fill_price,
                'stop_loss': stop_loss, 'take_profit': take_profit
            }

            if self.db_writer and self._ensure_db():
                try:
                    self.db_writer.record_trade_entry(
                        symbol=symbol, side='BUY', quantity=filled_qty,
                        entry_price=fill_price, strategy=STRATEGY_NAME,
                        signal_type='buy_signal', entry_reason='multi_indicator'
                    )
                except Exception as e:
                    logger.warning(f"Could not record trade entry: {e}")

            self._daily_trades += 1
            return True

        except Exception as e:
            logger.error(f"execute_buy failed for {symbol}: {e}", exc_info=True)
            return False

    def execute_sell(self, symbol: str) -> bool:
        """Close long position via market sell."""
        try:
            pos_info = self.open_positions.get(symbol)
            qty = pos_info['qty'] if pos_info else None

            # Cancel any open SL/TP orders for this symbol first
            try:
                open_orders = self.trading_client.get_orders()
                for o in open_orders:
                    if o.symbol == symbol and o.side == OrderSide.SELL:
                        self.trading_client.cancel_order_by_id(str(o.id))
                        logger.info(f"Cancelled open SELL order {o.id} for {symbol}")
            except Exception as e:
                logger.warning(f"Could not cancel open orders for {symbol}: {e}")

            # Market sell to close
            if qty:
                order = self.trading_client.submit_order(MarketOrderRequest(
                    symbol=symbol, qty=qty, side=OrderSide.SELL, time_in_force=TimeInForce.GTC
                ))
            else:
                self.trading_client.close_position(symbol)

            logger.info(f"SELL submitted: close {symbol}")

            filled = self._wait_for_fill(str(order.id) if qty else '', timeout=20) if qty else None
            exit_price = float(filled.filled_avg_price) if filled and filled.filled_avg_price else 0.0

            if self.db_writer and self._ensure_db() and pos_info:
                try:
                    cursor = self.db_writer.conn.cursor()
                    cursor.execute("""
                        UPDATE trades SET status='CLOSED', exit_price=%s, exited_at=NOW(),
                        updated_at=NOW(),
                        pnl = (exit_price - entry_price) * quantity,
                        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
                        WHERE bot_name=%s AND symbol=%s AND status='OPEN'
                        ORDER BY entered_at DESC LIMIT 1
                    """, (exit_price, self.bot_name, symbol))
                    self.db_writer.conn.commit()
                except Exception as e:
                    logger.warning(f"Could not close trade in DB: {e}")
                    try:
                        self.db_writer.conn.rollback()
                    except Exception:
                        pass

            self.open_positions.pop(symbol, None)
            self._daily_trades += 1
            return True

        except Exception as e:
            logger.error(f"execute_sell failed for {symbol}: {e}", exc_info=True)
            return False

    # -----------------------------------------------------------------------
    # Circuit breakers
    # -----------------------------------------------------------------------

    def _reset_daily_counters_if_needed(self):
        today = datetime.utcnow().date()
        if today != self._last_reset_date:
            self._daily_trades = 0
            self._circuit_breaker_open = False
            self._last_reset_date = today
            logger.info("Daily circuit breaker counters reset")

    def _check_circuit_breakers(self, equity: float) -> Optional[str]:
        limits = self.risk_config.get('limits', {})
        max_daily_trades = limits.get('max_daily_trades', 20)
        max_positions = limits.get('max_positions', 3)

        if self._circuit_breaker_open:
            return "Circuit breaker already open"
        if self._daily_trades >= max_daily_trades:
            return f"Max daily trades reached ({self._daily_trades}/{max_daily_trades})"
        if len(self.open_positions) >= max_positions:
            return f"Max positions reached ({len(self.open_positions)}/{max_positions})"
        return None

    # -----------------------------------------------------------------------
    # Strategy cycle
    # -----------------------------------------------------------------------

    def run_strategy_cycle(self):
        self._reset_daily_counters_if_needed()
        account = self.get_account()
        equity = account['equity']

        halt = self._check_circuit_breakers(equity)
        if halt:
            self._circuit_breaker_open = True
            logger.warning(f"CIRCUIT BREAKER OPEN: {halt}")
            return

        for symbol in self.symbols:
            try:
                df = self.get_market_data(symbol, hours=300)
                if df.empty or len(df) < 60:
                    logger.debug(f"{symbol}: insufficient data ({len(df)} bars)")
                    continue

                strategy = self.strategies[symbol]
                df = strategy.calculate_indicators(df)
                sig = strategy.generate_signal(df)

                latest = df.iloc[-1]
                current_price = float(latest['close'])
                atr = float(latest['atr']) if not pd.isna(latest['atr']) else 0.0

                has_position = symbol in self.open_positions

                if sig == 'BUY' and not has_position:
                    qty = strategy.calculate_position_size(equity, current_price, atr, self.risk_pct)
                    if qty <= 0:
                        logger.warning(f"Skipping BUY {symbol} — position size is zero")
                        continue
                    stop_loss = current_price - (atr * self.atr_multiplier)
                    take_profit = current_price + (atr * self.atr_multiplier * self.rr_ratio)
                    logger.info(
                        f"Executing BUY {qty:.6f} {symbol} @ ~${current_price:.2f} "
                        f"SL=${stop_loss:.2f} TP=${take_profit:.2f}"
                    )
                    self.execute_buy(symbol, qty, stop_loss, take_profit)

                elif sig == 'SELL' and has_position:
                    logger.info(f"Executing SELL (close long) {symbol} @ ~${current_price:.2f}")
                    self.execute_sell(symbol)

                else:
                    logger.debug(f"{symbol}: signal={sig}, has_position={has_position} — no action")

            except Exception as e:
                logger.error(f"Strategy cycle error for {symbol}: {e}", exc_info=True)

    # -----------------------------------------------------------------------
    # Heartbeat
    # -----------------------------------------------------------------------

    def send_heartbeat(self):
        if not self.db_writer or not self._ensure_db():
            return
        try:
            account = self.get_account()
            alpaca_positions = self.get_alpaca_positions()
            pos_dicts = []
            for p in alpaca_positions:
                pos_dicts.append({
                    'symbol': p.symbol,
                    'quantity': float(p.qty),
                    'entry_price': float(p.avg_entry_price),
                    'current_price': float(p.current_price),
                    'market_value': float(p.market_value),
                    'cost_basis': float(p.cost_basis),
                    'unrealized_pl': float(p.unrealized_pl),
                    'unrealized_plpc': float(p.unrealized_plpc),
                    'strategy': STRATEGY_NAME,
                })
            trades_count = 0
            try:
                cursor = self.db_writer.conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM trades WHERE bot_name = %s', (self.bot_name,))
                trades_count = cursor.fetchone()[0]
            except Exception:
                pass

            self.db_writer.update_status(
                account_info={
                    'equity': account['equity'],
                    'balance': account['cash'],
                    'buying_power': account['buying_power'],
                    'portfolio_value': account['portfolio_value'],
                },
                positions=pos_dicts,
                trades_count=trades_count
            )
            if pos_dicts:
                self.db_writer.update_positions(pos_dicts)
            logger.debug(f"Heartbeat — equity: ${account['equity']:.2f}, positions: {len(pos_dicts)}")
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}", exc_info=True)

    # -----------------------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------------------

    def run(self):
        logger.info(f"Starting {self.bot_name} V2 (Alpaca paper trading)...")
        self.send_heartbeat()

        heartbeat_interval = 30
        strategy_interval = self.config.get('strategy', {}).get('schedule', {}).get('check_interval', 300)

        last_heartbeat = time.time()
        last_strategy = time.time()

        while self.running:
            try:
                now = time.time()

                if now - last_heartbeat >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat = now

                if now - last_strategy >= strategy_interval:
                    logger.info("Running crypto strategy cycle...")
                    self.run_strategy_cycle()
                    last_strategy = now

                time.sleep(1)

            except Exception as e:
                logger.error(f"Main loop error: {e}", exc_info=True)
                time.sleep(10)

        logger.info("CryptoBotV2 stopped")


if __name__ == '__main__':
    bot = CryptoBotV2()
    bot.run()
