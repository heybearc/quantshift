# Phase 1.5 Safety Testing Guide

**Version:** 1.0  
**Date:** March 4, 2026  
**Status:** Ready for Execution

---

## Overview

This document provides comprehensive test scenarios for all Phase 1.5 Critical Safety Features implemented in QuantShift. These tests must pass before proceeding to paper trading validation (Phase 1.5.9).

**Safety Features to Test:**
1. Emergency Kill Switch (Phase 1.5.1)
2. Bracket Orders (Phase 1.5.2)
3. Hard Position Limits (Phase 1.5.3)
4. Position Recovery on Startup (Phase 1.5.4)
5. Graceful Strategy Failure Handling (Phase 1.5.5)
6. Crypto Bot Trading (Phase 1.5.6)
7. Atomic Performance Tracking (Phase 1.5.7)

---

## Test Environment Setup

### Prerequisites
- Both bots deployed to STANDBY (BLUE or GREEN node)
- Paper trading accounts configured
- Database access
- Redis access
- Prometheus metrics accessible
- SSH access to deployment nodes

### Test Data Requirements
- Equity bot: Paper trading account with $100K
- Crypto bot: Paper trading account with $10K
- Clean database state (no existing positions)
- Redis accessible and empty

---

## Test Scenarios

### 1. Emergency Kill Switch Tests

#### Test 1.1: Emergency Stop via Redis Flag
**Objective:** Verify bot stops trading and closes all positions when emergency flag is set

**Steps:**
1. Start equity bot on STANDBY
2. Wait for bot to open at least 1 position
3. Set emergency stop flag:
   ```bash
   redis-cli SET bot:quantshift-equity:emergency_stop true
   ```
4. Monitor bot logs for emergency stop detection
5. Verify all positions are closed at market price
6. Verify bot stops trading (no new positions)

**Expected Results:**
- ✅ Bot detects flag within 100ms
- ✅ All positions closed immediately
- ✅ Bot status updated to EMERGENCY_STOPPED
- ✅ Prometheus metric `emergency_stops_total` incremented
- ✅ Logs show: `emergency_stop_flag_detected` and `emergency_stop_executed`

**Pass Criteria:** All positions closed within 5 seconds, bot stops trading

---

#### Test 1.2: Emergency Stop via Admin UI
**Objective:** Verify emergency stop button in admin UI triggers stop

**Steps:**
1. Start equity bot on STANDBY
2. Wait for bot to open at least 1 position
3. Open admin UI: https://admin.quantshift.io
4. Navigate to Bot Management
5. Click "Emergency Stop" button for equity bot
6. Confirm action
7. Monitor bot behavior

**Expected Results:**
- ✅ Redis flag set to true
- ✅ All positions closed within 5 seconds
- ✅ Bot stops trading
- ✅ UI shows bot status as "Emergency Stopped"

**Pass Criteria:** Same as Test 1.1

---

#### Test 1.3: Emergency Stop Recovery
**Objective:** Verify bot can resume trading after emergency stop is cleared

**Steps:**
1. After Test 1.1 or 1.2, clear emergency flag:
   ```bash
   redis-cli DEL bot:quantshift-equity:emergency_stop
   ```
2. Restart bot
3. Wait for bot to resume normal operation
4. Verify bot can open new positions

**Expected Results:**
- ✅ Bot starts normally
- ✅ Bot can generate signals
- ✅ Bot can execute trades
- ✅ No emergency stop flag detected

**Pass Criteria:** Bot resumes normal trading within 1 cycle

---

### 2. Bracket Order Tests

#### Test 2.1: Bracket Order Execution (Equity)
**Objective:** Verify bracket orders are created atomically with stop-loss and take-profit

**Steps:**
1. Start equity bot on STANDBY
2. Wait for BUY signal with stop-loss and take-profit
3. Monitor order execution
4. Check Alpaca dashboard for orders
5. Verify 3 orders created: entry, stop-loss, take-profit

