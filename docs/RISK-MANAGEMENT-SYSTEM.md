# QuantShift Risk Management System

**Last Updated:** 2026-02-26  
**Status:** Active - Enhanced with Position Recovery Validation

---

## Overview

QuantShift implements a multi-layered risk management system to protect capital and ensure sustainable trading operations. This document outlines all risk controls, their configuration, and how they work together.

---

## Current Risk Incident: Over-Leverage Detection

### Incident Summary (2026-02-26)

**Discovered:** Dashboard showing $157k position value with only $100k account equity (1.57x leverage)

**Root Cause:**
- Alpaca paper trading account has 2x margin enabled ($200k buying power)
- Bot recovered existing positions from Redis on restart
- No risk validation performed during position recovery
- Positions accumulated over multiple trading sessions

**Impact:**
- Paper trading only (no real money at risk)
- 57% over-leveraged vs cash account standards
- Risk management limits not enforced on recovery

**Resolution:**
- ✅ Added position recovery risk validation (commit 386c99a)
- ✅ Bot now logs leverage ratio on startup
- ✅ Warns if over-leveraged (>1.0x)
- ⏳ Positions will naturally reduce through stop-losses and exits

---

## Risk Management Layers

### 1. Position Recovery Validation (NEW)

**Purpose:** Prevent over-leverage when bot restarts with existing positions

**Implementation:** `apps/bots/run_bot_v3.py::_recover_positions()`

**Checks:**
```python
leverage_ratio = total_position_value / account_equity
max_leverage = 1.0  # Cash account standard

if leverage_ratio > max_leverage:
    logger.warning("position_recovery_over_leveraged")
    # Positions recovered but new trading restricted
```

**Metrics Logged:**
- Total position value
- Account equity
- Leverage ratio
- Individual position values

**Action on Over-Leverage:**
- Positions are recovered (maintains existing trades)
- Warning logged for monitoring
- Orchestrator should restrict new position opens
- Natural position closes will reduce leverage

---

### 2. Portfolio-Level Risk Controls

**Configuration:** `config/equity_config.yaml` and `config/crypto_config.yaml`

```yaml
risk_management:
  max_portfolio_heat: 0.10      # 10% max total risk
  max_position_correlation: 0.7  # Max correlation between positions
  max_sector_exposure: 0.30      # 30% max in any sector
  daily_loss_limit: 0.05         # 5% daily loss limit
  max_drawdown_limit: 0.15       # 15% max drawdown
```

**Enforcement:**
- Checked before opening new positions
- Aggregates risk across all open positions
- Prevents concentration risk

**Status:** ⚠️ **Not enforced on position recovery** (enhancement needed)

---

### 3. Position-Level Risk Controls

**Per-Position Limits:**
- Stop-loss orders on all positions
- Take-profit targets
- Position size limits (via strategy)
- Maximum holding period

**Strategy-Specific:**
- **Bollinger Bounce:** 2% stop-loss, 4% take-profit
- **RSI Mean Reversion:** 2.5% stop-loss, 5% take-profit
- **Breakout Momentum:** 3% stop-loss, trailing stop

---

### 4. Market Regime-Based Risk Adjustment

**Regime Detection:** 5 market states
- Bull Market (1.0x risk multiplier)
- Bear Market (0.5x risk multiplier)
- High Volatility (0.6x risk multiplier)
- Low Volatility (0.8x risk multiplier)
- Crisis (0.25x risk multiplier)

**Dynamic Adjustment:**
- Position sizes scaled by regime multiplier
- More conservative in volatile/crisis markets
- More aggressive in stable bull markets

---

### 5. Circuit Breakers

**Automatic Trading Halt Triggers:**
1. **Daily Loss Limit:** Trading stops if down 5% in one day
2. **Max Drawdown:** Trading stops if down 15% from peak
3. **Rapid Loss:** Trading stops if down 3% in 15 minutes
4. **API Failures:** Trading paused on repeated API errors

**Recovery:**
- Manual review required
- Bot restart with risk validation
- Gradual position re-entry

---

## Known Issues & Gaps

### 1. ⚠️ Position Recovery Risk Validation (FIXED)
- **Issue:** No leverage check when recovering positions
- **Status:** ✅ Fixed in commit 386c99a
- **Next:** Add orchestrator check to prevent new positions when over-leveraged

### 2. ⚠️ Margin Account vs Cash Account
- **Issue:** Paper trading has 2x margin, production should be cash-only
- **Impact:** Can accumulate positions beyond account equity
- **Recommendation:** 
  - Verify production account is cash-only (no margin)
  - Add explicit margin check in bot initialization
  - Enforce 1.0x max leverage in all environments

