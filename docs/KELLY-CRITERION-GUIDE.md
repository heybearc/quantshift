# Kelly Criterion Position Sizing Guide

**Version:** 1.10.0  
**Status:** Implemented, Disabled by Default  
**Phase:** 4 - Advanced Position Sizing

---

## Overview

The Kelly Criterion is a mathematical formula for optimal position sizing that maximizes long-term growth while managing risk. QuantShift implements **fractional Kelly** (25% Kelly) for safety and requires minimum trade history for reliable calculations.

### Why Kelly Criterion?

**Traditional Fixed Fractional:**
- Always risk 1% per trade
- Doesn't adapt to strategy performance
- May be too conservative for winning strategies
- May be too aggressive for struggling strategies

**Kelly Criterion:**
- Adapts position size based on historical win rate and profit/loss
- Maximizes long-term growth rate
- Reduces position size when performance degrades
- Increases position size when performance improves

---

## The Formula

```
Kelly % = (Win Rate × Avg Win - (1 - Win Rate) × Avg Loss) / Avg Win
```

**Fractional Kelly (Safety):**
```
Position Size = Account Value × (Kelly % × 0.25)
```

### Example Calculation

**Strategy Stats:**
- Win Rate: 60% (0.60)
- Average Win: $500
- Average Loss: $300

```
Kelly % = (0.60 × $500 - 0.40 × $300) / $500
        = ($300 - $120) / $500
        = $180 / $500
        = 0.36 (36%)

Fractional Kelly (25%) = 0.36 × 0.25 = 0.09 (9%)
```

With $10,000 account: Position size = $10,000 × 0.09 = $900

---

## Implementation Details

### File Structure

```
packages/core/src/quantshift_core/
├── kelly_position_sizer.py    # Kelly Criterion calculator
└── risk_manager.py             # Integration with RiskManager
```

### Key Components

#### 1. KellyPositionSizer Class

**Features:**
- Fractional Kelly calculation (default 25%)
- Minimum trade requirement (default 20 trades)
- Rolling window analysis (last 30 trades)
- Automatic fallback to fixed 1% risk
- Per-strategy calculation support

**Methods:**
- `calculate_trade_stats()` - Analyze historical trades
- `calculate_kelly_percentage()` - Compute Kelly %
- `get_position_size()` - Calculate shares to buy
- `get_kelly_stats_summary()` - Get statistics for monitoring

#### 2. RiskManager Integration

**Methods:**
- `calculate_kelly_position_size()` - Calculate position using Kelly
- `get_kelly_stats()` - Get Kelly statistics for dashboard

**Database Integration:**
- Fetches last 100 closed trades
- Filters by bot name and strategy
- Converts to Kelly sizer format
- Handles errors gracefully

---

## Configuration

### Enable Kelly Criterion

**File:** `config/equity_config.yaml`

```yaml
risk_management:
  # ... other settings ...
  
  # Kelly Criterion position sizing
  use_kelly_sizing: true        # Enable Kelly Criterion
  kelly_fraction: 0.25          # Use 25% Kelly for safety
  kelly_min_trades: 20          # Minimum trades required
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_kelly_sizing` | `false` | Enable/disable Kelly Criterion |
| `kelly_fraction` | `0.25` | Fractional Kelly (0.25 = 25% Kelly) |
| `kelly_min_trades` | `20` | Minimum trades for calculation |

### Safety Recommendations

**Fractional Kelly Values:**
- `0.10` (10% Kelly) - Very conservative, slow growth
- `0.25` (25% Kelly) - **Recommended**, good balance
- `0.50` (50% Kelly) - Moderate risk, faster growth
- `1.00` (100% Kelly) - **Not recommended**, high volatility

**Minimum Trades:**
- `20` trades - **Recommended minimum**
- `30` trades - Better statistical reliability
- `50+` trades - High confidence in calculations

---

## Usage Example

### Basic Usage

```python
from quantshift_core.kelly_position_sizer import KellyPositionSizer

# Initialize Kelly sizer
kelly_sizer = KellyPositionSizer(
    kelly_fraction=0.25,
    min_trades_required=20,
    lookback_trades=30
)

# Calculate position size
shares, risk_amount, method = kelly_sizer.get_position_size(
    account_value=10000,
    entry_price=50.00,
    stop_loss_price=48.00,
    trades=historical_trades,
    strategy_name="BollingerBounce"
)

print(f"Buy {shares} shares using {method} method")
print(f"Risk amount: ${risk_amount:.2f}")
```

### With RiskManager

```python
from quantshift_core.risk_manager import RiskManager

# Initialize RiskManager with Kelly enabled
risk_manager = RiskManager(
    max_portfolio_heat=0.10,
    use_kelly_sizing=True,
    kelly_fraction=0.25,
    kelly_min_trades=20,
    db_manager=db_manager
)

# Calculate position size for a signal
shares, method = risk_manager.calculate_kelly_position_size(
    signal=buy_signal,
    account=account,
    bot_name="quantshift-equity",
    strategy_name="BollingerBounce"
)

# Get Kelly statistics
kelly_stats = risk_manager.get_kelly_stats(
    bot_name="quantshift-equity",
    strategy_name="BollingerBounce"
)
```

---

## Monitoring & Statistics

### Kelly Stats Output

```python
{
    "has_sufficient_data": True,
    "trade_count": 35,
    "win_rate": 0.60,
    "avg_win": 500.00,
    "avg_loss": 300.00,
    "profit_factor": 2.0,
    "raw_kelly_pct": 0.36,
    "fractional_kelly_pct": 0.09,
    "kelly_fraction": 0.25,
    "method": "kelly"
}
```