**Expected Results:**
- ✅ Single API call creates all 3 orders (OrderClass.BRACKET)
- ✅ Entry order filled
- ✅ Stop-loss order active (stop price set)
- ✅ Take-profit order active (limit price set)
- ✅ Logs show: `bracket_order_submitted` with R:R ratio

**Pass Criteria:** All 3 orders exist on broker, position protected immediately

---

#### Test 2.2: Bracket Order Execution (Crypto)
**Objective:** Verify crypto bot uses bracket pattern for protection

**Steps:**
1. Start crypto bot on STANDBY
2. Wait for BUY signal
3. Monitor order execution
4. Check Coinbase dashboard for orders
5. Verify entry + stop-loss + take-profit orders

**Expected Results:**
- ✅ Entry order filled
- ✅ Stop-loss order placed immediately after entry
- ✅ Take-profit order placed immediately after entry
- ✅ Logs show: `stop_loss_placed` and `take_profit_placed`

**Pass Criteria:** Position protected within 2 seconds of entry

---

#### Test 2.3: Bracket Order Protection During Bot Crash
**Objective:** Verify position is protected even if bot crashes after order submission

**Steps:**
1. Start equity bot on STANDBY
2. Wait for bracket order to be submitted
3. Immediately kill bot process:
   ```bash
   pm2 stop quantshift-equity
   ```
4. Check Alpaca dashboard
5. Verify stop-loss and take-profit orders still active

**Expected Results:**
- ✅ Stop-loss order exists on broker
- ✅ Take-profit order exists on broker
- ✅ Position is protected by broker-enforced orders
- ✅ No manual intervention needed

**Pass Criteria:** Orders remain active on broker after bot crash

---

### 3. Hard Position Limit Tests

#### Test 3.1: Max Position Size Limit
**Objective:** Verify bot rejects trades exceeding 10% of portfolio

**Steps:**
1. Modify strategy to generate large position size (>10% of portfolio)
2. Start equity bot
3. Wait for BUY signal
4. Monitor logs for rejection

**Expected Results:**
- ✅ Trade rejected before submission
- ✅ Log shows: `position_limit_violation` with `limit_type=max_position_pct`
- ✅ Prometheus metric `position_rejections_total{reason="max_position_pct"}` incremented
- ✅ No order submitted to broker

**Pass Criteria:** Trade rejected, no order placed

---

#### Test 3.2: Max Positions Limit
**Objective:** Verify bot rejects 6th position

**Steps:**
1. Start equity bot
2. Wait for bot to open 5 positions
3. Wait for 6th BUY signal
4. Monitor logs for rejection

**Expected Results:**
- ✅ 6th trade rejected
- ✅ Log shows: `position_limit_violation` with `limit_type=max_positions`
- ✅ Only 5 positions exist
- ✅ Prometheus metric incremented

**Pass Criteria:** Bot maintains exactly 5 positions, rejects 6th

---

#### Test 3.3: Daily Loss Circuit Breaker
**Objective:** Verify bot stops trading after 3% daily loss

**Steps:**
1. Start equity bot
2. Simulate losing trades (or wait for natural losses)
3. Monitor daily P&L
4. When daily loss reaches 3%, verify bot stops trading

**Expected Results:**
- ✅ Bot stops generating BUY signals
- ✅ Log shows: `circuit_breaker_triggered` with `reason=daily_loss_limit`
- ✅ Existing positions remain open
- ✅ No new positions opened

**Pass Criteria:** Bot stops trading at 3% daily loss

---

#### Test 3.4: Total Risk Limit
**Objective:** Verify bot rejects trades exceeding 15% total portfolio risk

**Steps:**
1. Start equity bot
2. Open multiple positions with wide stop-losses
3. Calculate total risk (sum of stop-loss distances)
4. When total risk approaches 15%, attempt new trade
5. Verify rejection

