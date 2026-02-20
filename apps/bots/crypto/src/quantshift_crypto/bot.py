"""Crypto trading bot using Coinbase Advanced Trade API."""

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

# Products to trade in sandbox mode
SANDBOX_PRODUCTS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
]

STRATEGY_NAME = "MA_CROSSOVER_CRYPTO"


class CryptoBot:
    """Cryptocurrency trading bot for Coinbase — sandbox mode."""

    def __init__(self, api_key: str, api_secret: str) -> None:
        self.bot_name = "crypto-bot"
        self.running = True

        # Coinbase REST client (sandbox uses same endpoint, just paper funds)
        self.client = RESTClient(api_key=api_key, api_secret=api_secret)

        # Strategy
        self.strategies = {p: CryptoStrategy(product_id=p) for p in SANDBOX_PRODUCTS}

        # Database writer for dashboard visibility
        self.db_writer = CryptoDatabaseWriter(bot_name=self.bot_name)
        try:
            self.db_writer.connect()
            self.db_writer.seed_bot_config(STRATEGY_NAME, SANDBOX_PRODUCTS)
            logger.info("Connected to admin platform database")
        except Exception as e:
            logger.warning(f"Could not connect to admin platform database: {e}")
            self.db_writer = None

        # Track open trade IDs per product (product_id -> db trade_id)
        self.open_trades: Dict[str, str] = {}

        # Signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        logger.info(f"CryptoBot initialized — products: {SANDBOX_PRODUCTS}, mode: sandbox")

    def _handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.db_writer:
            self.db_writer.disconnect()

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
        """Check each product for signals and log (sandbox — no real orders)."""
        for product_id, strategy in self.strategies.items():
            try:
                candles = self.get_candles_for_product(product_id)
                if not candles:
                    continue

                df = strategy.calculate_indicators(candles)
                if df.empty or len(df) < 200:
                    logger.debug(f"{product_id}: not enough candle data ({len(df)} rows)")
                    continue

                signal = strategy.generate_signal(df)
                current_price = self.get_best_bid_ask(product_id)
                if current_price == 0.0:
                    current_price = float(df.iloc[-1]["close"])

                if signal == "BUY" and product_id not in self.open_trades:
                    logger.info(f"SANDBOX SIGNAL: BUY {product_id} @ ${current_price:.4f}")
                    # Record as open trade in DB (sandbox — no actual order)
                    if self.db_writer:
                        trade_id = self.db_writer.record_trade(
                            symbol=product_id,
                            side="BUY",
                            quantity=0.001,  # nominal sandbox qty
                            entry_price=current_price,
                            strategy=STRATEGY_NAME,
                        )
                        if trade_id:
                            self.open_trades[product_id] = trade_id

                elif signal == "SELL" and product_id in self.open_trades:
                    logger.info(f"SANDBOX SIGNAL: SELL {product_id} @ ${current_price:.4f}")
                    if self.db_writer:
                        self.db_writer.close_trade(
                            trade_id=self.open_trades.pop(product_id),
                            exit_price=current_price,
                            exit_reason="sell_signal",
                        )

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
            account = self.get_account_summary()
            trades_count = 0
            positions = []
            try:
                cur = self.db_writer.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM trades WHERE bot_name = %s", (self.bot_name,))
                row = cur.fetchone()
                trades_count = row["count"] if row else 0
            except Exception:
                pass

            # Build position-like dicts from open trades for dashboard
            for product_id, trade_id in self.open_trades.items():
                current_price = self.get_best_bid_ask(product_id)
                positions.append({
                    "symbol": product_id,
                    "quantity": 0.001,
                    "entry_price": current_price,
                    "current_price": current_price,
                    "market_value": current_price * 0.001,
                    "cost_basis": current_price * 0.001,
                    "unrealized_pl": 0.0,
                    "unrealized_plpc": 0.0,
                    "strategy": STRATEGY_NAME,
                })

            self.db_writer.update_status(account, positions, trades_count)
            if positions:
                self.db_writer.update_positions(positions)
            logger.debug(f"Heartbeat sent — equity: ${account['equity']:.2f}, open: {len(self.open_trades)}")
        except Exception as e:
            logger.warning(f"Could not write DB heartbeat: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("CryptoBot starting main loop (sandbox mode)")

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