### Insufficient Data Output

```python
{
    "has_sufficient_data": False,
    "trade_count": 15,
    "required_trades": 20,
    "method": "fixed_fractional",
    "default_risk_pct": 0.01
}
```

---

## Behavior & Fallbacks

### Automatic Fallback Scenarios

1. **Insufficient Trades** (< 20 trades)
   - Falls back to fixed 1% risk
   - Logs reason: "insufficient_trades"
   
2. **Database Error**
   - Falls back to fixed 1% risk
   - Logs error details
   
3. **Invalid Stop Loss**
   - Returns 0 shares
   - Logs warning
   
4. **Negative Kelly %**
   - Returns 0 shares (strategy losing money)
   - Prevents taking positions in losing strategies

### Position Size Caps

- **Maximum:** 5% of account value (configurable)
- **Minimum:** 0 shares (no negative positions)
- **Kelly Negative:** 0 shares (don't trade losing strategies)

---

## Best Practices

### When to Enable Kelly

✅ **Enable Kelly When:**
- You have 20+ closed trades
- Strategy is profitable (profit factor > 1.0)
- Win rate is stable (not fluctuating wildly)
- You understand the risks of variable position sizing

❌ **Don't Enable Kelly When:**
- Starting a new strategy (< 20 trades)
- Strategy is losing money
- Win rate is unstable
- You prefer consistent position sizes

### Monitoring Recommendations

**Daily:**
- Check Kelly statistics in logs
- Monitor position sizes vs. fixed fractional
- Watch for "insufficient_trades" fallbacks

**Weekly:**
- Review win rate trends
- Check profit factor stability
- Verify Kelly % is reasonable (< 50%)

**Monthly:**
- Analyze Kelly vs. fixed fractional performance
- Adjust `kelly_fraction` if needed
- Review trade count requirements

---

## Troubleshooting

### Issue: Kelly % Too High (> 20%)

**Cause:** Exceptional win rate or profit factor  
**Solution:**
- Verify trade statistics are accurate
- Consider lowering `kelly_fraction` to 0.10-0.15
- Check for data quality issues

### Issue: Always Using Fixed Fractional

**Cause:** Insufficient trade history  
**Solution:**
- Wait for more trades to accumulate
- Check `kelly_min_trades` setting
- Verify database connection

### Issue: Position Sizes Too Small

**Cause:** Low Kelly % from poor performance  
**Solution:**
- Review strategy performance
- Check win rate and profit factor
- Consider if strategy needs optimization
- May indicate strategy should be disabled

### Issue: Position Sizes Too Large

**Cause:** High Kelly % from good performance  
**Solution:**
- Lower `kelly_fraction` (e.g., 0.15 instead of 0.25)
- Verify statistics are accurate
- Check for overfitting in backtest

---

## Performance Comparison

### Expected Outcomes

**Fixed 1% Risk:**
- Consistent position sizes
- Predictable risk per trade
- Slower growth
- Easier to understand

**25% Kelly:**
- Variable position sizes (0-5% of account)
- Adapts to strategy performance
- Faster growth when winning
- Smaller positions when losing
- More complex to monitor

### Backtest Comparison (Example)

| Metric | Fixed 1% | 25% Kelly | Improvement |
|--------|----------|-----------|-------------|
| Total Return | 15% | 22% | +47% |
| Max Drawdown | -8% | -12% | -50% worse |
| Sharpe Ratio | 1.2 | 1.5 | +25% |
| Win Rate | 60% | 60% | Same |
| Avg Position | 1% | 2.5% | +150% |

---

## Advanced Topics

### Per-Strategy Kelly

Kelly can be calculated separately for each strategy:

```python
# Get Kelly stats for specific strategy
kelly_stats = risk_manager.get_kelly_stats(
    bot_name="quantshift-equity",
    strategy_name="BollingerBounce"  # Strategy-specific
)
```

**Benefits:**
- Adapts to each strategy's performance
- Better strategies get larger positions
- Worse strategies get smaller positions

### Rolling Window Analysis

Kelly uses the last 30 trades by default:

```python
kelly_sizer = KellyPositionSizer(
    lookback_trades=30  # Analyze last 30 trades
)
```

**Trade-offs:**
- Smaller window (20): More responsive, less stable
- Larger window (50): More stable, less responsive
- **Recommended:** 30 trades

---

## References

### Academic Papers

1. Kelly, J. L. (1956). "A New Interpretation of Information Rate"
2. Thorp, E. O. (2008). "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"

### Implementation Notes

- Uses fractional Kelly for safety (Thorp's recommendation)
- Requires minimum trade history (industry standard)
- Caps maximum position size (risk management)
- Automatic fallback to fixed fractional (robustness)

---

## Summary

**Kelly Criterion Benefits:**
- ✅ Optimal long-term growth
- ✅ Adapts to strategy performance
- ✅ Reduces risk in losing periods
- ✅ Increases size in winning periods

**Implementation Features:**
- ✅ Fractional Kelly (25%) for safety
- ✅ Minimum 20 trades requirement
- ✅ Automatic fallback to fixed 1% risk
- ✅ Per-strategy calculation
- ✅ Comprehensive monitoring

**Status:**
- ✅ Implemented in v1.10.0
- ⏳ Disabled by default
- ⏳ Enable after 20+ trades
- ⏳ Monitor performance carefully

**Next Steps:**
1. Accumulate 20+ trades per strategy
2. Review Kelly statistics
3. Enable `use_kelly_sizing: true` in config
4. Monitor position sizes and performance
5. Adjust `kelly_fraction` if needed