**Expected Results:**
- ✅ Trade rejected when total risk > 15%
- ✅ Log shows: `position_limit_violation` with `limit_type=max_total_risk`
- ✅ Prometheus metric incremented

**Pass Criteria:** Trade rejected, total risk stays under 15%

---

### 4. Position Recovery Tests

#### Test 4.1: Orphaned Position Recovery (Equity)
**Objective:** Verify bot adds positions that exist in broker but not in database

**Steps:**
1. Manually create position in Alpaca (outside bot)
2. Start equity bot
3. Monitor logs for position recovery
4. Check database for new position

**Expected Results:**
- ✅ Log shows: `position_recovery_complete` with `orphaned_added=1`
- ✅ Position added to database with `strategy_name=RECOVERED`
- ✅ Database matches broker reality

**Pass Criteria:** Orphaned position added to database on startup

---

#### Test 4.2: Ghost Position Recovery (Equity)
**Objective:** Verify bot removes positions that exist in database but not in broker

**Steps:**
1. Manually insert position into database
2. Ensure position doesn't exist in Alpaca
3. Start equity bot
4. Monitor logs for position recovery
5. Check database - position should be removed

**Expected Results:**
- ✅ Log shows: `position_recovery_complete` with `ghosts_removed=1`
- ✅ Position removed from database
- ✅ Database matches broker reality

**Pass Criteria:** Ghost position removed from database on startup

---

#### Test 4.3: Position Recovery (Crypto)
**Objective:** Verify crypto bot recovers positions from Coinbase accounts

**Steps:**
1. Manually buy crypto in Coinbase (outside bot)
2. Start crypto bot
3. Monitor logs for position recovery
4. Check database for new position

**Expected Results:**
- ✅ Log shows: `position_recovery_complete` with `orphaned_added=1`
- ✅ Crypto holding added to database
- ✅ Current price fetched from Coinbase

**Pass Criteria:** Crypto holdings synced to database on startup

---

#### Test 4.4: Clean Recovery (No Discrepancies)
**Objective:** Verify bot handles case where database already matches broker

**Steps:**
1. Ensure database and broker are in sync
2. Start bot
3. Monitor logs

**Expected Results:**
- ✅ Log shows: `Position recovery: Database matches broker (no discrepancies)`
- ✅ No positions added or removed
- ✅ `orphaned_added=0` and `ghosts_removed=0`

**Pass Criteria:** No changes made, clean recovery

---

### 5. Strategy Failure Handling Tests

#### Test 5.1: Single Strategy Failure
**Objective:** Verify one strategy failure doesn't crash bot

**Steps:**
1. Inject error into one strategy (e.g., BollingerBounce)
2. Start equity bot with 3 strategies
3. Monitor logs
4. Verify other strategies continue running

**Expected Results:**
- ✅ Failed strategy logs error
- ✅ Prometheus metric `strategy_failures_total{strategy="BollingerBounce"}` incremented
- ✅ Other strategies (RSI, Breakout) continue generating signals
- ✅ Bot continues trading

**Pass Criteria:** Bot continues running, other strategies unaffected

---

#### Test 5.2: Strategy Disable After 3 Failures
**Objective:** Verify strategy is disabled after 3 consecutive failures

**Steps:**
1. Inject persistent error into one strategy
2. Start equity bot
3. Wait for 3 cycles
4. Monitor logs for strategy disable

**Expected Results:**
- ✅ After 3 failures, log shows: `strategy_disabled` with `consecutive_failures=3`
- ✅ Strategy skipped in subsequent cycles
- ✅ Prometheus metric `strategies_disabled=1`
- ✅ Other strategies continue running

**Pass Criteria:** Strategy disabled after 3 failures, bot continues

---

#### Test 5.3: Strategy Recovery
**Objective:** Verify strategy recovers when error is fixed

