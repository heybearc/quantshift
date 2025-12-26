# Phase 1 Backtest Analysis - MA Crossover Strategy

**Date:** December 26, 2025  
**Status:** ❌ **FAILED VALIDATION**

---

## Executive Summary

The Moving Average Crossover strategy (MA 20/50) with enhanced filters **failed to meet performance targets** in backtesting. The strategy was too conservative, generating only 2 trades over 3 years, both resulting in losses.

**Key Finding:** The combination of volume confirmation, trend confirmation, and support/resistance filters is **too restrictive**, preventing the strategy from taking trades even during valid crossover signals.

---

## Backtest Configuration

| Parameter | Value |
|-----------|-------|
| Symbol | SPY |
| Period | 2022-01-01 to 2024-12-31 (3 years) |
| Initial Capital | $10,000 |
| Data Points | 752 bars (daily) |
| Commission | $0 (Alpaca zero commission) |
| Slippage | 5 bps (0.05%) |

**Strategy Parameters:**
- Short MA: 20 days
- Long MA: 50 days
- ATR Period: 14 days
- Risk per Trade: 2%
- Max Positions: 5
- **Volume Confirmation: Enabled** ⚠️
- **Trend Confirmation: Enabled** ⚠️
- **Support/Resistance Filter: Enabled** ⚠️

---

## Performance Results

### Trading Statistics
| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Total Trades | 2 | N/A | ⚠️ Too Few |
| Winning Trades | 0 | N/A | ❌ |
| Losing Trades | 2 | N/A | ❌ |
| **Win Rate** | **0.00%** | **≥50%** | **❌ FAIL** |
| Average Win | $0.00 | N/A | N/A |
| Average Loss | $281.00 | N/A | ❌ |
| **Profit Factor** | **0.00** | **≥1.5** | **❌ FAIL** |

### Returns
| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| **Total Return** | **-5.72%** | **≥15%** | **❌ FAIL** |
| Final Equity | $9,428.49 | N/A | ❌ Loss |
| Profit/Loss | -$571.51 | N/A | ❌ |

### Risk Metrics
| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| **Max Drawdown** | **9.18%** | **<15%** | **✓ PASS** |
| **Sharpe Ratio** | **-0.61** | **≥1.5** | **❌ FAIL** |
| Avg Hold Time | 504 hours (21 days) | N/A | ⚠️ Long |

---

## Trade Analysis

### Trade #1: June 2022
- **Entry:** $400.63 (Golden Cross detected)
- **Exit:** $385.89 (Stop Loss hit)
- **P&L:** -$358.51 (-3.7%)
- **Hold Time:** ~21 days
- **Outcome:** Market continued downward in 2022 bear market

### Trade #2: November 2024
- **Entry:** $552.16 (Golden Cross detected)
- **Exit:** $540.46 (Stop Loss hit)
- **P&L:** -$203.49 (-2.1%)
- **Hold Time:** ~21 days
- **Outcome:** Market pullback triggered stop loss

---

## Root Cause Analysis

### 1. **Filters Too Restrictive**

The strategy logged multiple "golden_cross_filtered" events:
- **Volume confirmation failed** - Multiple times
- **Too close to resistance** - Multiple times
- **Weekly trend not aligned** - Implied by lack of trades

**Impact:** Valid MA crossover signals were rejected, preventing trades during potentially profitable periods.

### 2. **Insufficient Trade Frequency**

- **2 trades in 3 years** = 0.67 trades/year
- **Industry Standard:** 10-50 trades/year for daily strategies
- **Problem:** Not enough data to validate strategy effectiveness

### 3. **Both Trades Hit Stop Losses**

- Both trades were stopped out at -2% to -4% losses
- No trades reached take profit targets
- Suggests stop losses may be too tight or entry timing is poor

### 4. **Market Conditions**

- **2022:** Bear market (-18% for SPY)
- **2023:** Strong bull market (+24% for SPY)
- **2024:** Continued bull market (+23% for SPY)
- Strategy missed the entire 2023-2024 bull run!

---

## Comparison: Buy & Hold vs Strategy

| Metric | MA Crossover | Buy & Hold SPY |
|--------|--------------|----------------|
| Total Return | -5.72% | +22.8% |
| Max Drawdown | -9.18% | -25.4% |
| Trades | 2 | 0 |
| **Result** | **Lost Money** | **Made Money** |

**Conclusion:** A simple buy-and-hold strategy significantly outperformed our MA Crossover strategy.

