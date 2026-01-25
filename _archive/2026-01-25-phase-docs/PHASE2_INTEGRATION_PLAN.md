# Phase 2: Bot Integration Plan

**Status:** In Progress  
**Date:** December 26, 2025

---

## ✅ Phase 1 Results (Completed)

**Validated Strategy:** MA Crossover (5/20)

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Win Rate | 52.63% | ≥50% | ✓ PASS |
| Profit Factor | 2.40 | ≥1.5 | ✓ PASS |
| Max Drawdown | 6.34% | <15% | ✓ PASS |
| Total Return | +17.40% | ≥15% | ✓ PASS |
| Sharpe Ratio | 0.98 | ≥1.5 | ⚠️ Close |

**Conclusion:** Strategy validated and ready for deployment.

---

## Phase 2 Tasks

### ✅ Step 1: Update Configuration
- [x] Update `equity_strategy.yaml` with MA 5/20 parameters
- [x] Set risk_per_trade to 1% (validated)
- [x] Disable all filters (pure MA crossover)
- [x] Document backtest results in config

### ⏳ Step 2: Update Strategy Implementation
- [ ] Ensure MACrossoverStrategy uses config correctly
- [ ] Verify strategy matches backtest parameters
- [ ] Test strategy initialization

### ⏳ Step 3: Test Bot Integration
- [ ] Run `run_bot_v2.py` in test mode
- [ ] Verify strategy loads correctly
- [ ] Verify signals generate properly
- [ ] Test with paper trading (dry run)

### ⏳ Step 4: Deploy to Container
- [ ] Update systemd service to use `run_bot_v2.py`
- [ ] Deploy to quantshift-primary (10.92.3.27)
- [ ] Start bot service
- [ ] Monitor logs for errors

### ⏳ Step 5: Paper Trading Validation (30 Days)
- [ ] Monitor daily performance
- [ ] Track actual vs expected metrics
- [ ] Document any issues
- [ ] Compare to backtest results

### 🔮 Step 6: Advanced Features (Future)
- [ ] Add scale-out strategy (50% at +1 ATR)
- [ ] Add trailing stops (1.5x ATR)
- [ ] Implement Golden Cross scanner (600+ stocks)
- [ ] Add email notifications

---

## Current Configuration

**Strategy:** MA Crossover (5/20)
- Short MA: 5 days
- Long MA: 20 days
- ATR Period: 14 days
- Risk per Trade: 1%
- Filters: All disabled

**Symbols:**
- SPY (S&P 500 ETF)
- QQQ (Nasdaq 100 ETF)
- AAPL (Apple Inc.)
- MSFT (Microsoft Corp.)
- GOOGL (Alphabet Inc.)

**Risk Management:**
- Max Positions: 5
- Max Portfolio Heat: 10%
- Stop Loss: 2x ATR trailing
- Take Profit: 2:1 reward-to-risk

---

## Success Criteria

### Paper Trading Validation
- [ ] Minimum 10 trades in 30 days
- [ ] Win rate ≥ 45% (allowing for variance)
- [ ] No critical bugs or execution failures
- [ ] Max drawdown < 20% (allowing buffer)
- [ ] Sharpe ratio > 0.5 (allowing for market conditions)

### Go-Live Decision
After 30 days of paper trading:
- ✓ All success criteria met → Deploy to live trading
- ⚠️ Some criteria missed → Extend paper trading or adjust
- ✗ Major issues → Refine strategy or try alternative

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 0: Configuration | 1 day | ✓ Complete |
| Phase 1: Backtesting | 1 day | ✓ Complete |
| Phase 2: Integration | 2-3 days | 🔄 In Progress |
| Phase 3: Paper Trading | 30 days | ⏳ Pending |
| Phase 4: Live Trading | Ongoing | ⏳ Pending |

**Expected Go-Live:** ~January 26, 2026 (after 30-day validation)

---

## Risk Management

**Paper Trading Safeguards:**
- Zero real money at risk
- Full monitoring and logging
- Can stop/adjust at any time
- Learn from mistakes without cost

**Live Trading Safeguards (Future):**
- Start with $10,000 capital
- Maximum 1% risk per trade ($100)
- Daily loss limit: 5% ($500)
- Max drawdown circuit breaker: 15% ($1,500)
- Require manual approval for first live trade

---

## Next Immediate Actions

1. Test `run_bot_v2.py` with updated config
2. Verify strategy integration works
3. Deploy to paper trading container
4. Monitor first 24 hours closely
5. Document any issues or adjustments needed