**Steps:**
1. After Test 5.1, fix the injected error
2. Wait for next cycle
3. Monitor logs for recovery

**Expected Results:**
- ✅ Log shows: `strategy_recovered` with `previous_failures=1`
- ✅ Failure counter reset to 0
- ✅ Strategy generates signals normally

**Pass Criteria:** Strategy recovers and resumes normal operation

---

### 6. Crypto Bot Trading Tests

#### Test 6.1: Crypto Bot Signal Generation
**Objective:** Verify crypto bot generates trading signals

**Steps:**
1. Start crypto bot on STANDBY
2. Monitor logs for signal generation
3. Wait for at least 1 BUY signal

**Expected Results:**
- ✅ Log shows: `execute_signal_called` with `signal_type=BUY`
- ✅ Symbol is crypto pair (e.g., BTC-USD)
- ✅ Position size calculated
- ✅ Price available

**Pass Criteria:** At least 1 signal generated within 30 minutes

---

#### Test 6.2: Crypto Bot Position Execution
**Objective:** Verify crypto bot can execute trades

**Steps:**
1. Start crypto bot on STANDBY
2. Wait for BUY signal
3. Monitor order execution
4. Check Coinbase dashboard

**Expected Results:**
- ✅ Order submitted to Coinbase
- ✅ Order filled
- ✅ Position appears in database
- ✅ Position appears in Coinbase account

**Pass Criteria:** At least 1 position opened within 1 hour

---

#### Test 6.3: Crypto Bot Account Fetching
**Objective:** Verify crypto bot can fetch account balance

**Steps:**
1. Start crypto bot
2. Monitor logs for account fetch
3. Verify simulated capital used

**Expected Results:**
- ✅ Log shows: `using_simulated_capital` with `capital=10000`
- ✅ Account equity = $10,000
- ✅ Buying power = $10,000

**Pass Criteria:** Account balance fetched successfully

---

### 7. Atomic Transaction Tests

#### Test 7.1: Transaction Commit on Success
**Objective:** Verify position updates commit successfully

**Steps:**
1. Start equity bot
2. Wait for position update
3. Check database directly:
   ```sql
   SELECT * FROM positions WHERE bot_name = 'quantshift-equity';
   ```
4. Verify data is committed

**Expected Results:**
- ✅ Position exists in database
- ✅ All fields populated correctly
- ✅ `updated_at` timestamp recent

**Pass Criteria:** Position data persisted to database

---

#### Test 7.2: Transaction Rollback on Error
**Objective:** Verify position updates rollback on error

**Steps:**
1. Inject database error during position update
2. Attempt position update
3. Check database for partial updates

**Expected Results:**
- ✅ Log shows: `transaction_rolled_back`
- ✅ No partial data in database
- ✅ Database state unchanged
- ✅ No data corruption

**Pass Criteria:** No partial updates, clean rollback

---

#### Test 7.3: Row Locking (FOR UPDATE)
**Objective:** Verify concurrent updates are serialized

**Steps:**
1. Start two instances of equity bot (simulate race condition)
2. Both attempt to update same position simultaneously
3. Monitor database locks
4. Verify one waits for the other

**Expected Results:**
- ✅ First transaction acquires lock
- ✅ Second transaction waits
- ✅ Both updates succeed sequentially
- ✅ No lost updates

**Pass Criteria:** No race conditions, updates serialized correctly

---

#### Test 7.4: Bulk Position Sync
**Objective:** Verify `sync_positions_atomic()` works correctly

**Steps:**
1. Create test positions in broker
2. Call `sync_positions_atomic()` with position list
3. Check database
4. Verify stats returned

**Expected Results:**
- ✅ All positions synced in single transaction
- ✅ Stats show: `inserted`, `updated`, `deleted` counts
- ✅ Database matches input list
- ✅ Log shows: `positions_synced_atomic`

**Pass Criteria:** All positions synced atomically, stats accurate

---