---

## Recommendations

### Option A: Simplify Strategy (Recommended)
**Remove all filters and test pure MA crossover**

```yaml
strategy:
  volume_confirmation: false      # DISABLE
  trend_confirmation: false       # DISABLE
  support_resistance_filter: false # DISABLE
```

**Expected Impact:**
- More trades (10-20 over 3 years)
- Better sample size for validation
- Simpler logic, easier to understand

**Risk:** May generate false signals, but at least we'll have data

---

### Option B: Adjust Filter Thresholds
**Relax filter requirements**

```yaml
filters:
  volume:
    min_volume_ratio: 1.0  # Down from 1.2
  support_resistance:
    proximity_threshold: 0.05  # Up from 0.01 (5% buffer)
```

**Expected Impact:**
- Moderate increase in trades
- Still maintains some quality control
- May still be too conservative

---

### Option C: Different Strategy Entirely
**Try a different approach**

Options:
1. **RSI Mean Reversion** - Trade oversold/overbought conditions
2. **Breakout Strategy** - Trade new highs/lows
3. **Dual Momentum** - Combine trend and momentum
4. **Buy & Hold with Rebalancing** - Simple but effective

**Pros:** Fresh approach, different market conditions
**Cons:** More development time, same validation needed

---

### Option D: Shorter Timeframe
**Test on hourly or 4-hour data instead of daily**

**Pros:** More trading opportunities
**Cons:** More noise, higher transaction costs, more complexity

---

## Decision Matrix

| Option | Effort | Time | Success Probability | Recommendation |
|--------|--------|------|-------------------|----------------|
| **A: Simplify** | Low | 1 hour | High | ⭐⭐⭐⭐⭐ |
| B: Adjust Filters | Low | 1 hour | Medium | ⭐⭐⭐ |
| C: New Strategy | High | 1 week | Medium | ⭐⭐ |
| D: Shorter TF | Medium | 2 days | Low | ⭐ |

---

## Recommended Next Steps

### Immediate Action: Option A - Simplify Strategy

1. **Disable all filters** in strategy configuration
2. **Re-run backtest** with pure MA crossover
3. **Analyze results:**
   - If still poor → Try Option C (different strategy)
   - If improved but not meeting targets → Try Option B (adjust filters)
   - If meets targets → Proceed to Phase 2 (integration)

### Timeline
- **Today:** Re-run backtest with simplified strategy (1 hour)
- **Tomorrow:** Analyze results and make go/no-go decision
- **This Week:** Either proceed to Phase 2 or iterate on strategy

---

## Lessons Learned

### What Worked
✓ Broker-agnostic architecture made backtesting easy
✓ Comprehensive metrics and reporting
✓ Realistic cost modeling (slippage)
✓ Proper risk management (2% per trade)

### What Didn't Work
❌ Over-engineering with too many filters
❌ Not testing simpler version first
❌ Filters not validated independently

### Best Practices for Future
1. **Start simple, add complexity gradually**
2. **Test each filter independently**
3. **Require minimum trade frequency** (e.g., 10+ trades)
4. **Compare to buy-and-hold baseline**
5. **Test in different market conditions**

---

## Conclusion

The MA Crossover strategy with enhanced filters **failed validation** due to being too conservative. The strategy needs to be simplified by removing filters to generate sufficient trades for proper evaluation.

**Recommendation:** Proceed with **Option A** - disable all filters and re-run backtest with pure MA crossover strategy.

**Expected Outcome:** 10-20 trades over 3 years, providing adequate sample size to evaluate strategy effectiveness.

**Go/No-Go Decision:** Pending simplified backtest results.

---

## Appendix: Filter Analysis

### Volume Confirmation Filter
- **Purpose:** Ensure trades have strong volume support
- **Threshold:** Volume > 1.2x 20-day average
- **Impact:** Rejected multiple golden cross signals
- **Assessment:** Too restrictive for daily timeframe

### Trend Confirmation Filter  
- **Purpose:** Align with weekly trend
- **Method:** Weekly MA 10/20 crossover
- **Impact:** Unknown (not enough trades to assess)
- **Assessment:** May be preventing trades during trend changes

### Support/Resistance Filter
- **Purpose:** Avoid buying near resistance
- **Threshold:** Must be >1% away from 20-day high
- **Impact:** Rejected multiple signals
- **Assessment:** Too tight for volatile markets

**Overall Assessment:** Filters are well-intentioned but collectively too restrictive for this strategy and timeframe.
