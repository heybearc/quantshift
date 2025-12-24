"""Autonomous Trading Bot for Small Account Challenge.

Fully automated trading bot that manages the $500 to $1000 challenge
without user input. Trades crypto 24/7 and stocks during market hours.

Features:
- Automatic position entry based on signals
- Automatic stop-loss and take-profit management
- Position sizing based on simulated balance
- Trade logging and P&L tracking
- Runs continuously until goal is reached
"""

import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError

from alpaca_trading.core.config import config
from alpaca_trading.challenges.small_account_challenge import SmallAccountChallenge, ChallengeConfig
from alpaca_trading.crypto.crypto_config import crypto_config
from alpaca_trading.indicators import AdvancedSignalGenerator

logger = logging.getLogger(__name__)

# Bot state file
BOT_STATE_FILE = Path(__file__).parent.parent.parent / "data" / "autonomous_bot_state.json"


@dataclass
class Position:
    """Track an open position."""
    symbol: str
    side: str  # "long" or "short"
    qty: float
    entry_price: float
    entry_time: str
    stop_loss: float
    take_profit: float
    order_id: str
    asset_type: str  # "crypto" or "stock"


class AutonomousTrader:
    """Fully autonomous trading bot for the small account challenge."""
    
    def __init__(self, starting_capital: float = 500.0, goal: float = 1000.0):
        self.api = tradeapi.REST(
            config.api_key,
            config.api_secret,
            config.base_url,
            api_version='v2'
        )
        
        # Initialize challenge tracker
        self.challenge = SmallAccountChallenge(starting_capital, goal)
        
        # Trading parameters
        self.position_size_pct = 0.20  # 20% per position
        self.max_positions = 3
        self.stop_loss_pct = 0.025  # 2.5%
        self.take_profit_pct = 0.05  # 5%
        
        # Strategy parameters
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.momentum_threshold = 0.02
        
        # Crypto symbols (24/7 trading)
        self.crypto_symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD"]
        
        # State
        self.positions: Dict[str, Position] = {}
        self.running = False
        self.check_interval = 300  # 5 minutes
        
        # Advanced indicators
        self.signal_generator = AdvancedSignalGenerator()
        
        # Ensure data directory exists
        BOT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
        
        logger.info("="*50)
        logger.info("AUTONOMOUS TRADER INITIALIZED")
        logger.info(f"Starting Capital: ${starting_capital:,.2f}")
        logger.info(f"Goal: ${goal:,.2f}")
        logger.info(f"Current Balance: ${self.challenge.state.current_balance:,.2f}")
        logger.info("="*50)
    
    def _load_state(self):
        """Load bot state from file."""
        if BOT_STATE_FILE.exists():
            try:
                with open(BOT_STATE_FILE, 'r') as f:
                    data = json.load(f)
                    for symbol, pos_data in data.get("positions", {}).items():
                        self.positions[symbol] = Position(**pos_data)
                    logger.info(f"Loaded {len(self.positions)} existing positions")
            except Exception as e:
                logger.error(f"Error loading state: {e}")
    
    def _save_state(self):
        """Save bot state to file."""
        try:
            with open(BOT_STATE_FILE, 'w') as f:
                json.dump({
                    "positions": {s: asdict(p) for s, p in self.positions.items()},
                    "last_update": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def get_crypto_price(self, symbol: str) -> Optional[float]:
        """Get current crypto price."""
        try:
            quotes = self.api.get_latest_crypto_quotes([symbol], "us")
            if symbol in quotes:
                return float(quotes[symbol].ask_price)
            return None
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_crypto_bars(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Get historical crypto bars."""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            bars = self.api.get_crypto_bars(
                symbol,
                tradeapi.TimeFrame.Hour,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d")
            ).df
            
            if not bars.empty:
                bars = bars.reset_index()
                if 'symbol' in bars.columns:
                    bars = bars[bars['symbol'] == symbol]
                bars = bars.set_index('timestamp')
                bars.index = bars.index.tz_localize(None)
            
            return bars
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI."""
        if len(prices) < period + 1:
            return 50.0
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def calculate_momentum(self, prices: pd.Series, period: int = 6) -> float:
        """Calculate momentum."""
        if len(prices) < period + 1:
            return 0.0
        
        current = prices.iloc[-1]
        past = prices.iloc[-period - 1]
        
        return (current - past) / past if past > 0 else 0.0
    
    def should_buy(self, symbol: str) -> tuple[bool, str, float]:
        """Determine if we should buy a crypto using advanced indicators."""
        bars = self.get_crypto_bars(symbol)
        if bars.empty or len(bars) < 20:
            return False, "Insufficient data", 0
        
        price = self.get_crypto_price(symbol)
        if price is None:
            return False, "No price", 0
        
        # Basic RSI/Momentum check
        rsi = self.calculate_rsi(bars['close'])
        momentum = self.calculate_momentum(bars['close'])
        
        # Calculate previous momentum for reversal detection
        if len(bars) > 7:
            prev_momentum = self.calculate_momentum(bars['close'].iloc[:-1])
        else:
            prev_momentum = momentum
        
        # Use advanced indicators for consensus
        try:
            consensus = self.signal_generator.get_consensus(bars)
            all_signals = self.signal_generator.analyze_all(bars)
            
            # Log indicator signals
            for name, sig in all_signals.items():
                if sig.signal_type in ["BUY", "STRONG_BUY", "SELL", "STRONG_SELL"]:
                    logger.info(f"  {name}: {sig}")
            
            # Moderate consensus buy signal (35% threshold)
            if consensus.signal_type in ["BUY", "STRONG_BUY"] and consensus.strength >= 0.35:
                return True, f"Advanced indicators: {consensus.reason}", consensus.strength
            
            # Also allow single strong indicator signals (≥80%)
            for name, sig in all_signals.items():
                if sig.signal_type in ["BUY", "STRONG_BUY"] and sig.strength >= 0.8:
                    return True, f"Strong {name} signal: {sig.reason}", sig.strength
        except Exception as e:
            logger.warning(f"Advanced indicators failed: {e}, falling back to basic")
        
        # Fallback to basic signals
        # BUY CONDITIONS:
        # 1. RSI oversold (<30) AND momentum turning positive (reversal)
        # 2. RSI very oversold (<20) - extreme condition
        
        if rsi < self.rsi_oversold and prev_momentum < 0 and momentum > 0:
            strength = min(1.0, (self.rsi_oversold - rsi) / 20 + 0.3)
            return True, f"Bullish reversal! RSI={rsi:.1f}, momentum turning positive", strength
        
        if rsi < 20:
            strength = min(1.0, (20 - rsi) / 10)
            return True, f"Extreme oversold RSI={rsi:.1f}", strength
        
        return False, f"No signal (RSI={rsi:.1f}, Mom={momentum:.1%})", 0
    
    def should_sell(self, symbol: str, position: Position) -> tuple[bool, str]:
        """Determine if we should sell a position."""
        price = self.get_crypto_price(symbol)
        if price is None:
            return False, "No price"
        
        # Check stop loss
        if price <= position.stop_loss:
            return True, f"Stop loss hit (${position.stop_loss:.2f})"
        
        # Check take profit
        if price >= position.take_profit:
            return True, f"Take profit hit (${position.take_profit:.2f})"
        
        # Check for bearish reversal
        bars = self.get_crypto_bars(symbol)
        if not bars.empty and len(bars) > 20:
            rsi = self.calculate_rsi(bars['close'])
            momentum = self.calculate_momentum(bars['close'])
            
            if rsi > self.rsi_overbought and momentum < 0:
                return True, f"Bearish reversal (RSI={rsi:.1f})"
        
        return False, "Hold"
    
    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on simulated balance."""
        balance = self.challenge.state.current_balance
        max_position_value = balance * self.position_size_pct
        qty = max_position_value / price
        
        # Round appropriately
        if price > 1000:
            qty = round(qty, 6)  # BTC
        elif price > 100:
            qty = round(qty, 4)  # ETH, SOL
        else:
            qty = round(qty, 2)  # DOGE
        
        return max(0, qty)
    
    def execute_buy(self, symbol: str, reason: str) -> Optional[str]:
        """Execute a buy order."""
        if symbol in self.positions:
            logger.info(f"Already have position in {symbol}")
            return None
        
        if len(self.positions) >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached")
            return None
        
        price = self.get_crypto_price(symbol)
        if price is None:
            return None
        
        qty = self.calculate_position_size(price)
        if qty <= 0:
            logger.warning(f"Position size too small for {symbol}")
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
            position = Position(
                symbol=symbol,
                side="long",
                qty=qty,
                entry_price=price,
                entry_time=datetime.now().isoformat(),
                stop_loss=price * (1 - self.stop_loss_pct),
                take_profit=price * (1 + self.take_profit_pct),
                order_id=order.id,
                asset_type="crypto"
            )
            self.positions[symbol] = position
            self._save_state()
            
            logger.info(f"✅ BUY {qty} {symbol} @ ${price:.2f}")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   Stop: ${position.stop_loss:.2f} | Target: ${position.take_profit:.2f}")
            
            return order.id
            
        except APIError as e:
            logger.error(f"Order failed for {symbol}: {e}")
            return None
    
    def execute_sell(self, symbol: str, reason: str) -> Optional[str]:
        """Execute a sell order and record P&L."""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        price = self.get_crypto_price(symbol)
        if price is None:
            return None
        
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=position.qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            # Calculate P&L
            pnl = (price - position.entry_price) * position.qty
            pnl_pct = (price - position.entry_price) / position.entry_price * 100
            
            # Record trade in challenge
            self.challenge.record_trade(
                symbol=symbol,
                side="sell",
                qty=position.qty,
                price=price,
                pnl=pnl,
                strategy="autonomous",
                notes=reason
            )
            
            logger.info(f"✅ SELL {position.qty} {symbol} @ ${price:.2f}")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
            logger.info(f"   New Balance: ${self.challenge.state.current_balance:.2f}")
            
            # Remove position
            del self.positions[symbol]
            self._save_state()
            
            return order.id
            
        except APIError as e:
            logger.error(f"Sell order failed for {symbol}: {e}")
            return None
    
    def check_positions(self):
        """Check all open positions for exit signals."""
        for symbol, position in list(self.positions.items()):
            should_exit, reason = self.should_sell(symbol, position)
            if should_exit:
                self.execute_sell(symbol, reason)
    
    def scan_for_entries(self):
        """Scan for new entry opportunities."""
        if len(self.positions) >= self.max_positions:
            return
        
        for symbol in self.crypto_symbols:
            if symbol in self.positions:
                continue
            
            should_enter, reason, strength = self.should_buy(symbol)
            if should_enter and strength >= 0.5:
                self.execute_buy(symbol, reason)
    
    def run_cycle(self):
        """Run one trading cycle."""
        logger.info("-" * 40)
        logger.info(f"Trading Cycle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check challenge status
        status = self.challenge.get_status()
        logger.info(f"Balance: ${status['challenge']['current_balance']:.2f} | Progress: {status['challenge']['progress_pct']:.1f}%")
        
        # Check if goal reached
        if status['challenge']['goal_reached']:
            logger.info("🎉 GOAL REACHED! Stopping bot.")
            self.running = False
            return
        
        # Check existing positions for exits
        self.check_positions()
        
        # Scan for new entries
        self.scan_for_entries()
        
        # Log position summary
        if self.positions:
            logger.info(f"Open Positions: {len(self.positions)}")
            for symbol, pos in self.positions.items():
                price = self.get_crypto_price(symbol) or pos.entry_price
                pnl = (price - pos.entry_price) * pos.qty
                logger.info(f"  {symbol}: {pos.qty} @ ${pos.entry_price:.2f} | Current: ${price:.2f} | P&L: ${pnl:+.2f}")
    
    def run(self):
        """Run the autonomous trading bot continuously."""
        logger.info("="*50)
        logger.info("🤖 AUTONOMOUS TRADER STARTING")
        logger.info(f"Check Interval: {self.check_interval} seconds")
        logger.info("="*50)
        
        self.running = True
        
        while self.running:
            try:
                self.run_cycle()
                
                # Check if goal reached
                if self.challenge.state.current_balance >= self.challenge.config.goal:
                    logger.info("🎉🎉🎉 CHALLENGE COMPLETE! 🎉🎉🎉")
                    logger.info(f"Final Balance: ${self.challenge.state.current_balance:.2f}")
                    self.running = False
                    break
                
                # Wait for next cycle
                logger.info(f"Next check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                time.sleep(60)  # Wait a minute before retrying
        
        logger.info("Autonomous trader stopped.")
        self.challenge.print_status()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            "running": self.running,
            "challenge": self.challenge.get_status(),
            "positions": {s: asdict(p) for s, p in self.positions.items()},
            "symbols_monitored": self.crypto_symbols,
            "check_interval": self.check_interval
        }


def main():
    """Entry point for autonomous trader."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start with $500, goal $1000
    trader = AutonomousTrader(starting_capital=500.0, goal=1000.0)
    trader.run()


if __name__ == "__main__":
    main()
