"""Short Selling Strategy for Bearish Markets.

Implements strategies for profiting from declining stocks:
1. Direct short selling (borrow and sell, buy back lower)
2. Inverse ETF buying (SQQQ, SPXS, SDOW)

Works with the small account challenge constraints.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame

from alpaca_trading.core.config import config

logger = logging.getLogger(__name__)


@dataclass
class ShortSignal:
    """Signal for short selling opportunity."""
    symbol: str
    action: str  # "SHORT", "COVER", "BUY_INVERSE", "SELL_INVERSE", "HOLD"
    strength: float
    reason: str
    price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    
    def __str__(self):
        return f"{self.action} {self.symbol} @ ${self.price:.2f} ({self.reason})"


# Inverse ETFs - go UP when market goes DOWN
INVERSE_ETFS = {
    "SQQQ": {"tracks": "QQQ", "leverage": 3, "description": "3x Inverse Nasdaq-100"},
    "SPXS": {"tracks": "SPY", "leverage": 3, "description": "3x Inverse S&P 500"},
    "SDOW": {"tracks": "DIA", "leverage": 3, "description": "3x Inverse Dow Jones"},
    "SH": {"tracks": "SPY", "leverage": 1, "description": "1x Inverse S&P 500"},
    "PSQ": {"tracks": "QQQ", "leverage": 1, "description": "1x Inverse Nasdaq-100"},
    "SOXS": {"tracks": "SOXX", "leverage": 3, "description": "3x Inverse Semiconductors"},
}

# Good stocks to short in a downturn (high beta, volatile)
SHORTABLE_STOCKS = [
    "TSLA", "NVDA", "AMD", "COIN", "MARA", "RIOT", 
    "PLTR", "RIVN", "LCID", "NIO", "SNAP", "HOOD"
]


class ShortStrategy:
    """Strategy for short selling and inverse ETF trading."""
    
    def __init__(self):
        self.api = tradeapi.REST(
            config.api_key,
            config.api_secret,
            config.base_url,
            api_version='v2'
        )
        
        # Strategy parameters
        self.rsi_period = 14
        self.rsi_overbought = 70  # Short when RSI > 70
        self.momentum_period = 10
        self.momentum_threshold = -0.02  # Short when momentum < -2%
        
        # Risk management
        self.stop_loss_pct = 0.03  # 3% stop loss
        self.take_profit_pct = 0.06  # 6% take profit
        
        logger.info("ShortStrategy initialized")
    
    def get_bars(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical bars for a symbol."""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            bars = self.api.get_bars(
                symbol,
                TimeFrame.Hour,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                adjustment='all'
            ).df
            
            if not bars.empty:
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
    
    def calculate_momentum(self, prices: pd.Series, period: int = 10) -> float:
        """Calculate momentum as percentage change."""
        if len(prices) < period + 1:
            return 0.0
        
        current = prices.iloc[-1]
        past = prices.iloc[-period - 1]
        
        return (current - past) / past if past > 0 else 0.0
    
    def is_shortable(self, symbol: str) -> bool:
        """Check if a stock can be shorted."""
        try:
            asset = self.api.get_asset(symbol)
            return asset.shortable and asset.easy_to_borrow
        except Exception as e:
            logger.error(f"Error checking shortability for {symbol}: {e}")
            return False
    
    def analyze_for_short(self, symbol: str) -> Optional[ShortSignal]:
        """Analyze a stock for short selling opportunity."""
        bars = self.get_bars(symbol)
        if bars.empty:
            return None
        
        try:
            current_price = float(bars['close'].iloc[-1])
        except:
            return None
        
        rsi = self.calculate_rsi(bars['close'])
        momentum = self.calculate_momentum(bars['close'])
        
        # Check for short signal
        # Ideal: RSI overbought (>70) AND negative momentum
        short_score = 0
        reasons = []
        
        if rsi > self.rsi_overbought:
            short_score += 0.4
            reasons.append(f"RSI overbought at {rsi:.1f}")
        elif rsi > 60:
            short_score += 0.2
            reasons.append(f"RSI elevated at {rsi:.1f}")
        
        if momentum < self.momentum_threshold:
            short_score += 0.4
            reasons.append(f"Negative momentum ({momentum:.1%})")
        elif momentum < 0:
            short_score += 0.2
            reasons.append(f"Weak momentum ({momentum:.1%})")
        
        # Check if shortable
        if not self.is_shortable(symbol):
            return ShortSignal(
                symbol=symbol,
                action="HOLD",
                strength=0,
                reason="Not shortable",
                price=current_price,
                stop_loss=0,
                take_profit=0,
                timestamp=datetime.now()
            )
        
        if short_score >= 0.5:
            return ShortSignal(
                symbol=symbol,
                action="SHORT",
                strength=min(1.0, short_score),
                reason=" + ".join(reasons),
                price=current_price,
                stop_loss=current_price * (1 + self.stop_loss_pct),
                take_profit=current_price * (1 - self.take_profit_pct),
                timestamp=datetime.now()
            )
        
        return ShortSignal(
            symbol=symbol,
            action="HOLD",
            strength=short_score,
            reason=f"RSI: {rsi:.1f}, Momentum: {momentum:.1%}",
            price=current_price,
            stop_loss=0,
            take_profit=0,
            timestamp=datetime.now()
        )
    
    def analyze_inverse_etf(self, etf_symbol: str) -> Optional[ShortSignal]:
        """Analyze an inverse ETF for buying opportunity.
        
        For inverse ETFs, we want to BUY when the underlying is FALLING.
        """
        if etf_symbol not in INVERSE_ETFS:
            return None
        
        info = INVERSE_ETFS[etf_symbol]
        underlying = info["tracks"]
        
        # Analyze the underlying (e.g., SPY for SPXS)
        bars = self.get_bars(underlying)
        if bars.empty:
            return None
        
        try:
            underlying_price = float(bars['close'].iloc[-1])
        except:
            return None
        
        # Get inverse ETF price
        etf_bars = self.get_bars(etf_symbol)
        if etf_bars.empty:
            return None
        
        try:
            etf_price = float(etf_bars['close'].iloc[-1])
        except:
            return None
        
        rsi = self.calculate_rsi(bars['close'])
        momentum = self.calculate_momentum(bars['close'])
        
        # For inverse ETFs, we want to BUY when underlying is WEAK
        # (opposite of normal logic)
        buy_score = 0
        reasons = []
        
        if rsi > self.rsi_overbought:
            buy_score += 0.3
            reasons.append(f"{underlying} RSI overbought ({rsi:.1f})")
        
        if momentum < self.momentum_threshold:
            buy_score += 0.4
            reasons.append(f"{underlying} falling ({momentum:.1%})")
        elif momentum < 0:
            buy_score += 0.2
            reasons.append(f"{underlying} weak ({momentum:.1%})")
        
        # Leverage bonus - 3x ETFs move faster
        if info["leverage"] == 3:
            buy_score += 0.1
            reasons.append(f"{info['leverage']}x leverage")
        
        if buy_score >= 0.5:
            return ShortSignal(
                symbol=etf_symbol,
                action="BUY_INVERSE",
                strength=min(1.0, buy_score),
                reason=" + ".join(reasons),
                price=etf_price,
                stop_loss=etf_price * (1 - self.stop_loss_pct),
                take_profit=etf_price * (1 + self.take_profit_pct),
                timestamp=datetime.now()
            )
        
        return ShortSignal(
            symbol=etf_symbol,
            action="HOLD",
            strength=buy_score,
            reason=f"{underlying}: RSI {rsi:.1f}, Mom {momentum:.1%}",
            price=etf_price,
            stop_loss=0,
            take_profit=0,
            timestamp=datetime.now()
        )
    
    def scan_all(self) -> Dict[str, List[ShortSignal]]:
        """Scan all shortable stocks and inverse ETFs."""
        results = {
            "short_candidates": [],
            "inverse_etf_candidates": [],
        }
        
        logger.info("Scanning for short opportunities...")
        
        # Scan shortable stocks
        for symbol in SHORTABLE_STOCKS:
            signal = self.analyze_for_short(symbol)
            if signal and signal.action == "SHORT":
                results["short_candidates"].append(signal)
                logger.info(f"Short signal: {signal}")
        
        # Scan inverse ETFs
        for etf in INVERSE_ETFS.keys():
            signal = self.analyze_inverse_etf(etf)
            if signal and signal.action == "BUY_INVERSE":
                results["inverse_etf_candidates"].append(signal)
                logger.info(f"Inverse ETF signal: {signal}")
        
        # Sort by strength
        results["short_candidates"].sort(key=lambda x: x.strength, reverse=True)
        results["inverse_etf_candidates"].sort(key=lambda x: x.strength, reverse=True)
        
        return results
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """Get overall market sentiment based on major indices."""
        sentiment = {
            "spy_momentum": 0,
            "qqq_momentum": 0,
            "overall": "NEUTRAL",
            "recommendation": ""
        }
        
        for symbol in ["SPY", "QQQ"]:
            bars = self.get_bars(symbol)
            if not bars.empty:
                momentum = self.calculate_momentum(bars['close'])
                if symbol == "SPY":
                    sentiment["spy_momentum"] = momentum
                else:
                    sentiment["qqq_momentum"] = momentum
        
        avg_momentum = (sentiment["spy_momentum"] + sentiment["qqq_momentum"]) / 2
        
        if avg_momentum < -0.02:
            sentiment["overall"] = "BEARISH"
            sentiment["recommendation"] = "Consider shorts or inverse ETFs"
        elif avg_momentum > 0.02:
            sentiment["overall"] = "BULLISH"
            sentiment["recommendation"] = "Avoid shorts, go long"
        else:
            sentiment["overall"] = "NEUTRAL"
            sentiment["recommendation"] = "Wait for clearer direction"
        
        return sentiment