## Test Execution Checklist

### Pre-Test Setup
- [ ] Both bots deployed to STANDBY
- [ ] Paper trading accounts funded
- [ ] Database clean (no test data)
- [ ] Redis accessible
- [ ] Prometheus metrics accessible
- [ ] Admin UI accessible
- [ ] SSH access confirmed

### Emergency Kill Switch (1.5.1)
- [ ] Test 1.1: Emergency stop via Redis flag
- [ ] Test 1.2: Emergency stop via Admin UI
- [ ] Test 1.3: Emergency stop recovery

### Bracket Orders (1.5.2)
- [ ] Test 2.1: Bracket order execution (equity)
- [ ] Test 2.2: Bracket order execution (crypto)
- [ ] Test 2.3: Bracket order protection during crash

### Hard Position Limits (1.5.3)
- [ ] Test 3.1: Max position size limit
- [ ] Test 3.2: Max positions limit
- [ ] Test 3.3: Daily loss circuit breaker
- [ ] Test 3.4: Total risk limit

### Position Recovery (1.5.4)
- [ ] Test 4.1: Orphaned position recovery (equity)
- [ ] Test 4.2: Ghost position recovery (equity)
- [ ] Test 4.3: Position recovery (crypto)
- [ ] Test 4.4: Clean recovery (no discrepancies)

### Strategy Failure Handling (1.5.5)
- [ ] Test 5.1: Single strategy failure
- [ ] Test 5.2: Strategy disable after 3 failures
- [ ] Test 5.3: Strategy recovery

### Crypto Bot Trading (1.5.6)
- [ ] Test 6.1: Crypto bot signal generation
- [ ] Test 6.2: Crypto bot position execution
- [ ] Test 6.3: Crypto bot account fetching

### Atomic Transactions (1.5.7)
- [ ] Test 7.1: Transaction commit on success
- [ ] Test 7.2: Transaction rollback on error
- [ ] Test 7.3: Row locking (FOR UPDATE)
- [ ] Test 7.4: Bulk position sync

---

## Success Criteria

**Phase 1.5.8 passes if:**
- ✅ All emergency stop tests pass (3/3)
- ✅ All bracket order tests pass (3/3)
- ✅ All position limit tests pass (4/4)
- ✅ All position recovery tests pass (4/4)
- ✅ All strategy failure tests pass (3/3)
- ✅ All crypto bot tests pass (3/3)
- ✅ All atomic transaction tests pass (4/4)

**Total: 24 tests must pass**

---

## Failure Handling

If any test fails:
1. Document the failure in detail
2. Fix the root cause
3. Re-run the failed test
4. Re-run all related tests
5. Only proceed to Phase 1.5.9 after all tests pass

---

## Test Results Log

Create a test results file: `TEST-RESULTS-PHASE-1.5.md`

Format:
```markdown
# Phase 1.5 Safety Testing Results

**Date:** YYYY-MM-DD  
**Tester:** [Name]  
**Environment:** STANDBY (BLUE/GREEN)

## Test Results

### Emergency Kill Switch
- [ ] Test 1.1: PASS/FAIL - [Notes]
- [ ] Test 1.2: PASS/FAIL - [Notes]
- [ ] Test 1.3: PASS/FAIL - [Notes]

[Continue for all tests...]

## Summary
- Total Tests: 24
- Passed: X
- Failed: Y
- Pass Rate: Z%

## Issues Found
1. [Issue description]
2. [Issue description]

## Recommendations
1. [Recommendation]
2. [Recommendation]
```

---

## Next Steps After Testing

Once all tests pass:
1. Document test results
2. Update IMPLEMENTATION-PLAN.md to mark Phase 1.5.8 complete
3. Proceed to Phase 1.5.9: Paper Trading Validation (2-4 weeks)
4. Monitor bots daily during paper trading
5. Only proceed to live trading after 4 consecutive weeks of success
