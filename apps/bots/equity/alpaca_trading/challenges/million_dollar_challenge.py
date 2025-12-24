"""Million Dollar Challenge - Aggressive Long-Term Growth Tracker.

A long-term trading strategy to grow from $1,000 to $1,000,000
with bi-monthly contributions and aggressive swing trading.

Key parameters:
- Starting capital: $1,000
- Goal: $1,000,000
- Monthly contribution: $500 (bi-monthly: $250 twice/month)
- Strategy: Aggressive swing trading (2-7 day holds)
- Risk per trade: 10% of portfolio
- Take profit: 15-25%
- Stop loss: 7-10%
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import math

import pandas as pd

logger = logging.getLogger(__name__)

# Challenge data file
MILLION_CHALLENGE_FILE = Path(__file__).parent.parent.parent / "data" / "million_dollar_challenge.json"


@dataclass
class MillionChallengeConfig:
    """Configuration for the million dollar challenge."""
    starting_capital: float = 1000.0
    goal: float = 1_000_000.0
    
    # Contribution schedule
    monthly_contribution: float = 500.0  # $500/month
    contribution_frequency: str = "bimonthly"  # $250 twice per month
    
    # Position sizing (aggressive)
    position_size_pct: float = 0.25  # 25% per position
    max_positions: int = 4
    
    # Risk management (aggressive but controlled)
    stop_loss_pct: float = 0.08  # 8%
    take_profit_pct: float = 0.20  # 20% (2.5:1 R:R)
    max_daily_loss_pct: float = 0.10  # 10% max daily drawdown
    
    # Trading style
    min_hold_days: int = 1  # Minimum 1 day hold (avoid day trading)
    target_hold_days: int = 5  # Target 5 day swings
    
    # Asset allocation (aggressive growth)
    crypto_allocation: float = 0.50  # 50% crypto
    leveraged_etf_allocation: float = 0.30  # 30% leveraged ETFs
    momentum_stock_allocation: float = 0.20  # 20% momentum stocks
    
    # Preferred symbols
    crypto_symbols: List[str] = field(default_factory=lambda: [
        "BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD", "LINK/USD"
    ])
    
    leveraged_etfs: List[str] = field(default_factory=lambda: [
        "TQQQ",  # 3x Nasdaq-100
        "SOXL",  # 3x Semiconductors
        "TECL",  # 3x Technology
        "UPRO",  # 3x S&P 500
        "FNGU",  # 3x FANG+
    ])
    
    momentum_stocks: List[str] = field(default_factory=lambda: [
        "NVDA", "TSLA", "AMD", "SMCI", "ARM",
        "MSTR", "COIN", "PLTR", "IONQ", "RKLB"
    ])
    
    # Inverse ETFs for bear markets
    inverse_etfs: List[str] = field(default_factory=lambda: [
        "SQQQ", "SOXS", "TECS", "SPXS"
    ])


@dataclass
class ContributionRecord:
    """Record of a contribution."""
    amount: float
    date: str
    note: str = ""


@dataclass
class MillionChallengeState:
    """Current state of the million dollar challenge."""
    started_at: str = ""
    current_balance: float = 0.0
    starting_balance: float = 0.0
    goal: float = 1_000_000.0
    
    # Contribution tracking
    total_contributed: float = 0.0
    contributions: List[Dict] = field(default_factory=list)
    next_contribution_date: str = ""
    
    # Progress tracking
    peak_balance: float = 0.0
    lowest_balance: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    
    # Performance metrics
    best_month_pnl: float = 0.0
    worst_month_pnl: float = 0.0
    current_month_pnl: float = 0.0
    monthly_returns: List[Dict] = field(default_factory=list)
    
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
        return max(0, min(100, (self.current_balance / self.goal) * 100))
    
    @property
    def trading_gains(self) -> float:
        """Gains from trading only (excluding contributions)."""
        return self.current_balance - self.total_contributed - self.starting_balance
    
    @property
    def trading_gains_pct(self) -> float:
        """Trading gains as percentage of invested capital."""
        invested = self.starting_balance + self.total_contributed
        if invested <= 0:
            return 0.0
        return (self.trading_gains / invested) * 100
    
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
    def months_active(self) -> float:
        """Number of months since challenge started."""
        return self.days_active / 30.44  # Average days per month
    
    @property
    def avg_monthly_return_pct(self) -> float:
        """Average monthly return percentage."""
        if self.months_active < 1:
            return self.trading_gains_pct  # Return total if less than a month
        return self.trading_gains_pct / self.months_active


class MillionDollarChallenge:
    """Manages the million dollar growth challenge."""
    
    def __init__(self, starting_capital: float = 1000.0):
        self.config = MillionChallengeConfig(starting_capital=starting_capital)
        self.state = MillionChallengeState()
        
        # Ensure data directory exists
        MILLION_CHALLENGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing state or initialize new
        self._load_state()
        
        logger.info(f"Million Dollar Challenge initialized")
        logger.info(f"Starting: ${self.config.starting_capital:,.0f} → Goal: ${self.config.goal:,.0f}")
    
    def _load_state(self):
        """Load challenge state from file."""
        if MILLION_CHALLENGE_FILE.exists():
            try:
                with open(MILLION_CHALLENGE_FILE, 'r') as f:
                    data = json.load(f)
                    self.state = MillionChallengeState(**data)
                    logger.info(f"Loaded existing challenge: ${self.state.current_balance:,.2f}")
            except Exception as e:
                logger.error(f"Error loading state: {e}")
                self._initialize_new_challenge()
        else:
            self._initialize_new_challenge()
    
    def _save_state(self):
        """Save challenge state to file."""
        try:
            with open(MILLION_CHALLENGE_FILE, 'w') as f:
                json.dump(asdict(self.state), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _initialize_new_challenge(self):
        """Initialize a new challenge."""
        now = datetime.now()
        
        # Calculate first contribution date (15th of current or next month)
        if now.day <= 15:
            next_contrib = now.replace(day=15)
        else:
            # First of next month
            if now.month == 12:
                next_contrib = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_contrib = now.replace(month=now.month + 1, day=1)
        
        self.state = MillionChallengeState(
            started_at=now.isoformat(),
            current_balance=self.config.starting_capital,
            starting_balance=self.config.starting_capital,
            goal=self.config.goal,
            peak_balance=self.config.starting_capital,
            lowest_balance=self.config.starting_capital,
            total_contributed=0.0,
            next_contribution_date=next_contrib.strftime("%Y-%m-%d"),
        )
        self._save_state()
        logger.info(f"New million dollar challenge started with ${self.config.starting_capital:,.0f}")
    
    def add_contribution(self, amount: float, note: str = ""):
        """Record a contribution to the challenge."""
        contribution = ContributionRecord(
            amount=amount,
            date=datetime.now().isoformat(),
            note=note or f"Bi-monthly contribution"
        )
        
        self.state.contributions.append(asdict(contribution))
        self.state.total_contributed += amount
        self.state.current_balance += amount
        
        # Update next contribution date
        now = datetime.now()
        if now.day < 15:
            next_date = now.replace(day=15)
        else:
            # First of next month
            if now.month == 12:
                next_date = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_date = now.replace(month=now.month + 1, day=1)
        
        self.state.next_contribution_date = next_date.strftime("%Y-%m-%d")
        
        self._save_state()
        logger.info(f"Contribution recorded: ${amount:,.2f} | Total contributed: ${self.state.total_contributed:,.2f}")
    
    def calculate_eta_to_goal(self, target_monthly_return_pct: float = None) -> Dict[str, Any]:
        """Calculate estimated time to reach $1M goal.
        
        Uses either actual performance or projected returns.
        """
        current = self.state.current_balance
        goal = self.state.goal
        monthly_contrib = self.config.monthly_contribution
        
        # Use actual performance if we have enough data, otherwise use projections
        if self.state.months_active >= 1 and self.state.avg_monthly_return_pct > 0:
            monthly_return = self.state.avg_monthly_return_pct / 100
            based_on = "actual"
        else:
            # Use target for aggressive scalping strategy (45% monthly target)
            monthly_return = (target_monthly_return_pct or 45) / 100  # Default 45% monthly for scalping
            based_on = "projected"
        
        # Calculate months to goal with compound growth + contributions
        months = 0
        balance = current
        max_months = 240  # 20 year cap
        
        while balance < goal and months < max_months:
            # Monthly return on current balance
            balance = balance * (1 + monthly_return)
            # Add monthly contribution
            balance += monthly_contrib
            months += 1
        
        if months >= max_months:
            eta_date = None
            eta_str = "20+ years"
        else:
            eta_date = datetime.now() + timedelta(days=months * 30.44)
            years = months // 12
            remaining_months = months % 12
            if years > 0:
                eta_str = f"{years}y {remaining_months}m"
            else:
                eta_str = f"{remaining_months} months"
        
        return {
            "months_to_goal": months if months < max_months else None,
            "eta_date": eta_date.strftime("%B %Y") if eta_date else "20+ years",
            "eta_string": eta_str,
            "monthly_return_used": monthly_return * 100,
            "based_on": based_on,
            "assumptions": {
                "monthly_contribution": monthly_contrib,
                "monthly_return_pct": monthly_return * 100,
                "current_balance": current,
                "goal": goal,
            }
        }
    
    def calculate_scenarios(self) -> List[Dict[str, Any]]:
        """Calculate ETA under different return scenarios.
        
        Updated for aggressive scalping strategy (6% TP, 3% SL):
        - Conservative: 15% monthly (50% win rate, fewer trades)
        - Moderate: 25% monthly (55% win rate, normal activity)
        - Aggressive: 45% monthly (60% win rate, high activity) - TARGET
        - Best Case: 60% monthly (65% win rate, optimal conditions)
        """
        scenarios = [
            {"name": "Conservative", "monthly_return": 15, "color": "🟡"},
            {"name": "Moderate", "monthly_return": 25, "color": "🟢"},
            {"name": "Aggressive", "monthly_return": 45, "color": "🔵"},
            {"name": "Best Case", "monthly_return": 60, "color": "🟣"},
        ]
        
        results = []
        for scenario in scenarios:
            eta = self.calculate_eta_to_goal(scenario["monthly_return"])
            results.append({
                "name": scenario["name"],
                "color": scenario["color"],
                "monthly_return": scenario["monthly_return"],
                "eta_string": eta["eta_string"],
                "eta_date": eta["eta_date"],
                "months": eta["months_to_goal"],
            })
        
        return results
    
    def get_milestones(self) -> List[Dict[str, Any]]:
        """Get progress milestones."""
        milestones = [
            {"amount": 5_000, "name": "First $5K", "emoji": "🌱"},
            {"amount": 10_000, "name": "$10K Club", "emoji": "💪"},
            {"amount": 25_000, "name": "$25K Milestone", "emoji": "🚀"},
            {"amount": 50_000, "name": "Halfway to $100K", "emoji": "⭐"},
            {"amount": 100_000, "name": "Six Figures!", "emoji": "🎯"},
            {"amount": 250_000, "name": "Quarter Million", "emoji": "💎"},
            {"amount": 500_000, "name": "Half Million", "emoji": "👑"},
            {"amount": 750_000, "name": "Three Quarters", "emoji": "🔥"},
            {"amount": 1_000_000, "name": "MILLIONAIRE!", "emoji": "🏆"},
        ]
        
        current = self.state.current_balance
        
        for m in milestones:
            m["reached"] = current >= m["amount"]
            m["progress_pct"] = min(100, (current / m["amount"]) * 100)
            if not m["reached"]:
                m["remaining"] = m["amount"] - current
        
        return milestones
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive challenge status."""
        eta = self.calculate_eta_to_goal()
        scenarios = self.calculate_scenarios()
        milestones = self.get_milestones()
        
        # Find next milestone
        next_milestone = None
        for m in milestones:
            if not m["reached"]:
                next_milestone = m
                break
        
        return {
            "challenge": {
                "started": self.state.started_at,
                "days_active": self.state.days_active,
                "months_active": round(self.state.months_active, 1),
                "starting_balance": self.state.starting_balance,
                "current_balance": self.state.current_balance,
                "goal": self.state.goal,
                "progress_pct": self.state.progress_pct,
                "goal_reached": self.state.current_balance >= self.state.goal,
            },
            "contributions": {
                "total_contributed": self.state.total_contributed,
                "monthly_amount": self.config.monthly_contribution,
                "frequency": self.config.contribution_frequency,
                "next_date": self.state.next_contribution_date,
                "count": len(self.state.contributions),
            },
            "performance": {
                "trading_gains": self.state.trading_gains,
                "trading_gains_pct": self.state.trading_gains_pct,
                "total_pnl": self.state.total_pnl,
                "peak_balance": self.state.peak_balance,
                "lowest_balance": self.state.lowest_balance,
                "max_drawdown_pct": ((self.state.peak_balance - self.state.lowest_balance) / self.state.peak_balance) * 100 if self.state.peak_balance > 0 else 0,
                "avg_monthly_return_pct": self.state.avg_monthly_return_pct,
            },
            "trades": {
                "total": self.state.total_trades,
                "winning": self.state.winning_trades,
                "losing": self.state.losing_trades,
                "win_rate": self.state.win_rate,
            },
            "eta": eta,
            "scenarios": scenarios,
            "milestones": milestones,
            "next_milestone": next_milestone,
            "config": {
                "position_size_pct": self.config.position_size_pct * 100,
                "max_positions": self.config.max_positions,
                "stop_loss_pct": self.config.stop_loss_pct * 100,
                "take_profit_pct": self.config.take_profit_pct * 100,
                "crypto_allocation": self.config.crypto_allocation * 100,
                "leveraged_etf_allocation": self.config.leveraged_etf_allocation * 100,
                "momentum_stock_allocation": self.config.momentum_stock_allocation * 100,
            }
        }
    
    def print_status(self):
        """Print a formatted status report."""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("💰 MILLION DOLLAR CHALLENGE STATUS")
        print("="*60)
        
        c = status["challenge"]
        print(f"\n📊 Current Balance: ${c['current_balance']:,.2f}")
        print(f"🎯 Goal: ${c['goal']:,.0f}")
        print(f"📈 Progress: {c['progress_pct']:.3f}%")
        print(f"📅 Active: {c['days_active']} days ({c['months_active']:.1f} months)")
        
        contrib = status["contributions"]
        print(f"\n💵 Total Contributed: ${contrib['total_contributed']:,.2f}")
        print(f"📆 Next Contribution: {contrib['next_date']} (${contrib['monthly_amount']/2:.0f})")
        
        p = status["performance"]
        print(f"\n📈 Trading Gains: ${p['trading_gains']:,.2f} ({p['trading_gains_pct']:.1f}%)")
        print(f"🔝 Peak Balance: ${p['peak_balance']:,.2f}")
        print(f"📉 Max Drawdown: {p['max_drawdown_pct']:.1f}%")
        
        eta = status["eta"]
        print(f"\n⏱️ ETA to $1M: {eta['eta_string']} ({eta['eta_date']})")
        print(f"   Based on: {eta['based_on']} {eta['monthly_return_used']:.1f}% monthly return")
        
        print("\n📊 Scenarios:")
        for s in status["scenarios"]:
            print(f"   {s['color']} {s['name']} ({s['monthly_return']}%/mo): {s['eta_string']}")
        
        nm = status["next_milestone"]
        if nm:
            print(f"\n🎯 Next Milestone: {nm['emoji']} {nm['name']} (${nm['amount']:,.0f})")
            print(f"   ${nm['remaining']:,.2f} to go ({nm['progress_pct']:.1f}% complete)")
        
        if c["goal_reached"]:
            print("\n🎉🎉🎉 CONGRATULATIONS! YOU'RE A MILLIONAIRE! 🎉🎉🎉")
        
        print("="*60 + "\n")


def main():
    """Entry point for challenge status check."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    challenge = MillionDollarChallenge(starting_capital=1000.0)
    challenge.print_status()


if __name__ == "__main__":
    main()