### 3. ⚠️ Risk Limits Not Enforced on Recovery
- **Issue:** Portfolio heat, sector exposure not checked on startup
- **Impact:** Can start trading with existing positions that violate limits
- **Recommendation:** Add full risk validation in `_recover_positions()`

### 4. ⚠️ No Position Size Limits
- **Issue:** No hard cap on individual position size as % of account
- **Impact:** Single position could be 20%+ of account
- **Recommendation:** Add `max_position_size: 0.10` (10% max per position)

---

## Risk Monitoring

### Real-Time Metrics (Prometheus)

**Bot Metrics (Port 9200 - Equity, 9201 - Crypto):**
```
quantshift_equity_account_equity
quantshift_equity_position_count
quantshift_equity_unrealized_pl
quantshift_equity_daily_pnl
```

**Leverage Monitoring:**
```
# Calculate leverage ratio
sum(quantshift_equity_position_value) / quantshift_equity_account_equity
```

**Alert Thresholds:**
- Leverage > 1.0x (cash account)
- Leverage > 1.5x (margin account)
- Daily loss > 3%
- Drawdown > 10%

### Log Monitoring

**Key Log Events:**
```bash
# Check for over-leverage warnings
ssh root@10.92.3.27 'grep "position_recovery_over_leveraged" /opt/quantshift/logs/equity-bot.log'

# Check risk validation
ssh root@10.92.3.27 'grep "position_recovery_risk_validated" /opt/quantshift/logs/equity-bot.log'

# Check circuit breaker triggers
ssh root@10.92.3.27 'grep "circuit_breaker\|trading_halted" /opt/quantshift/logs/equity-bot.log'
```

---

## Recommendations

### Immediate (This Week)
1. ✅ Add position recovery validation - **DONE**
2. ⏳ Monitor leverage ratio in Grafana
3. ⏳ Add orchestrator check to prevent new positions when over-leveraged
4. ⏳ Document expected leverage for paper vs production

### Short-Term (This Month)
1. Add full risk validation on position recovery (portfolio heat, sector exposure)
2. Implement max position size limit (10% of account)
3. Add leverage ratio to dashboard
4. Create risk management alerts in Grafana

### Long-Term (3-6 Months)
1. Implement portfolio optimization (Kelly Criterion)
2. Add correlation-based position sizing
3. Dynamic risk limits based on market conditions
4. Risk-adjusted performance metrics (Sharpe, Sortino)

---

## Configuration Reference

### Equity Bot Risk Config
**File:** `/opt/quantshift/config/equity_config.yaml`

```yaml
risk_management:
  max_portfolio_heat: 0.10
  max_position_correlation: 0.7
  max_sector_exposure: 0.30
  daily_loss_limit: 0.05
  max_drawdown_limit: 0.15
```

### Crypto Bot Risk Config
**File:** `/opt/quantshift/config/crypto_config.yaml`

```yaml
risk_management:
  max_portfolio_heat: 0.08  # More conservative for crypto
  max_position_correlation: 0.6
  max_sector_exposure: 0.40  # Crypto has fewer "sectors"
  daily_loss_limit: 0.06     # Higher volatility tolerance
  max_drawdown_limit: 0.20
```

---

## Testing Risk Controls

### Manual Testing

**1. Test Over-Leverage Detection:**
```bash
# Restart bot and check logs
ssh root@10.92.3.27 'systemctl restart quantshift-equity'
ssh root@10.92.3.27 'journalctl -u quantshift-equity -n 50 | grep leverage'
```

**2. Test Daily Loss Limit:**
```python
# Simulate large loss in paper trading
# Verify bot halts trading
```

**3. Test Circuit Breakers:**
```python
# Trigger rapid loss scenario
# Verify trading paused
```

### Automated Testing

**Unit Tests:** `tests/test_risk_management.py`
- Test leverage calculation
- Test position recovery validation
- Test circuit breaker triggers

**Integration Tests:** `tests/test_bot_integration.py`
- Test full risk validation flow
- Test position recovery with over-leverage
- Test trading halt and resume

---

## Support

**Questions or Issues:**
1. Check bot logs: `/opt/quantshift/logs/`
2. Review Grafana dashboards: `http://grafana.quantshift.io`
3. Check Prometheus metrics: `http://10.92.3.27:9200/metrics`
4. Review this documentation

**Emergency Contacts:**
- Bot halted unexpectedly: Check circuit breakers
- Over-leveraged: Review position recovery logs
- Risk limits violated: Check orchestrator logic

---

## Changelog

**2026-02-26:**
- Added position recovery risk validation
- Documented over-leverage incident
- Created comprehensive risk management documentation

**2026-01-26:**
- Initial risk management implementation
- Portfolio heat, sector exposure, daily loss limits
- Market regime-based risk adjustment
