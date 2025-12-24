"""Small Account Challenge - $100-500 to $1000 Growth Tracker.

A realistic trading scenario that simulates growing a small account
using conservative position sizing and risk management.

Key constraints:
- Starting capital: $100-500 (configurable)
- Goal: $1,000
- Position sizing: 10-20% of account per trade
- Max positions: 2-3 (diversification with small capital)
- Stop loss: 2-3% (protect capital)
- Take profit: 4-6% (2:1 risk/reward)
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import alpaca_trade_api as tradeapi

from alpaca_trading.core.config import config

logger = logging.getLogger(__name__)

# Challenge data file
CHALLENGE_FILE = Path(__file__).parent.parent.parent / "data" / "small_account_challenge.json"


@dataclass
class TradeRecord:
    """Record of a single trade."""
    symbol: str
    side: str  # "buy" or "sell"
    qty: float
    price: float
    timestamp: str
    pnl: float = 0.0
    pnl_pct: float = 0.0
    strategy: str = ""
    notes: str = ""


@dataclass
class ChallengeConfig:
    """Configuration for the small account challenge."""
    starting_capital: float = 500.0
    goal: float = 1000.0
    
    # Position sizing (percentage of account)
    position_size_pct: float = 0.20  # 20% per position
    max_positions: int = 3
    
    # Risk management
    stop_loss_pct: float = 0.025  # 2.5%
    take_profit_pct: float = 0.05  # 5% (2:1 R:R)
    max_daily_loss_pct: float = 0.05  # 5% max daily drawdown
    
    # Trading rules
    trade_stocks: bool = True
    trade_crypto: bool = True
    crypto_only_weekends: bool = True  # Trade crypto when stock market closed
    
    # Preferred symbols (small account friendly - lower prices, good liquidity)
    stock_symbols: List[str] = field(default_factory=lambda: [
        # Original momentum stocks
        "AMD", "PLTR", "SOFI", "NIO", "F", "RIVN", "LCID", 
        "SNAP", "HOOD", "COIN", "MARA", "RIOT",
        # Mega-cap tech (high liquidity, good swings)
        "NVDA", "TSLA", "META", "GOOGL", "AMZN",
        # High-volatility momentum
        "SMCI", "ARM", "IONQ", "RKLB", "AFRM",
        # Crypto-adjacent (moves with BTC)
        "MSTR", "CLSK", "HUT",
    ])
    # Inverse ETFs for bearish markets (profit when market falls)
    inverse_etfs: List[str] = field(default_factory=lambda: [
        "SQQQ",  # 3x Inverse Nasdaq-100
        "SPXS",  # 3x Inverse S&P 500
        "SDOW",  # 3x Inverse Dow Jones
        "SOXS",  # 3x Inverse Semiconductors
        "TECS",  # 3x Inverse Tech
        "FAZ",   # 3x Inverse Financials
    ])
    crypto_symbols: List[str] = field(default_factory=lambda: [
        "BTC/USD", "ETH/USD", "DOGE/USD", "SOL/USD"
    ])


@dataclass
class ChallengeState:
    """Current state of the challenge."""
    started_at: str = ""
    current_balance: float = 0.0
    starting_balance: float = 0.0
    goal: float = 1000.0
    
    # Progress tracking
    peak_balance: float = 0.0
    lowest_balance: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    
    # Daily tracking
    daily_pnl: float = 0.0
    daily_trades: int = 0
    last_trade_date: str = ""
    
    # Trade history
    trades: List[Dict] = field(default_factory=list)
    daily_snapshots: List[Dict] = field(default_factory=list)
    
    @property
    def progress_pct(self) -> float:
        """Progress toward goal as percentage."""
        if self.goal <= self.starting_balance:
            return 100.0
        gain_needed = self.goal - self.starting_balance
        gain_achieved = self.current_balance - self.starting_balance
        return max(0, min(100, (gain_achieved / gain_needed) * 100))
    
    @property
    def win_rate(self) -> float:
        """Win rate as percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def days_active(self) -> int:
        """Number of days since challenge started."""
        if not self.started_at:
            return 0
        start = datetime.fromisoformat(self.started_at)
        return (datetime.now() - start).days
    
    @property
    def avg_daily_return(self) -> float:
        """Average daily return percentage."""
        if self.days_active == 0 or self.starting_balance == 0:
            return 0.0
        total_return = (self.current_balance - self.starting_balance) / self.starting_balance
        return (total_return / max(1, self.days_active)) * 100
    
    @property
    def projected_days_to_goal(self) -> Optional[int]:
        """Estimated days to reach goal at current pace."""
        if self.avg_daily_return <= 0:
            return None
        remaining_pct = ((self.goal - self.current_balance) / self.current_balance) * 100
        return int(remaining_pct / self.avg_daily_return)


