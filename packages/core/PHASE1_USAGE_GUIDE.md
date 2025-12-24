# Phase 1 Improvements - Usage Guide

## Overview

Phase 1 adds three critical improvements to the QuantShift trading system:
1. **Backtesting Framework** - Validate strategies before live trading
2. **Kelly Criterion Position Sizing** - Optimal capital allocation
3. **Multi-Timeframe Analysis** - Reduce false signals

All improvements are in the `quantshift-core` package and available to both equity and crypto bots.

---

## 1. Backtesting Framework

### Basic Usage

```python
from quantshift_core import BacktestEngine
import pandas as pd

# Initialize backtest engine
engine = BacktestEngine(
    initial_capital=10000.0,
    commission=0.0,  # Alpaca is commission-free
    slippage=0.001   # 0.1% slippage
)

# Execute trades
engine.execute_trade(
    symbol="AAPL",
    action="BUY",
    price=150.00,
    quantity=10,
    timestamp=datetime.now(),
    stop_loss=145.00,
    take_profit=160.00
)

# Later, sell
engine.execute_trade(
    symbol="AAPL",
    action="SELL",
    price=155.00,
    quantity=10,
    timestamp=datetime.now()
)

# Get performance metrics
metrics = engine.get_metrics()
print(f"Win Rate: {metrics['win_rate']:.2f}%")
print(f"Total Return: {metrics['total_return']:.2f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
```

### Walk-Forward Optimization

```python
from quantshift_core import WalkForwardOptimizer

# Define parameter ranges to test
param_ranges = {
    'fast_ma': [10, 20, 30],
    'slow_ma': [50, 100, 200],
    'rsi_period': [14, 21, 28]
}

# Initialize optimizer
optimizer = WalkForwardOptimizer(
    strategy_class=YourStrategy,
    data=historical_data,
    param_ranges=param_ranges,
    in_sample_periods=252,   # 1 year training
    out_sample_periods=63    # 3 months testing
)

# Run optimization
results = optimizer.optimize()
print(f"Average Out-Sample Return: {results['avg_out_sample_return']:.2f}%")
print(f"Average Out-Sample Sharpe: {results['avg_out_sample_sharpe']:.2f}")
```

---

## 2. Kelly Criterion Position Sizing

### Fixed Fractional (Current Method - Improved)

```python
from quantshift_core import PositionSizer

# Initialize position sizer
sizer = PositionSizer(
    account_balance=10000.0,
    max_position_pct=0.20,      # Max 20% per position
    max_portfolio_risk=0.06     # Max 6% total portfolio risk
)

# Calculate position size
shares = sizer.fixed_fractional(
    entry_price=150.00,
    stop_loss=145.00,
    risk_per_trade=0.02  # Risk 2% of account
)

print(f"Buy {shares} shares")
```

### Kelly Criterion (Optimal Sizing)

```python
# Calculate position size using Kelly Criterion
shares = sizer.kelly_criterion(
    win_rate=0.60,           # 60% win rate
    avg_win=500.00,          # Average win: $500
    avg_loss=250.00,         # Average loss: $250
    entry_price=150.00,
    kelly_fraction=0.25      # Use 1/4 Kelly (conservative)
)

print(f"Kelly suggests {shares} shares")
```

### ATR-Based Sizing

```python
# Position size based on volatility (ATR)
shares = sizer.atr_based(
    entry_price=150.00,
    atr=3.50,               # Average True Range
    atr_multiplier=2.0,     # 2x ATR for stop loss
    risk_per_trade=0.02
)

print(f"ATR-based: {shares} shares")
```

### Portfolio Risk Management

```python
from quantshift_core import RiskManager

risk_mgr = RiskManager(
    max_portfolio_risk=0.06,      # 6% max total risk
    max_correlated_risk=0.10,     # 10% max correlated positions
    max_sector_exposure=0.30      # 30% max per sector
)

# Check if new position can be opened
current_positions = {
    "AAPL": {
        "quantity": 10,
        "current_price": 150.00,
        "stop_loss": 145.00
    }
}

can_trade = risk_mgr.can_open_position(
    positions=current_positions,
    account_balance=10000.0,
    new_position_risk=200.00  # $200 risk for new trade
)

if can_trade:
    print("Safe to open new position")
else:
    print("Portfolio risk limit exceeded")
```

---

## 3. Multi-Timeframe Analysis

### Check Trend Alignment

```python
from quantshift_core import MultiTimeframeAnalyzer

analyzer = MultiTimeframeAnalyzer()

# Check if trends align across timeframes
alignment = analyzer.check_trend_alignment(
    daily_data=daily_df,      # Daily OHLCV data
    hourly_data=hourly_df,    # Hourly OHLCV data
    current_data=current_df   # Current timeframe (e.g., 15min)
)

print(f"Daily Trend: {alignment['daily_trend']}")
print(f"Hourly Trend: {alignment['hourly_trend']}")
print(f"Current Trend: {alignment['current_trend']}")
print(f"Aligned: {alignment['aligned']}")
print(f"Direction: {alignment['direction']}")
print(f"Strength (ADX): {alignment['strength']:.2f}")
```

### Trade Approval

```python
# Check if trade should be taken
should_trade, reason = analyzer.should_trade(
    symbol="AAPL",
    daily_data=daily_df,
    hourly_data=hourly_df,
    current_data=current_df,
    direction="long"  # or "short"
)

if should_trade:
    print(f"✅ Trade approved: {reason}")
else:
    print(f"❌ Trade rejected: {reason}")
```

