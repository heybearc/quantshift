"""Crypto trading bot using Coinbase Advanced Trade API — dry-run paper trading."""

import os
import time
import signal
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from coinbase.rest import RESTClient

from quantshift_crypto.strategy import CryptoStrategy
from quantshift_crypto.database_writer import CryptoDatabaseWriter

logger = logging.getLogger(__name__)

PRODUCTS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
]

STRATEGY_NAME = "MA_CROSSOVER_CRYPTO"

# Dry-run paper trading — simulated starting balance
PAPER_BALANCE = 10_000.0

# Risk / circuit breaker limits
RISK_PCT = 0.01          # 1% of balance risked per trade
MAX_POSITIONS = 3        # max concurrent open positions
MAX_DAILY_TRADES = 20    # circuit breaker
MAX_DAILY_LOSS_PCT = 0.05  # halt if daily loss exceeds 5% of starting balance


class CryptoBot:
    """Cryptocurrency trading bot — dry-run paper trading on Coinbase market data."""

    def __init__(self, api_key: str, api_secret: str) -> None:
        self.bot_name = "crypto-bot"
        self.running = True

        self.client = RESTClient(api_key=api_key, api_secret=api_secret)
        self.strategies = {p: CryptoStrategy(product_id=p) for p in PRODUCTS}

        # Paper trading state
        self.paper_balance = PAPER_BALANCE
        self.paper_balance_start = PAPER_BALANCE
        # open_trades: product_id -> {trade_id, qty, entry_price, stop_loss, take_profit}
        self.open_trades: Dict[str, Dict] = {}

        # Circuit breaker state (reset daily)
        self._daily_trades = 0
        self._daily_loss = 0.0
        self._circuit_breaker_open = False
        self._last_reset_date = datetime.now(timezone.utc).date()

        # Database writer
        self.db_writer = CryptoDatabaseWriter(bot_name=self.bot_name)
        try:
            self.db_writer.connect()
            self.db_writer.seed_bot_config(STRATEGY_NAME, PRODUCTS)
            logger.info("Connected to admin platform database")
        except Exception as e:
            logger.warning(f"Could not connect to admin platform database: {e}")
            self.db_writer = None

        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        logger.info(
            f"CryptoBot initialized — products: {PRODUCTS}, "
            f"mode: DRY-RUN paper trading, balance: ${self.paper_balance:,.2f}"
        )

    def _handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.db_writer:
            self.db_writer.disconnect()

    # ------------------------------------------------------------------
    # Circuit breakers
    # ------------------------------------------------------------------

    def _reset_daily_counters_if_needed(self):
        today = datetime.now(timezone.utc).date()
        if today != self._last_reset_date:
            self._daily_trades = 0
            self._daily_loss = 0.0
            self._circuit_breaker_open = False
            self._last_reset_date = today
            logger.info("Daily circuit breaker counters reset")

    def _check_circuit_breakers(self) -> Optional[str]:
        if self._circuit_breaker_open:
            return "Circuit breaker already open"
        if self._daily_trades >= MAX_DAILY_TRADES:
            return f"Max daily trades reached ({self._daily_trades}/{MAX_DAILY_TRADES})"
        if len(self.open_trades) >= MAX_POSITIONS:
            return f"Max positions reached ({len(self.open_trades)}/{MAX_POSITIONS})"
        daily_loss_pct = self._daily_loss / self.paper_balance_start
        if daily_loss_pct >= MAX_DAILY_LOSS_PCT:
            return f"Max daily loss breached ({daily_loss_pct:.1%} >= {MAX_DAILY_LOSS_PCT:.1%})"
        return None

    # ------------------------------------------------------------------
    # Account helpers
    # ------------------------------------------------------------------

    def get_account_summary(self) -> Dict[str, float]:
        """Return a summary of USD account balance."""
        try:
            resp = self.client.get_accounts()
            accounts = resp.get("accounts", []) if isinstance(resp, dict) else getattr(resp, "accounts", [])
            total_usd = 0.0
            for acct in accounts:
                currency = acct.get("currency", "") if isinstance(acct, dict) else getattr(acct, "currency", "")
                if currency == "USD":
                    bal = acct.get("available_balance", {}) if isinstance(acct, dict) else getattr(acct, "available_balance", {})
                    val = bal.get("value", 0) if isinstance(bal, dict) else getattr(bal, "value", 0)
                    total_usd += float(val)
            return {
                "equity": total_usd,
                "cash": total_usd,
                "buying_power": total_usd,
                "portfolio_value": total_usd,
            }
        except Exception as e:
            logger.error(f"get_account_summary failed: {e}")
            return {"equity": 0, "cash": 0, "buying_power": 0, "portfolio_value": 0}

    def get_candles_for_product(self, product_id: str) -> List[Dict]:
        """Fetch recent hourly candles for a product."""
        try:
            end_ts = int(datetime.now(timezone.utc).timestamp())
            start_ts = int((datetime.now(timezone.utc) - timedelta(hours=250)).timestamp())
            resp = self.client.get_candles(
                product_id=product_id,
                start=str(start_ts),
                end=str(end_ts),
                granularity="ONE_HOUR",
            )
            candles = resp.get("candles", []) if isinstance(resp, dict) else getattr(resp, "candles", [])
            return [c if isinstance(c, dict) else c.__dict__ for c in candles]
        except Exception as e:
            logger.error(f"get_candles failed for {product_id}: {e}")
            return []

    def get_best_bid_ask(self, product_id: str) -> float:
        """Get current mid price for a product."""
        try:
            resp = self.client.get_best_bid_ask(product_ids=[product_id])
            pricebooks = resp.get("pricebooks", []) if isinstance(resp, dict) else getattr(resp, "pricebooks", [])
            if pricebooks:
                pb = pricebooks[0]
                bids = pb.get("bids", []) if isinstance(pb, dict) else getattr(pb, "bids", [])
                asks = pb.get("asks", []) if isinstance(pb, dict) else getattr(pb, "asks", [])
                if bids and asks:
                    bid = float(bids[0].get("price", 0) if isinstance(bids[0], dict) else getattr(bids[0], "price", 0))
                    ask = float(asks[0].get("price", 0) if isinstance(asks[0], dict) else getattr(asks[0], "price", 0))
                    return (bid + ask) / 2
        except Exception as e:
            logger.debug(f"get_best_bid_ask failed for {product_id}: {e}")
        return 0.0

    # ------------------------------------------------------------------
    # Strategy cycle
    # ------------------------------------------------------------------

    def run_strategy_cycle(self):
        """Run strategy on real Coinbase market data — dry-run, no real orders placed."""
        self._reset_daily_counters_if_needed()

        halt = self._check_circuit_breakers()
        if halt:
            self._circuit_breaker_open = True
            logger.warning(f"CIRCUIT BREAKER OPEN — skipping cycle: {halt}")
            return

        for product_id, strategy in self.strategies.items():
            try:
                candles = self.get_candles_for_product(product_id)
                if not candles:
                    continue

                df = strategy.calculate_indicators(candles)
                if df.empty or len(df) < 200:
                    logger.debug(f"{product_id}: not enough candle data ({len(df)} rows)")
                    continue

                sig = strategy.generate_signal(df)
                current_price = self.get_best_bid_ask(product_id)
                if current_price == 0.0:
                    current_price = float(df.iloc[-1]["close"])

                latest = df.iloc[-1]
                atr = float(latest.get("atr", 0)) if not df.empty else 0.0

                has_position = product_id in self.open_trades

                if sig == "BUY" and not has_position:
                    # ATR-based position sizing
                    qty = strategy.calculate_position_size(
                        account_balance=self.paper_balance,
                        current_price=current_price,
                        atr=atr if atr > 0 else current_price * 0.02,
                        risk_percent=RISK_PCT,
                    )
                    qty = max(qty, 0.000001)  # floor
                    stop_loss = current_price - (atr * 2) if atr > 0 else current_price * 0.98
                    take_profit = current_price + (atr * 4) if atr > 0 else current_price * 1.04
                    notional = qty * current_price

                    logger.info(
                        f"[DRY-RUN] BUY {qty:.6f} {product_id} @ ${current_price:.4f} "
                        f"notional=${notional:.2f} SL=${stop_loss:.4f} TP=${take_profit:.4f}"
                    )

                    if self.db_writer:
                        trade_id = self.db_writer.record_trade(
                            symbol=product_id,
                            side="BUY",
                            quantity=qty,
                            entry_price=current_price,
                            strategy=STRATEGY_NAME,
                        )
                        if trade_id:
                            self.open_trades[product_id] = {
                                "trade_id": trade_id,
                                "qty": qty,
                                "entry_price": current_price,
                                "stop_loss": stop_loss,
                                "take_profit": take_profit,
                            }
                            self._daily_trades += 1

                elif sig == "SELL" and has_position:
                    pos = self.open_trades.pop(product_id)
                    pnl = (current_price - pos["entry_price"]) * pos["qty"]
                    self._daily_loss += max(0.0, -pnl)  # track losses only
                    logger.info(
                        f"[DRY-RUN] SELL {pos['qty']:.6f} {product_id} @ ${current_price:.4f} "
                        f"P&L=${pnl:+.4f}"
                    )
                    if self.db_writer:
                        self.db_writer.close_trade(
                            trade_id=pos["trade_id"],
                            exit_price=current_price,
                            exit_reason="sell_signal",
                        )
                    self._daily_trades += 1

                else:
                    # Check stop loss / take profit on open positions
                    if has_position:
                        pos = self.open_trades[product_id]
                        if current_price <= pos["stop_loss"]:
                            pnl = (current_price - pos["entry_price"]) * pos["qty"]
                            self._daily_loss += abs(pnl)
                            logger.info(
                                f"[DRY-RUN] STOP LOSS hit {product_id} @ ${current_price:.4f} "
                                f"P&L=${pnl:+.4f}"
                            )
                            self.open_trades.pop(product_id)
                            if self.db_writer:
                                self.db_writer.close_trade(
                                    trade_id=pos["trade_id"],
                                    exit_price=current_price,
                                    exit_reason="stop_loss",
                                )
                            self._daily_trades += 1
                        elif current_price >= pos["take_profit"]:
                            pnl = (current_price - pos["entry_price"]) * pos["qty"]
                            logger.info(
                                f"[DRY-RUN] TAKE PROFIT hit {product_id} @ ${current_price:.4f} "
                                f"P&L=${pnl:+.4f}"
                            )
                            self.open_trades.pop(product_id)
                            if self.db_writer:
                                self.db_writer.close_trade(
                                    trade_id=pos["trade_id"],
                                    exit_price=current_price,
                                    exit_reason="take_profit",
                                )
                            self._daily_trades += 1

            except Exception as e:
                logger.error(f"Strategy cycle error for {product_id}: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    def send_heartbeat(self):
        """Write heartbeat to DB so dashboard shows RUNNING."""
        if not self.db_writer:
            return
        try:
            trades_count = 0
            positions = []
            try:
                cur = self.db_writer.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM trades WHERE bot_name = %s", (self.bot_name,))
                row = cur.fetchone()
                trades_count = row["count"] if row else 0
            except Exception:
                pass

            # Build position dicts from open dry-run trades with live prices
            total_unrealized_pl = 0.0
            for product_id, pos in self.open_trades.items():
                current_price = self.get_best_bid_ask(product_id)
                if current_price == 0.0:
                    current_price = pos["entry_price"]
                qty = pos["qty"]
                market_value = qty * current_price
                cost_basis = qty * pos["entry_price"]
                unrealized_pl = market_value - cost_basis
                unrealized_plpc = (unrealized_pl / cost_basis) if cost_basis else 0.0
                total_unrealized_pl += unrealized_pl
                positions.append({
                    "symbol": product_id,
                    "quantity": qty,
                    "entry_price": pos["entry_price"],
                    "current_price": current_price,
                    "market_value": market_value,
                    "cost_basis": cost_basis,
                    "unrealized_pl": unrealized_pl,
                    "unrealized_plpc": unrealized_plpc,
                    "stop_loss": pos["stop_loss"],
                    "take_profit": pos["take_profit"],
                    "strategy": STRATEGY_NAME,
                })

            paper_equity = self.paper_balance + total_unrealized_pl
            account_info = {
                "equity": paper_equity,
                "cash": self.paper_balance,
                "buying_power": self.paper_balance,
                "portfolio_value": paper_equity,
            }

            self.db_writer.update_status(account_info, positions, trades_count)
            self.db_writer.update_positions(positions)
            logger.debug(
                f"Heartbeat — paper equity: ${paper_equity:.2f}, "
                f"open: {len(self.open_trades)}, trades: {trades_count}"
            )
        except Exception as e:
            logger.warning(f"Could not write DB heartbeat: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("CryptoBot starting main loop (DRY-RUN paper trading)")

        heartbeat_interval = 30
        strategy_interval = 300   # 5 minutes — hourly candles don't need faster
        last_heartbeat = 0.0
        last_strategy = 0.0

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

            except KeyboardInterrupt:
                logger.info("CryptoBot interrupted")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}", exc_info=True)
                time.sleep(10)

        logger.info("CryptoBot stopped")