class SmallAccountChallenge:
    """Manages the small account growth challenge."""
    
    def __init__(self, starting_capital: float = 500.0, goal: float = 1000.0):
        self.api = tradeapi.REST(
            config.api_key,
            config.api_secret,
            config.base_url,
            api_version='v2'
        )
        
        self.config = ChallengeConfig(starting_capital=starting_capital, goal=goal)
        self.state = ChallengeState()
        
        # Ensure data directory exists
        CHALLENGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing state or initialize new
        self._load_state()
        
        logger.info(f"Small Account Challenge initialized")
        logger.info(f"Starting: ${self.config.starting_capital} → Goal: ${self.config.goal}")
    
    def _load_state(self):
        """Load challenge state from file."""
        if CHALLENGE_FILE.exists():
            try:
                with open(CHALLENGE_FILE, 'r') as f:
                    data = json.load(f)
                    self.state = ChallengeState(**data)
                    logger.info(f"Loaded existing challenge: ${self.state.current_balance:.2f}")
            except Exception as e:
                logger.error(f"Error loading state: {e}")
                self._initialize_new_challenge()
        else:
            self._initialize_new_challenge()
    
    def _save_state(self):
        """Save challenge state to file."""
        try:
            with open(CHALLENGE_FILE, 'w') as f:
                json.dump(asdict(self.state), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _initialize_new_challenge(self):
        """Initialize a new challenge."""
        self.state = ChallengeState(
            started_at=datetime.now().isoformat(),
            current_balance=self.config.starting_capital,
            starting_balance=self.config.starting_capital,
            goal=self.config.goal,
            peak_balance=self.config.starting_capital,
            lowest_balance=self.config.starting_capital,
        )
        self._save_state()
        logger.info(f"New challenge started with ${self.config.starting_capital}")
    
    def reset_challenge(self, starting_capital: float = None):
        """Reset the challenge with optional new starting capital."""
        if starting_capital:
            self.config.starting_capital = starting_capital
            self.config.goal = starting_capital * 2  # Default: double your money
        self._initialize_new_challenge()
        return self.get_status()
    
    def get_account_balance(self) -> float:
        """Get current simulated balance (NOT the actual Alpaca balance).
        
        The challenge tracks a virtual balance starting from the configured
        starting capital, not the actual paper trading account balance.
        """
        # Return the simulated balance, not the actual Alpaca balance
        return self.state.current_balance
    
    def get_actual_alpaca_balance(self) -> float:
        """Get the actual Alpaca account balance (for reference only)."""
        try:
            account = self.api.get_account()
            return float(account.portfolio_value)
        except Exception as e:
            logger.error(f"Error getting Alpaca balance: {e}")
            return 0.0
    
    def sync_with_alpaca(self):
        """Update challenge state (does NOT sync with actual Alpaca balance).
        
        The challenge uses a simulated balance that only changes when trades
        are recorded, allowing you to simulate starting with $500 even though
        the paper account has $100k.
        """
        balance = self.state.current_balance  # Use simulated balance
        
        # Update peak/lowest tracking
        self.state.peak_balance = max(self.state.peak_balance, balance)
        self.state.lowest_balance = min(self.state.lowest_balance, balance)
        
        # Take daily snapshot
        today = datetime.now().strftime("%Y-%m-%d")
        if not self.state.daily_snapshots or self.state.daily_snapshots[-1].get("date") != today:
            self.state.daily_snapshots.append({
                "date": today,
                "balance": balance,
                "pnl": balance - self.state.starting_balance,
                "trades": self.state.daily_trades
            })
            # Reset daily counters
            self.state.daily_pnl = 0.0
            self.state.daily_trades = 0
        
        self._save_state()
        return balance
    
    def record_trade(self, symbol: str, side: str, qty: float, price: float, 
                     pnl: float = 0.0, strategy: str = "", notes: str = ""):
        """Record a trade in the challenge history and update simulated balance."""
        trade = TradeRecord(
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            timestamp=datetime.now().isoformat(),
            pnl=pnl,
            pnl_pct=(pnl / (qty * price)) * 100 if qty * price > 0 else 0,
            strategy=strategy,
            notes=notes
        )
        
        self.state.trades.append(asdict(trade))
        self.state.total_trades += 1
        self.state.daily_trades += 1
        
        if pnl > 0:
            self.state.winning_trades += 1
        elif pnl < 0:
            self.state.losing_trades += 1
        
        self.state.total_pnl += pnl
        self.state.daily_pnl += pnl
        self.state.last_trade_date = datetime.now().strftime("%Y-%m-%d")
        
        # Update simulated balance with P&L
        self.state.current_balance += pnl
        
        # Sync state (updates peak/lowest, saves)
        self.sync_with_alpaca()
        
        logger.info(f"Trade recorded: {side.upper()} {qty} {symbol} @ ${price:.2f} P&L: ${pnl:.2f}")
        logger.info(f"Simulated balance: ${self.state.current_balance:.2f}")
    
    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on current balance and config."""
        max_position_value = self.state.current_balance * self.config.position_size_pct
        shares = max_position_value / price
        
        # Round down to avoid over-buying
        if price > 10:
            shares = int(shares)
        else:
            shares = round(shares, 2)
        
        return max(0, shares)
    
    def can_trade(self) -> tuple[bool, str]:
        """Check if we can make a trade based on rules."""
        # Check daily loss limit
        if self.state.daily_pnl < -(self.state.current_balance * self.config.max_daily_loss_pct):
            return False, "Daily loss limit reached"
        
        # Check if goal reached
        if self.state.current_balance >= self.state.goal:
            return False, "🎉 Goal reached!"
        
        # Check if account blown
        if self.state.current_balance < self.state.starting_balance * 0.5:
            return False, "Account below 50% - consider resetting"
        
        return True, "Ready to trade"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current challenge status."""
        self.sync_with_alpaca()
        
        can_trade, trade_status = self.can_trade()
        
        return {
            "challenge": {
                "started": self.state.started_at,
                "days_active": self.state.days_active,
                "starting_balance": self.state.starting_balance,
                "current_balance": self.state.current_balance,
                "goal": self.state.goal,
                "progress_pct": self.state.progress_pct,
                "goal_reached": self.state.current_balance >= self.state.goal,
            },
            "performance": {
                "total_pnl": self.state.total_pnl,
                "total_pnl_pct": (self.state.total_pnl / self.state.starting_balance) * 100,
                "peak_balance": self.state.peak_balance,
                "lowest_balance": self.state.lowest_balance,
                "max_drawdown_pct": ((self.state.peak_balance - self.state.lowest_balance) / self.state.peak_balance) * 100 if self.state.peak_balance > 0 else 0,
            },
            "trades": {
                "total": self.state.total_trades,
                "winning": self.state.winning_trades,
                "losing": self.state.losing_trades,
                "win_rate": self.state.win_rate,
            },
            "projections": {
                "avg_daily_return_pct": self.state.avg_daily_return,
                "projected_days_to_goal": self.state.projected_days_to_goal,
            },
            "today": {
                "pnl": self.state.daily_pnl,
                "trades": self.state.daily_trades,
                "can_trade": can_trade,
                "status": trade_status,
            },
            "config": {
                "position_size_pct": self.config.position_size_pct * 100,
                "max_positions": self.config.max_positions,
                "stop_loss_pct": self.config.stop_loss_pct * 100,
                "take_profit_pct": self.config.take_profit_pct * 100,
            }
        }
    
    def get_trade_history(self, limit: int = 20) -> List[Dict]:
        """Get recent trade history."""
        return self.state.trades[-limit:][::-1]  # Most recent first
    
    def get_daily_snapshots(self) -> pd.DataFrame:
        """Get daily balance snapshots as DataFrame."""
        if not self.state.daily_snapshots:
            return pd.DataFrame()
        return pd.DataFrame(self.state.daily_snapshots)
    
    def print_status(self):
        """Print a formatted status report."""
        status = self.get_status()
        
        print("\n" + "="*50)
        print("📈 SMALL ACCOUNT CHALLENGE STATUS")
        print("="*50)
        
        c = status["challenge"]
        print(f"\n💰 Balance: ${c['current_balance']:,.2f}")
        print(f"🎯 Goal: ${c['goal']:,.2f}")
        print(f"📊 Progress: {c['progress_pct']:.1f}%")
        print(f"📅 Days Active: {c['days_active']}")
        
        p = status["performance"]
        print(f"\n📈 Total P&L: ${p['total_pnl']:,.2f} ({p['total_pnl_pct']:.1f}%)")
        print(f"🔝 Peak: ${p['peak_balance']:,.2f}")
        print(f"📉 Max Drawdown: {p['max_drawdown_pct']:.1f}%")
        
        t = status["trades"]
        print(f"\n🔄 Trades: {t['total']} (W: {t['winning']} / L: {t['losing']})")
        print(f"✅ Win Rate: {t['win_rate']:.1f}%")
        
        proj = status["projections"]
        print(f"\n📊 Avg Daily Return: {proj['avg_daily_return_pct']:.2f}%")
        if proj["projected_days_to_goal"]:
            print(f"🗓️ Est. Days to Goal: {proj['projected_days_to_goal']}")
        
        today = status["today"]
        print(f"\n📅 Today: ${today['pnl']:,.2f} P&L, {today['trades']} trades")
        print(f"🚦 Status: {today['status']}")
        
        if c["goal_reached"]:
            print("\n🎉🎉🎉 CONGRATULATIONS! GOAL REACHED! 🎉🎉🎉")
        
        print("="*50 + "\n")


def main():
    """Entry point for challenge status check."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Default: $500 start, $1000 goal
    challenge = SmallAccountChallenge(starting_capital=500.0, goal=1000.0)
    challenge.print_status()


if __name__ == "__main__":
    main()