### Entry Timing

```python
# Get optimal entry timing
timing = analyzer.get_entry_timing(
    data=current_df,
    direction="long"
)

if timing['ready']:
    print(f"✅ Good entry: {timing['reason']}")
else:
    print(f"⏳ Wait: {timing['reason']}")
```

### Support/Resistance Levels

```python
# Identify key levels
levels = analyzer.get_support_resistance(
    data=daily_df,
    lookback=50
)

print(f"Support Levels: {levels['support']}")
print(f"Resistance Levels: {levels['resistance']}")
```

---

## Complete Trading Example

```python
from quantshift_core import (
    PositionSizer,
    RiskManager,
    MultiTimeframeAnalyzer,
    BacktestEngine
)

# Initialize components
sizer = PositionSizer(account_balance=10000.0)
risk_mgr = RiskManager()
analyzer = MultiTimeframeAnalyzer()

# 1. Check multi-timeframe alignment
should_trade, reason = analyzer.should_trade(
    symbol="AAPL",
    daily_data=daily_df,
    hourly_data=hourly_df,
    current_data=current_df,
    direction="long"
)

if not should_trade:
    print(f"Trade rejected: {reason}")
    exit()

# 2. Check entry timing
timing = analyzer.get_entry_timing(current_df, "long")
if not timing['ready']:
    print(f"Wait for better entry: {timing['reason']}")
    exit()

# 3. Calculate position size using Kelly Criterion
entry_price = current_df['close'].iloc[-1]
atr = calculate_atr(current_df)  # Your ATR calculation

shares = sizer.kelly_criterion(
    win_rate=0.60,
    avg_win=500.00,
    avg_loss=250.00,
    entry_price=entry_price,
    kelly_fraction=0.25
)

# 4. Check portfolio risk
stop_loss = entry_price - (atr * 2)
position_risk = shares * (entry_price - stop_loss)

can_trade = risk_mgr.can_open_position(
    positions=current_positions,
    account_balance=10000.0,
    new_position_risk=position_risk
)

if not can_trade:
    print("Portfolio risk limit exceeded")
    exit()

# 5. Execute trade
print(f"✅ All checks passed!")
print(f"Buy {shares} shares of AAPL at ${entry_price:.2f}")
print(f"Stop Loss: ${stop_loss:.2f}")
print(f"Position Risk: ${position_risk:.2f}")
```

---

## Integration with Existing Bot

### Update Your Bot Strategy

```python
# In your bot's strategy file
from quantshift_core import (
    PositionSizer,
    MultiTimeframeAnalyzer,
    TechnicalIndicators
)

class ImprovedStrategy:
    def __init__(self, account_balance):
        self.sizer = PositionSizer(account_balance)
        self.analyzer = MultiTimeframeAnalyzer()
        self.indicators = TechnicalIndicators()
    
    def generate_signal(self, daily_df, hourly_df, current_df):
        # Check multi-timeframe alignment
        should_trade, reason = self.analyzer.should_trade(
            symbol="AAPL",
            daily_data=daily_df,
            hourly_data=hourly_df,
            current_data=current_df,
            direction="long"
        )
        
        if not should_trade:
            return None
        
        # Check entry timing
        timing = self.analyzer.get_entry_timing(current_df, "long")
        if not timing['ready']:
            return None
        
        return "BUY"
    
    def calculate_position_size(self, entry_price, stop_loss, win_rate, avg_win, avg_loss):
        # Use Kelly Criterion instead of fixed percentage
        return self.sizer.kelly_criterion(
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            entry_price=entry_price,
            kelly_fraction=0.25
        )
```

---

## Testing Phase 1 Improvements

### On Standby Container (Paper Trading)

```bash
# SSH to standby
ssh quantshift-standby

# Check logs
tail -f /opt/quantshift/logs/equity-bot.log

# Monitor for 3-7 days
# Compare metrics to primary bot
```

### Metrics to Track

1. **Win Rate** - Should improve with multi-timeframe filters
2. **Profit Factor** - Should improve with Kelly Criterion
3. **Max Drawdown** - Should decrease with better risk management
4. **Sharpe Ratio** - Should increase overall

---

## Next Steps

1. ✅ Phase 1 deployed to standby (LXC 101)
2. ⏳ Monitor performance for 3-7 days
3. ⏳ Compare to primary bot metrics
4. ⏳ If improved, deploy to primary (LXC 100)
5. ⏳ Deploy crypto bot (inherits Phase 1 automatically)

---

## Expected Improvements

Based on industry standards and your earlier analysis:

| Metric | Before | After Phase 1 | Improvement |
|--------|--------|---------------|-------------|
| Win Rate | 59.4% | 65-70% | +5-10% |
| Profit Factor | Unknown | 1.8-2.5 | Measurable |
| Max Drawdown | Unknown | 15-25% | Controlled |
| Sharpe Ratio | Unknown | 1.5-2.5 | Good |
| Annual Return | 100%+ | 50-80% | More sustainable |

---

## Support

All Phase 1 improvements are in `quantshift-core` package:
- `backtesting.py` - Backtesting framework
- `position_sizing.py` - Kelly Criterion and risk management
- `indicators.py` - Multi-timeframe analysis

Both equity and crypto bots automatically inherit these improvements.