def main():
    """Test the short strategy."""
    logging.basicConfig(level=logging.INFO)
    
    strategy = ShortStrategy()
    
    print("\n" + "="*60)
    print("📉 SHORT SELLING STRATEGY ANALYSIS")
    print("="*60)
    
    # Market sentiment
    sentiment = strategy.get_market_sentiment()
    print(f"\n🌡️ MARKET SENTIMENT: {sentiment['overall']}")
    print(f"   SPY Momentum: {sentiment['spy_momentum']:.1%}")
    print(f"   QQQ Momentum: {sentiment['qqq_momentum']:.1%}")
    print(f"   Recommendation: {sentiment['recommendation']}")
    
    # Scan for opportunities
    results = strategy.scan_all()
    
    print(f"\n📊 SHORT CANDIDATES ({len(results['short_candidates'])}):")
    for sig in results["short_candidates"][:5]:
        print(f"   {sig.symbol:6} @ ${sig.price:>8.2f} | Strength: {sig.strength:.0%} | {sig.reason}")
        print(f"          Stop: ${sig.stop_loss:.2f} | Target: ${sig.take_profit:.2f}")
    
    print(f"\n📈 INVERSE ETF CANDIDATES ({len(results['inverse_etf_candidates'])}):")
    for sig in results["inverse_etf_candidates"]:
        print(f"   {sig.symbol:6} @ ${sig.price:>8.2f} | Strength: {sig.strength:.0%} | {sig.reason}")
        print(f"          Stop: ${sig.stop_loss:.2f} | Target: ${sig.take_profit:.2f}")
    
    print("="*60)


if __name__ == "__main__":
    main()
