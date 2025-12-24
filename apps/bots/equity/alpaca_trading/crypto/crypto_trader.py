"""Crypto trading bot for Alpaca.

Main trading engine that:
- Monitors crypto prices 24/7
- Applies multiple strategies
- Manages positions with stop-loss/take-profit
- Logs all activity
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import pandas as pd
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError

from alpaca_trading.core.config import config
from .crypto_config import crypto_config
from .crypto_strategy import (
    CryptoStrategy,
    RSIStrategy,
    BollingerStrategy,
    MomentumStrategy,
    Signal,
)

logger = logging.getLogger(__name__)


@dataclass
class CryptoPosition:
    """Track an open crypto position."""
    symbol: str
    qty: float
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    strategy: str


class CryptoTrader:
    """Main crypto trading engine."""
    
    def __init__(self):
        self.api = tradeapi.REST(
            config.api_key,
            config.api_secret,
            config.base_url,
            api_version='v2'
        )
        self.config = crypto_config
        
        # Initialize strategies
        self.strategies: List[CryptoStrategy] = [
            RSIStrategy(),
            BollingerStrategy(),
            MomentumStrategy(),
        ]
        
        # Track positions
        self.positions: Dict[str, CryptoPosition] = {}
        
        # Load existing positions
        self._load_existing_positions()
        
        logger.info("CryptoTrader initialized")
        logger.info(f"Monitoring symbols: {self.config.symbols}")
        logger.info(f"Strategies: {[s.name for s in self.strategies]}")
    
    def _load_existing_positions(self):
        """Load existing crypto positions from Alpaca."""
        try:
            positions = self.api.list_positions()
            for pos in positions:
                # Check if it's a crypto position (symbol contains /)
                if "/" in pos.symbol or pos.symbol.endswith("USD"):
                    symbol = pos.symbol if "/" in pos.symbol else f"{pos.symbol[:-3]}/{pos.symbol[-3:]}"
                    self.positions[symbol] = CryptoPosition(
                        symbol=symbol,
                        qty=float(pos.qty),
                        entry_price=float(pos.avg_entry_price),
                        entry_time=datetime.now(),  # Approximate
                        stop_loss=float(pos.avg_entry_price) * (1 - self.config.stop_loss_pct),
                        take_profit=float(pos.avg_entry_price) * (1 + self.config.take_profit_pct),
                        strategy="existing"
                    )
                    logger.info(f"Loaded existing position: {symbol} qty={pos.qty}")
        except Exception as e:
            logger.error(f"Error loading positions: {e}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            account = self.api.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "crypto_status": account.crypto_status if hasattr(account, 'crypto_status') else "unknown"
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {"cash": 0, "portfolio_value": 0, "buying_power": 0}
    
    def get_crypto_price(self, symbol: str) -> Optional[float]:
        """Get current crypto price."""
        try:
            # Alpaca crypto quotes - use get_latest_crypto_quotes (plural)
            quotes = self.api.get_latest_crypto_quotes([symbol], "us")
            if symbol in quotes:
                quote = quotes[symbol]
                return float(quote.ask_price) if quote.ask_price else None
            return None
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_crypto_bars(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical crypto bars."""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            # Use date format that Alpaca accepts (YYYY-MM-DD)
            bars = self.api.get_crypto_bars(
                symbol,
                tradeapi.TimeFrame.Hour,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d")
            ).df
            
            if not bars.empty:
                # Reset index and filter to just this symbol
                bars = bars.reset_index()
                if 'symbol' in bars.columns:
                    bars = bars[bars['symbol'] == symbol]
                bars = bars.set_index('timestamp')
                bars.index = bars.index.tz_localize(None)
            
            return bars
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return pd.DataFrame()
    
    def analyze_symbol(self, symbol: str) -> List[Signal]:
        """Run all strategies on a symbol and return signals."""
        signals = []
        
        price = self.get_crypto_price(symbol)
        if price is None:
            logger.warning(f"Could not get price for {symbol}")
            return signals
        
        bars = self.get_crypto_bars(symbol)
        if bars.empty:
            logger.warning(f"Could not get bars for {symbol}")
            return signals
        
        for strategy in self.strategies:
            try:
                signal = strategy.analyze(symbol, bars, price)
                signals.append(signal)
                if signal.action != "HOLD":
                    logger.info(f"Signal: {signal}")
            except Exception as e:
                logger.error(f"Error in {strategy.name} for {symbol}: {e}")
        
        return signals
    
    def should_buy(self, signals: List[Signal]) -> bool:
        """Determine if we should buy based on signals."""
        buy_signals = [s for s in signals if s.action == "BUY"]
        if not buy_signals:
            return False
        
        # Require at least 2 strategies to agree, or 1 with high strength
        if len(buy_signals) >= 2:
            return True
        if buy_signals[0].strength >= 0.7:
            return True
        
        return False
    
    def should_sell(self, signals: List[Signal]) -> bool:
        """Determine if we should sell based on signals."""
        sell_signals = [s for s in signals if s.action == "SELL"]
        if not sell_signals:
            return False
        
        # Require at least 2 strategies to agree, or 1 with high strength
        if len(sell_signals) >= 2:
            return True
        if sell_signals[0].strength >= 0.7:
            return True
        
        return False
    
    def place_buy_order(self, symbol: str, signals: List[Signal]) -> Optional[str]:
        """Place a buy order for crypto."""
        if symbol in self.positions:
            logger.info(f"Already have position in {symbol}")
            return None
        
        if len(self.positions) >= self.config.max_positions:
            logger.info(f"Max positions ({self.config.max_positions}) reached")
            return None
        
        price = self.get_crypto_price(symbol)
        if price is None:
            return None
        
        account = self.get_account_info()
        qty = self.config.position_size_usd / price
        
        # Round to reasonable precision
        qty = round(qty, 6)
        
        if qty * price > account["buying_power"]:
            logger.warning(f"Insufficient buying power for {symbol}")
            return None
        
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            
            # Track position
            self.positions[symbol] = CryptoPosition(
                symbol=symbol,
                qty=qty,
                entry_price=price,
                entry_time=datetime.now(),
                stop_loss=price * (1 - self.config.stop_loss_pct),
                take_profit=price * (1 + self.config.take_profit_pct),
                strategy=signals[0].strategy if signals else "unknown"
            )
            
            logger.info(f"BUY order placed: {symbol} qty={qty} @ ~${price:.2f}")
            return order.id
            
        except APIError as e:
            logger.error(f"Order failed for {symbol}: {e}")
            return None
    
    def place_sell_order(self, symbol: str, reason: str = "signal") -> Optional[str]:
        """Place a sell order to close position."""
        if symbol not in self.positions:
            logger.warning(f"No position to sell for {symbol}")
            return None
        
        position = self.positions[symbol]
        
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=position.qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            # Calculate P&L
            current_price = self.get_crypto_price(symbol) or position.entry_price
            pnl = (current_price - position.entry_price) * position.qty
            pnl_pct = (current_price - position.entry_price) / position.entry_price * 100
            
            logger.info(f"SELL order placed: {symbol} qty={position.qty} reason={reason} P&L=${pnl:.2f} ({pnl_pct:.1f}%)")
            
            # Remove from tracking
            del self.positions[symbol]
            
            return order.id
            
        except APIError as e:
            logger.error(f"Sell order failed for {symbol}: {e}")
            return None
    
    def check_stop_loss_take_profit(self):
        """Check all positions for stop-loss or take-profit triggers."""
        for symbol, position in list(self.positions.items()):
            price = self.get_crypto_price(symbol)
            if price is None:
                continue
            
            if price <= position.stop_loss:
                logger.info(f"Stop-loss triggered for {symbol} @ ${price:.2f}")
                self.place_sell_order(symbol, reason="stop_loss")
            elif price >= position.take_profit:
                logger.info(f"Take-profit triggered for {symbol} @ ${price:.2f}")
                self.place_sell_order(symbol, reason="take_profit")
    
    def run_once(self) -> Dict[str, Any]:
        """Run one iteration of the trading loop."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "signals": [],
            "orders": [],
            "positions": len(self.positions),
        }
        
        # Check stop-loss/take-profit first
        self.check_stop_loss_take_profit()
        
        # Analyze each symbol
        for symbol in self.config.symbols:
            signals = self.analyze_symbol(symbol)
            results["signals"].extend([str(s) for s in signals if s.action != "HOLD"])
            
            if self.should_buy(signals):
                order_id = self.place_buy_order(symbol, signals)
                if order_id:
                    results["orders"].append(f"BUY {symbol}")
            
            elif symbol in self.positions and self.should_sell(signals):
                order_id = self.place_sell_order(symbol, reason="signal")
                if order_id:
                    results["orders"].append(f"SELL {symbol}")
        
        return results
    
    def run_loop(self):
        """Run the trading bot continuously."""
        logger.info("Starting crypto trading loop...")
        logger.info(f"Check interval: {self.config.check_interval_minutes} minutes")
        
        while self.config.trading_enabled:
            try:
                results = self.run_once()
                
                if results["signals"] or results["orders"]:
                    logger.info(f"Cycle complete: {len(results['signals'])} signals, {len(results['orders'])} orders")
                
                # Sleep until next check
                time.sleep(self.config.check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Shutting down crypto trader...")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the crypto trader."""
        account = self.get_account_info()
        
        position_details = []
        for symbol, pos in self.positions.items():
            current_price = self.get_crypto_price(symbol) or pos.entry_price
            pnl = (current_price - pos.entry_price) * pos.qty
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
            position_details.append({
                "symbol": symbol,
                "qty": pos.qty,
                "entry_price": pos.entry_price,
                "current_price": current_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "stop_loss": pos.stop_loss,
                "take_profit": pos.take_profit,
                "strategy": pos.strategy,
            })
        
        return {
            "account": account,
            "positions": position_details,
            "symbols_monitored": self.config.symbols,
            "strategies": [s.name for s in self.strategies],
            "trading_enabled": self.config.trading_enabled,
        }


def main():
    """Entry point for crypto trader."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    trader = CryptoTrader()
    
    # Print initial status
    status = trader.get_status()
    logger.info(f"Account: ${status['account']['portfolio_value']:,.2f}")
    logger.info(f"Positions: {len(status['positions'])}")
    
    # Run the trading loop
    trader.run_loop()


if __name__ == "__main__":
    main()
