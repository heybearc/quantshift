"""Autonomous Trading Bot for Million Dollar Challenge.

AGGRESSIVE SCALPING BOT for the $1,000 to $1,000,000 challenge.
Uses high-frequency scalping strategy optimized for crypto volatility.

Features:
- Dynamic symbol selection via momentum screener
- Aggressive scalping: 6% take profit, 3% stop loss (2:1 R:R)
- High position turnover - capture frequent small wins
- Focus on high-volatility crypto assets
- Compound gains through frequent profitable trades
- Tracks trades against Million Dollar Challenge
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
from alpaca_trading.challenges.million_dollar_challenge import MillionDollarChallenge
from alpaca_trading.indicators import AdvancedSignalGenerator
from alpaca_trading.screeners.momentum_screener import MomentumScreener, ScreenerResult

logger = logging.getLogger(__name__)

# Bot state file - SEPARATE from small account bot
BOT_STATE_FILE = Path(__file__).parent.parent.parent / "data" / "million_dollar_bot_state.json"


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
    high_water_mark: float = 0.0  # Highest price reached (for trailing stop)


class MillionDollarTrader:
    """Aggressive autonomous trading bot for the Million Dollar Challenge."""
    
    def __init__(self, starting_capital: float = 1000.0):
        self.api = tradeapi.REST(
            config.api_key,
            config.api_secret,
            config.base_url,
            api_version='v2'
        )
        
        # Initialize challenge tracker
        self.challenge = MillionDollarChallenge(starting_capital)
        
        # AGGRESSIVE SCALPING parameters - optimized for live trading with fees
        # Industry standard: 2:1 R:R ratio minimum to account for fees
        # With 0.5% round-trip fees: 2.5% TP - 0.5% fees = 2% net profit
        # With 1% SL + 0.5% fees = 1.5% net loss
        # Net R:R = 2:1.5 = 1.33:1 (need ~43% win rate to break even)
        self.position_size_pct = 0.12  # 12% per position (8 positions = 96% deployed)
        self.max_positions = 8  # More positions = more opportunities to scalp
        self.stop_loss_pct = 0.01  # 1% stop loss - tight risk management
        self.take_profit_pct = 0.025  # 2.5% take profit - gives 2:1 R:R after fees
        
        # Daily loss limit - stop trading if we lose too much in one day
        self.max_daily_loss_pct = 0.03  # 3% max daily loss
        self.daily_loss = 0.0
        self.last_trading_day = None
        
        # Trailing stop parameters
        self.trailing_stop_activation_pct = 0.01  # Activate trailing stop after +1% gain
        self.trailing_stop_distance_pct = 0.01  # Trail 1% below high water mark
        
        # Scalping strategy parameters - very aggressive entry
        self.rsi_oversold = 40  # Buy even earlier for scalping
        self.rsi_overbought = 60  # Sell earlier to lock in gains
        self.momentum_threshold = 0.01  # Very low threshold - trade more often
        self.consensus_threshold = 0.25  # Lower consensus - more trades
        
        # Dynamic symbol selection via screener
        self.screener = MomentumScreener()
        self.min_momentum_score = 30.0  # Lower threshold for scalping - trade more
        self.screener_refresh_interval = 180  # Refresh screener every 3 minutes for faster opportunity detection
        self.last_screener_refresh = None
        self.current_opportunities: List[ScreenerResult] = []
        
        # Fallback symbols if screener fails
        self.fallback_crypto = ["BTC/USD", "ETH/USD", "SOL/USD"]
        
        # Blacklist stablecoins - they won't ever hit take profit targets
        self.stablecoin_blacklist = [
            "USDG/USD", "USDC/USD", "USDT/USD", "DAI/USD", "BUSD/USD",
            "TUSD/USD", "USDP/USD", "GUSD/USD", "FRAX/USD", "LUSD/USD",
            "PYUSD/USD", "EURC/USD", "USDD/USD"
        ]
        
        # State
        self.positions: Dict[str, Position] = {}
        self.running = False
        self.check_interval = 5  # 5 seconds - near real-time monitoring (~127 API calls/min with 3-min screener, 64% of limit)
        
        # Cooldown tracking - different cooldowns for wins vs losses
        self.sell_cooldowns: Dict[str, datetime] = {}  # symbol -> cooldown_until
        self.cooldown_after_tp = 30  # 30 seconds after take profit (price settled, can re-enter)
        self.cooldown_after_sl = 300  # 5 minutes after stop loss (don't chase falling knife)
        
        # Advanced indicators
        self.signal_generator = AdvancedSignalGenerator()
        
        # Ensure data directory exists
        BOT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
        
        logger.info("="*60)
        logger.info("MILLION DOLLAR TRADER INITIALIZED (AGGRESSIVE)")
        logger.info(f"Starting Capital: ${starting_capital:,.2f}")
        logger.info(f"Goal: $1,000,000")
        logger.info(f"Current Balance: ${self.challenge.state.current_balance:,.2f}")
        logger.info(f"Position Size: {self.position_size_pct*100:.0f}%")
        logger.info(f"Stop Loss: {self.stop_loss_pct*100:.0f}% | Take Profit: {self.take_profit_pct*100:.0f}%")
        logger.info(f"Using Dynamic Screener (refreshes every {self.screener_refresh_interval//60} min)")
        logger.info("="*60)
    
    def refresh_opportunities(self) -> List[ScreenerResult]:
        """Refresh the list of trading opportunities from screener."""
        now = datetime.now()
        
        # Check if we need to refresh
        if (self.last_screener_refresh and 
            (now - self.last_screener_refresh).total_seconds() < self.screener_refresh_interval):
            return self.current_opportunities
        
        try:
            logger.info("Refreshing momentum screener...")
            opportunities = self.screener.get_top_opportunities(
                top_n=10,
                include_stocks=True,
                min_momentum_score=self.min_momentum_score
            )
            
            if opportunities:
                self.current_opportunities = opportunities
                self.last_screener_refresh = now
                
                logger.info(f"Found {len(opportunities)} opportunities:")
                for opp in opportunities[:5]:
                    logger.info(f"  #{opp.rank} {opp.symbol}: Score={opp.momentum_score:.1f}, "
                               f"24h={opp.change_24h_pct:+.2f}%, RSI={opp.rsi:.1f}, Trend={opp.trend_direction}")
                
                # Save screener results for dashboard
                self._save_screener_results(opportunities)
            else:
                logger.warning("No opportunities found, using fallback symbols")
                
        except Exception as e:
            logger.error(f"Screener error: {e}, using fallback symbols")
        
        return self.current_opportunities
    
    def _save_screener_results(self, opportunities: List[ScreenerResult]):
        """Save screener results to file for dashboard display."""
        screener_file = BOT_STATE_FILE.parent / "screener_results.json"
        try:
            results = []
            for opp in opportunities:
                results.append({
                    "rank": opp.rank,
                    "symbol": opp.symbol,
                    "asset_type": opp.asset_type,
                    "price": opp.current_price,
                    "change_24h_pct": opp.change_24h_pct,
                    "rsi": opp.rsi,
                    "momentum_score": opp.momentum_score,
                    "trend": opp.trend_direction,
                    "volatility": opp.volatility
                })
            
            with open(screener_file, 'w') as f:
                json.dump({
                    "last_update": datetime.now().isoformat(),
                    "opportunities": results
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving screener results: {e}")
    
    def get_tradeable_symbols(self) -> List[str]:
        """Get list of symbols to consider for trading."""
        opportunities = self.refresh_opportunities()
        
        if opportunities:
            # Return symbols from top opportunities, excluding ones we already hold
            symbols = [opp.symbol for opp in opportunities if opp.symbol not in self.positions]
            return symbols[:6]  # Top 6 not already held
        
        # Fallback to static list
        return [s for s in self.fallback_crypto if s not in self.positions]
    
    def _load_state(self):
        """Load bot state from file."""
        if BOT_STATE_FILE.exists():
            try:
                with open(BOT_STATE_FILE, 'r') as f:
                    data = json.load(f)
                    for symbol, pos_data in data.get("positions", {}).items():
                        # Handle legacy positions without high_water_mark
                        if 'high_water_mark' not in pos_data:
                            pos_data['high_water_mark'] = pos_data.get('entry_price', 0.0)
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
                    "last_update": datetime.now().isoformat(),
                    "challenge": "million_dollar"
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
        """Determine if we should buy using aggressive criteria."""
        # Skip stablecoins - they won't hit profit targets
        if symbol in self.stablecoin_blacklist:
            return False, "Stablecoin blacklisted", 0
        
        bars = self.get_crypto_bars(symbol)
        if bars.empty or len(bars) < 20:
            return False, "Insufficient data", 0
        
        price = self.get_crypto_price(symbol)
        if price is None:
            return False, "No price", 0
        
        # FALLING KNIFE CHECK: Don't buy if price dropped >0.5% in last few bars
        recent_prices = bars['close'].tail(5)
        if len(recent_prices) >= 5:
            price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            if price_change < -0.005:  # Price dropped more than 0.5%
                return False, f"Falling knife - price down {price_change:.1%} recently", 0
        
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
            
            # AGGRESSIVE: Lower consensus threshold (30% vs 35%)
            if consensus.signal_type in ["BUY", "STRONG_BUY"] and consensus.strength >= self.consensus_threshold:
                return True, f"Advanced indicators: {consensus.reason}", consensus.strength
            
            # Single indicator threshold - require 85% confidence for quality signals
            for name, sig in all_signals.items():
                if sig.signal_type in ["BUY", "STRONG_BUY"] and sig.strength >= 0.85:
                    return True, f"Strong {name} signal: {sig.reason}", sig.strength
        except Exception as e:
            logger.warning(f"Advanced indicators failed: {e}, falling back to basic")
        
        # AGGRESSIVE: Higher RSI threshold for oversold (35 vs 30)
        if rsi < self.rsi_oversold and prev_momentum < 0 and momentum > 0:
            strength = min(1.0, (self.rsi_oversold - rsi) / 20 + 0.3)
            return True, f"Bullish reversal! RSI={rsi:.1f}, momentum turning positive", strength
        
        # AGGRESSIVE: Buy on moderate oversold too
        if rsi < 25:
            strength = min(1.0, (25 - rsi) / 10)
            return True, f"Oversold RSI={rsi:.1f}", strength
        
        # AGGRESSIVE: Buy on strong positive momentum
        if momentum > 0.05 and rsi < 60:
            return True, f"Strong momentum={momentum:.1%}, RSI={rsi:.1f}", 0.6
        
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
        
        # Check for reversal signals using advanced indicators
        try:
            bars = self.get_crypto_bars(symbol)
            if not bars.empty:
                consensus = self.signal_generator.get_consensus(bars)
                if consensus.signal_type in ["SELL", "STRONG_SELL"] and consensus.strength >= 0.6:
                    return True, f"Sell signal: {consensus.reason}"
        except Exception:
            pass
        
        return False, "Hold"
    
    def get_invested_amount(self) -> float:
        """Calculate total amount currently invested in positions."""
        total = 0.0
        for symbol, pos in self.positions.items():
            total += pos.entry_price * pos.qty
        return total
    
    def get_available_cash(self) -> float:
        """Calculate available cash for new positions."""
        total_balance = self.challenge.state.current_balance
        invested = self.get_invested_amount()
        return max(0, total_balance - invested)
    
    def execute_buy(self, symbol: str, reason: str, strength: float) -> bool:
        """Execute a buy order."""
        if symbol in self.positions:
            logger.info(f"Already have position in {symbol}")
            return False
        
        if len(self.positions) >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached")
            return False
        
        price = self.get_crypto_price(symbol)
        if price is None:
            return False
        
        # Calculate available cash (can't invest more than we have)
        available_cash = self.get_available_cash()
        
        if available_cash < 10:  # Minimum $10 to trade
            logger.info(f"Insufficient cash: ${available_cash:.2f} available")
            return False
        
        # Calculate position size based on total balance, but cap at available cash
        balance = self.challenge.state.current_balance
        position_value = min(balance * self.position_size_pct, available_cash)
        qty = position_value / price
        
        # Round appropriately
        if price > 1000:  # BTC, ETH
            qty = round(qty, 6)
        else:
            qty = round(qty, 4)
        
        if qty <= 0:
            logger.warning(f"Position size too small for {symbol}")
            return False
        
        try:
            # Submit market order
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            
            # Wait briefly for fill and get actual fill price from Alpaca position
            import time
            time.sleep(0.5)  # Brief wait for order to fill
            
            # Get actual entry price from Alpaca position (not quote price)
            actual_price = price  # Default to quote price
            try:
                alpaca_symbol = symbol.replace('/', '')
                position = self.api.get_position(alpaca_symbol)
                actual_price = float(position.avg_entry_price)
                qty = float(position.qty)  # Use actual filled qty too
            except Exception as e:
                logger.warning(f"Could not get fill price, using quote: {e}")
            
            # Calculate stop loss and take profit from ACTUAL fill price
            stop_loss = actual_price * (1 - self.stop_loss_pct)
            take_profit = actual_price * (1 + self.take_profit_pct)
            
            # Track position with actual fill price
            self.positions[symbol] = Position(
                symbol=symbol,
                side="long",
                qty=qty,
                entry_price=actual_price,
                entry_time=datetime.now().isoformat(),
                stop_loss=stop_loss,
                take_profit=take_profit,
                order_id=order.id,
                asset_type="crypto"
            )
            
            self._save_state()
            
            logger.info(f"🟢 BUY {symbol}: {qty} @ ${actual_price:,.2f}")
            logger.info(f"   Reason: {reason} (strength: {strength:.0%})")
            logger.info(f"   Stop Loss: ${stop_loss:,.2f} | Take Profit: ${take_profit:,.2f}")
            
            return True
            
        except APIError as e:
            logger.error(f"Order failed for {symbol}: {e}")
            return False
    
    def execute_sell(self, symbol: str, reason: str) -> bool:
        """Execute a sell order."""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        price = self.get_crypto_price(symbol)
        if price is None:
            return False
        
        try:
            # Get actual quantity from Alpaca (may differ slightly from tracked qty)
            alpaca_symbol = symbol.replace('/', '')
            actual_qty = position.qty
            try:
                alpaca_positions = self.api.list_positions()
                for ap in alpaca_positions:
                    if ap.symbol == alpaca_symbol:
                        actual_qty = float(ap.qty)
                        price = float(ap.current_price)  # Use Alpaca's price too
                        break
            except:
                pass
            
            # Submit market sell order with actual Alpaca quantity
            order = self.api.submit_order(
                symbol=symbol,
                qty=actual_qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            # Calculate P&L
            pnl = (price - position.entry_price) * position.qty
            pnl_pct = ((price - position.entry_price) / position.entry_price) * 100
            
            # Record trade in challenge
            self.challenge.state.total_trades += 1
            self.challenge.state.total_pnl += pnl
            self.challenge.state.current_balance += pnl
            
            if pnl > 0:
                self.challenge.state.winning_trades += 1
            else:
                self.challenge.state.losing_trades += 1
                # Track daily losses
                self.daily_loss += abs(pnl)
            
            # Add to trade history
            trade_record = {
                "symbol": symbol,
                "side": "sell",
                "qty": position.qty,
                "entry_price": position.entry_price,
                "exit_price": price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            self.challenge.state.trades.append(trade_record)
            # Keep only last 50 trades
            if len(self.challenge.state.trades) > 50:
                self.challenge.state.trades = self.challenge.state.trades[-50:]
            
            # Update peak/lowest
            self.challenge.state.peak_balance = max(
                self.challenge.state.peak_balance, 
                self.challenge.state.current_balance
            )
            self.challenge.state.lowest_balance = min(
                self.challenge.state.lowest_balance,
                self.challenge.state.current_balance
            )
            
            self.challenge._save_state()
            
            # Remove position
            del self.positions[symbol]
            self._save_state()
            
            # Add cooldown - longer after stop loss to avoid chasing falling knives
            is_stop_loss = "Stop loss" in reason or "stop loss" in reason.lower()
            cooldown_secs = self.cooldown_after_sl if is_stop_loss else self.cooldown_after_tp
            self.sell_cooldowns[symbol] = datetime.now() + timedelta(seconds=cooldown_secs)
            cooldown_label = "5min (stop loss)" if is_stop_loss else "30s (take profit)"
            logger.info(f"   Cooldown: {symbol} blocked for {cooldown_label}")
            
            emoji = "🟢" if pnl > 0 else "🔴"
            logger.info(f"{emoji} SELL {symbol}: {position.qty} @ ${price:,.2f}")
            logger.info(f"   P&L: ${pnl:+,.2f} ({pnl_pct:+.1f}%)")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   New Balance: ${self.challenge.state.current_balance:,.2f}")
            
            return True
            
        except APIError as e:
            logger.error(f"Sell order failed for {symbol}: {e}")
            return False
    
    def check_positions(self):
        """Check all open positions for exit signals using Alpaca's live position prices."""
        # Get live positions from Alpaca for accurate current prices
        try:
            alpaca_positions = self.api.list_positions()
            # Create lookup by symbol without slash (AAVEUSD format)
            alpaca_price_map = {}
            for ap in alpaca_positions:
                alpaca_price_map[ap.symbol] = float(ap.current_price)
        except Exception as e:
            logger.warning(f"Could not fetch Alpaca positions: {e}")
            alpaca_price_map = {}
        
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            
            # Convert symbol format: AAVE/USD -> AAVEUSD
            alpaca_symbol = symbol.replace('/', '')
            
            # Get current price from Alpaca positions (more accurate than quote API)
            current_price = alpaca_price_map.get(alpaca_symbol)
            
            if current_price:
                # Check stop loss first (always honored)
                if current_price <= position.stop_loss:
                    logger.info(f"🔴 {symbol}: Price ${current_price:.2f} <= SL ${position.stop_loss:.2f}")
                    self.execute_sell(symbol, f"Stop loss hit (${position.stop_loss:.2f})")
                    continue
                
                # Check take profit (immediate exit at target)
                if current_price >= position.take_profit:
                    logger.info(f"🟢 {symbol}: Price ${current_price:.2f} >= TP ${position.take_profit:.2f}")
                    self.execute_sell(symbol, f"Take profit hit (${position.take_profit:.2f})")
                    continue
                
                # Update high water mark for trailing stop
                if current_price > position.high_water_mark:
                    position.high_water_mark = current_price
                    self._save_state()  # Persist the new high
                
                # Check trailing stop (only if activated - price went +1% above entry)
                activation_price = position.entry_price * (1 + self.trailing_stop_activation_pct)
                if position.high_water_mark >= activation_price:
                    # Trailing stop is active - calculate trailing stop price
                    trailing_stop_price = position.high_water_mark * (1 - self.trailing_stop_distance_pct)
                    
                    # Only trigger if trailing stop is better than original stop loss
                    if trailing_stop_price > position.stop_loss and current_price <= trailing_stop_price:
                        gain_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                        logger.info(f"📈 {symbol}: TRAILING STOP triggered at ${current_price:.2f}")
                        logger.info(f"   High: ${position.high_water_mark:.2f} | Trail: ${trailing_stop_price:.2f}")
                        self.execute_sell(symbol, f"Trailing stop hit (+{gain_pct:.1f}% locked in)")
                        continue
            else:
                # Fallback to original method if position not found in Alpaca
                should_exit, reason = self.should_sell(symbol, position)
                if should_exit:
                    self.execute_sell(symbol, reason)
    
    def scan_for_entries(self):
        """Scan for new entry opportunities using dynamic screener."""
        if len(self.positions) >= self.max_positions:
            return
        
        # Get tradeable symbols from screener
        symbols = self.get_tradeable_symbols()
        
        if not symbols:
            logger.info("No tradeable symbols found")
            return
        
        logger.info(f"Scanning {len(symbols)} symbols: {', '.join(symbols[:5])}...")
        
        for symbol in symbols:
            if symbol in self.positions:
                continue
            
            # Check cooldown - skip if recently sold
            if symbol in self.sell_cooldowns:
                if datetime.now() < self.sell_cooldowns[symbol]:
                    continue  # Still in cooldown
                else:
                    del self.sell_cooldowns[symbol]  # Cooldown expired
            
            # Check if this is a crypto or stock
            is_crypto = "/" in symbol
            
            if is_crypto:
                should_enter, reason, strength = self.should_buy(symbol)
            else:
                # For stocks, check if market is open
                try:
                    clock = self.api.get_clock()
                    if not clock.is_open:
                        continue
                    should_enter, reason, strength = self.should_buy_stock(symbol)
                except:
                    continue
            
            if should_enter:
                self.execute_buy(symbol, reason, strength)
                
                # Only enter one position per cycle
                if len(self.positions) >= self.max_positions:
                    break
    
    def should_buy_stock(self, symbol: str) -> tuple[bool, str, float]:
        """Determine if we should buy a stock."""
        try:
            bars = self.api.get_bars(
                symbol,
                tradeapi.TimeFrame.Hour,
                start=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                end=datetime.now().strftime("%Y-%m-%d")
            ).df
            
            if bars.empty or len(bars) < 20:
                return False, "Insufficient data", 0
            
            # Get current price
            quote = self.api.get_latest_trade(symbol)
            price = float(quote.price)
            
            # Calculate indicators
            rsi = self.calculate_rsi(bars['close'])
            momentum = self.calculate_momentum(bars['close'])
            
            # Use screener data if available
            for opp in self.current_opportunities:
                if opp.symbol == symbol:
                    if opp.momentum_score >= 50 and opp.trend_direction == "up":
                        return True, f"Screener: Score={opp.momentum_score:.0f}, Trend={opp.trend_direction}", opp.momentum_score / 100
            
            # Fallback to basic signals
            if rsi < self.rsi_oversold and momentum > 0:
                return True, f"Oversold bounce RSI={rsi:.1f}", 0.6
            
            return False, f"No signal (RSI={rsi:.1f})", 0
            
        except Exception as e:
            logger.debug(f"Error checking stock {symbol}: {e}")
            return False, str(e), 0
    
    def run(self):
        """Main trading loop."""
        self.running = True
        logger.info("Starting Million Dollar Trader...")
        logger.info(f"Using Dynamic Screener for symbol selection")
        logger.info(f"Check Interval: {self.check_interval} seconds")
        
        while self.running:
            try:
                # Reset daily loss counter at start of new day
                today = datetime.now().date()
                if self.last_trading_day != today:
                    self.daily_loss = 0.0
                    self.last_trading_day = today
                    logger.info(f"📅 New trading day - daily loss reset")
                
                # Check daily loss limit
                max_daily_loss = self.challenge.state.current_balance * self.max_daily_loss_pct
                if self.daily_loss >= max_daily_loss:
                    logger.warning(f"⛔ DAILY LOSS LIMIT HIT: ${self.daily_loss:.2f} >= ${max_daily_loss:.2f} ({self.max_daily_loss_pct*100:.0f}%)")
                    logger.info("Pausing new entries until tomorrow. Still monitoring existing positions.")
                    # Still check positions but don't enter new ones
                    self.check_positions()
                    time.sleep(60)  # Check less frequently when paused
                    continue
                
                logger.info("-" * 40)
                logger.info(f"Trading Cycle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                invested = self.get_invested_amount()
                available = self.get_available_cash()
                logger.info(f"Balance: ${self.challenge.state.current_balance:,.2f} | Invested: ${invested:,.2f} | Cash: ${available:,.2f}")
                
                # Check existing positions
                self.check_positions()
                
                # Scan for new entries
                self.scan_for_entries()
                
                # Log status
                logger.info(f"Open Positions: {len(self.positions)}")
                for symbol, pos in self.positions.items():
                    price = self.get_crypto_price(symbol)
                    if price:
                        pnl = (price - pos.entry_price) * pos.qty
                        logger.info(f"  {symbol}: {pos.qty} @ ${pos.entry_price:,.2f} | Current: ${price:,.2f} | P&L: ${pnl:+,.2f}")
                
                # Check if goal reached (unlikely but hey!)
                if self.challenge.state.current_balance >= self.challenge.state.goal:
                    logger.info("🎉🎉🎉 MILLION DOLLAR GOAL REACHED! 🎉🎉🎉")
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
                time.sleep(60)
        
        logger.info("Million Dollar Trader stopped.")
        self.challenge.print_status()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            "running": self.running,
            "challenge": self.challenge.get_status(),
            "positions": {s: asdict(p) for s, p in self.positions.items()},
            "symbols_monitored": self.crypto_symbols,
            "check_interval": self.check_interval,
            "config": {
                "position_size_pct": self.position_size_pct,
                "stop_loss_pct": self.stop_loss_pct,
                "take_profit_pct": self.take_profit_pct,
                "max_positions": self.max_positions
            }
        }


def main():
    """Entry point for Million Dollar Trader."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start with $1000, goal $1,000,000
    trader = MillionDollarTrader(starting_capital=1000.0)
    trader.run()


if __name__ == "__main__":
    main()
