"""Crypto Momentum Reversal Alerts.

Monitors crypto for momentum reversals - when a falling coin starts to bounce.
This is the ideal entry point: RSI oversold + momentum turning positive.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi

from alpaca_trading.core.config import config
from alpaca_trading.crypto.crypto_config import crypto_config

logger = logging.getLogger(__name__)

# Alerts data file
ALERTS_FILE = Path(__file__).parent.parent.parent / "data" / "crypto_alerts.json"


@dataclass
class CryptoAlert:
    """Alert for crypto momentum reversal."""
    symbol: str
    alert_type: str  # "REVERSAL_UP", "REVERSAL_DOWN", "OVERSOLD", "OVERBOUGHT"
    price: float
    rsi: float
    momentum: float
    prev_momentum: float
    strength: float
    message: str
    timestamp: str
    triggered: bool = False
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "alert_type": self.alert_type,
            "price": self.price,
            "rsi": self.rsi,
            "momentum": self.momentum,
            "prev_momentum": self.prev_momentum,
            "strength": self.strength,
            "message": self.message,
            "timestamp": self.timestamp,
            "triggered": self.triggered
        }


class CryptoAlertMonitor:
    """Monitors crypto for momentum reversals and generates alerts."""
    
    def __init__(self):
        self.api = tradeapi.REST(
            config.api_key,
            config.api_secret,
            config.base_url,
            api_version='v2'
        )
        
        self.symbols = crypto_config.symbols
        
        # Alert thresholds
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.momentum_threshold = 0.01  # 1% momentum change
        
        # Previous state for detecting reversals
        self.previous_state: Dict[str, Dict] = {}
        
        # Active alerts
        self.alerts: List[CryptoAlert] = []
        
        # Ensure data directory exists
        ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
        
        logger.info("CryptoAlertMonitor initialized")
    
    def _load_state(self):
        """Load previous state from file."""
        if ALERTS_FILE.exists():
            try:
                with open(ALERTS_FILE, 'r') as f:
                    data = json.load(f)
                    self.previous_state = data.get("previous_state", {})
                    self.alerts = [CryptoAlert(**a) for a in data.get("alerts", [])]
            except Exception as e:
                logger.error(f"Error loading state: {e}")
    
    def _save_state(self):
        """Save state to file."""
        try:
            with open(ALERTS_FILE, 'w') as f:
                json.dump({
                    "previous_state": self.previous_state,
                    "alerts": [a.to_dict() for a in self.alerts[-50:]]  # Keep last 50
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
        """Calculate short-term momentum (6 hours for crypto)."""
        if len(prices) < period + 1:
            return 0.0
        
        current = prices.iloc[-1]
        past = prices.iloc[-period - 1]
        
        return (current - past) / past if past > 0 else 0.0
    
    def check_symbol(self, symbol: str) -> Optional[CryptoAlert]:
        """Check a symbol for alert conditions."""
        price = self.get_crypto_price(symbol)
        if price is None:
            return None
        
        bars = self.get_crypto_bars(symbol)
        if bars.empty or len(bars) < 20:
            return None
        
        rsi = self.calculate_rsi(bars['close'])
        momentum = self.calculate_momentum(bars['close'])
        
        # Get previous state
        prev = self.previous_state.get(symbol, {})
        prev_momentum = prev.get("momentum", 0)
        prev_rsi = prev.get("rsi", 50)
        
        # Update state
        self.previous_state[symbol] = {
            "momentum": momentum,
            "rsi": rsi,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
        
        alert = None
        
        # Check for BULLISH REVERSAL (the golden signal!)
        # RSI oversold + momentum turning positive
        if rsi < self.rsi_oversold and prev_momentum < 0 and momentum > 0:
            alert = CryptoAlert(
                symbol=symbol,
                alert_type="REVERSAL_UP",
                price=price,
                rsi=rsi,
                momentum=momentum,
                prev_momentum=prev_momentum,
                strength=min(1.0, (self.rsi_oversold - rsi) / 20),
                message=f"🚀 BULLISH REVERSAL! RSI oversold ({rsi:.1f}) + momentum turning positive ({prev_momentum:.1%} → {momentum:.1%})",
                timestamp=datetime.now().isoformat()
            )
            logger.info(f"ALERT: {alert.message}")
        
        # Check for BEARISH REVERSAL
        elif rsi > self.rsi_overbought and prev_momentum > 0 and momentum < 0:
            alert = CryptoAlert(
                symbol=symbol,
                alert_type="REVERSAL_DOWN",
                price=price,
                rsi=rsi,
                momentum=momentum,
                prev_momentum=prev_momentum,
                strength=min(1.0, (rsi - self.rsi_overbought) / 20),
                message=f"⚠️ BEARISH REVERSAL! RSI overbought ({rsi:.1f}) + momentum turning negative",
                timestamp=datetime.now().isoformat()
            )
            logger.info(f"ALERT: {alert.message}")
        
        # Check for EXTREME OVERSOLD (potential bounce coming)
        elif rsi < 20:
            alert = CryptoAlert(
                symbol=symbol,
                alert_type="OVERSOLD",
                price=price,
                rsi=rsi,
                momentum=momentum,
                prev_momentum=prev_momentum,
                strength=min(1.0, (20 - rsi) / 10),
                message=f"📉 EXTREME OVERSOLD! RSI at {rsi:.1f} - watch for reversal",
                timestamp=datetime.now().isoformat()
            )
        
        if alert:
            self.alerts.append(alert)
            self._save_state()
        
        return alert
    
    def scan_all(self) -> List[CryptoAlert]:
        """Scan all crypto symbols for alerts."""
        new_alerts = []
        
        for symbol in self.symbols:
            alert = self.check_symbol(symbol)
            if alert:
                new_alerts.append(alert)
        
        self._save_state()
        return new_alerts
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "symbols_monitored": self.symbols,
            "active_alerts": len([a for a in self.alerts if not a.triggered]),
            "recent_alerts": [a.to_dict() for a in self.alerts[-10:]],
            "current_state": self.previous_state
        }
    
    def get_buy_signals(self) -> List[CryptoAlert]:
        """Get all untriggered bullish reversal alerts."""
        return [a for a in self.alerts 
                if a.alert_type == "REVERSAL_UP" and not a.triggered]
    
    def mark_triggered(self, symbol: str):
        """Mark alerts for a symbol as triggered (after trading)."""
        for alert in self.alerts:
            if alert.symbol == symbol and not alert.triggered:
                alert.triggered = True
        self._save_state()


def main():
    """Run alert monitor."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    monitor = CryptoAlertMonitor()
    
    print("\n" + "="*60)
    print("🔔 CRYPTO MOMENTUM REVERSAL MONITOR")
    print("="*60)
    
    print("\n📊 Current State:")
    for symbol in monitor.symbols:
        state = monitor.previous_state.get(symbol, {})
        if state:
            print(f"  {symbol:12} RSI: {state.get('rsi', 0):.1f}  Mom: {state.get('momentum', 0):.1%}")
    
    print("\n🔍 Scanning for alerts...")
    alerts = monitor.scan_all()
    
    if alerts:
        print(f"\n🚨 NEW ALERTS ({len(alerts)}):")
        for alert in alerts:
            print(f"  {alert.symbol}: {alert.message}")
    else:
        print("\n✅ No new alerts. Monitoring continues...")
    
    # Show any buy signals
    buy_signals = monitor.get_buy_signals()
    if buy_signals:
        print(f"\n🎯 ACTIVE BUY SIGNALS ({len(buy_signals)}):")
        for sig in buy_signals:
            print(f"  {sig.symbol} @ ${sig.price:.2f} - {sig.message}")
    
    print("="*60)


if __name__ == "__main__":
    main()
