"""Crypto trading bot using Coinbase Advanced Trade API."""

import time
from datetime import datetime
from typing import Dict, List, Optional

import structlog
from coinbase.rest import RESTClient

from quantshift_core import StateManager, get_settings

logger = structlog.get_logger()


class CryptoBot:
    """Cryptocurrency trading bot for Coinbase."""

    def __init__(self, api_key: str, api_secret: str) -> None:
        """Initialize crypto bot."""
        self.client = RESTClient(api_key=api_key, api_secret=api_secret)
        self.state = StateManager(bot_name="crypto-bot")
        self.settings = get_settings()
        
        # Register shutdown handler
        self.state.register_shutdown_handler(self._shutdown)
        
        logger.info("crypto_bot_initialized")

    def _shutdown(self) -> None:
        """Cleanup on shutdown."""
        logger.info("crypto_bot_shutting_down")
        # Close any open positions if needed
        # Save final state
        positions = self.get_positions()
        for position in positions:
            self.state.save_position(
                position["product_id"],
                {
                    "size": position["size"],
                    "avg_price": position["avg_price"],
                    "side": position["side"],
                }
            )

    def get_account(self) -> Dict:
        """Get account information."""
        try:
            accounts = self.client.get_accounts()
            return accounts
        except Exception as e:
            logger.error("get_account_failed", error=str(e))
            raise

    def get_product_info(self, product_id: str) -> Dict:
        """Get product information."""
        try:
            product = self.client.get_product(product_id)
            return product
        except Exception as e:
            logger.error("get_product_failed", product_id=product_id, error=str(e))
            raise

    def get_candles(
        self,
        product_id: str,
        start: str,
        end: str,
        granularity: str = "ONE_HOUR"
    ) -> List[Dict]:
        """Get historical candles."""
        try:
            candles = self.client.get_candles(
                product_id=product_id,
                start=start,
                end=end,
                granularity=granularity
            )
            return candles.get("candles", [])
        except Exception as e:
            logger.error("get_candles_failed", product_id=product_id, error=str(e))
            raise

    def place_market_order(
        self,
        product_id: str,
        side: str,
        size: str
    ) -> Dict:
        """Place a market order."""
        try:
            order = self.client.market_order_buy(
                product_id=product_id,
                quote_size=size
            ) if side == "BUY" else self.client.market_order_sell(
                product_id=product_id,
                base_size=size
            )
            
            logger.info(
                "market_order_placed",
                product_id=product_id,
                side=side,
                size=size,
                order_id=order.get("order_id")
            )
            
            return order
        except Exception as e:
            logger.error(
                "market_order_failed",
                product_id=product_id,
                side=side,
                error=str(e)
            )
            raise

    def place_limit_order(
        self,
        product_id: str,
        side: str,
        size: str,
        price: str
    ) -> Dict:
        """Place a limit order."""
        try:
            order = self.client.limit_order_gtc_buy(
                product_id=product_id,
                base_size=size,
                limit_price=price
            ) if side == "BUY" else self.client.limit_order_gtc_sell(
                product_id=product_id,
                base_size=size,
                limit_price=price
            )
            
            logger.info(
                "limit_order_placed",
                product_id=product_id,
                side=side,
                size=size,
                price=price,
                order_id=order.get("order_id")
            )
            
            return order
        except Exception as e:
            logger.error(
                "limit_order_failed",
                product_id=product_id,
                side=side,
                error=str(e)
            )
            raise

    def get_positions(self) -> List[Dict]:
        """Get current positions."""
        try:
            accounts = self.client.get_accounts()
            positions = []
            
            for account in accounts.get("accounts", []):
                balance = float(account.get("available_balance", {}).get("value", 0))
                if balance > 0:
                    positions.append({
                        "product_id": account.get("currency"),
                        "size": balance,
                        "avg_price": 0,  # Would need to track this
                        "side": "LONG"
                    })
            
            return positions
        except Exception as e:
            logger.error("get_positions_failed", error=str(e))
            return []

    def run(self) -> None:
        """Main bot loop."""
        logger.info("crypto_bot_starting")
        
        while True:
            try:
                # Send heartbeat
                self.state.heartbeat()
                
                # Check if primary
                if not self.state.is_primary():
                    logger.info("running_as_standby")
                    time.sleep(30)
                    continue
                
                # Main trading logic here
                logger.info("crypto_bot_running")
                
                # Sleep before next iteration
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("crypto_bot_interrupted")
                break
            except Exception as e:
                logger.error("crypto_bot_error", error=str(e))
                time.sleep(60)
