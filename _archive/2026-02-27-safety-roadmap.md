# QuantShift Safety-Focused Roadmap
**Capital Protection First - Balanced Trading Second**

**Last Updated:** 2026-02-27  
**Portfolio:** $2600 initial ($1300 equity, $1300 crypto)  
**Risk Tolerance:** LOW - Cannot afford to lose capital due to app failures  
**Timeline:** 4-6 weeks to safe live trading

---

## 🎯 Mission: Build Bulletproof Trading System

**Core Principle:** Never lose money due to software failures. Only lose money due to market conditions within defined risk limits.

**Approach:** Safety features first, then gradual capital deployment, then advanced features.

---

## 📊 Current State Assessment

### ✅ What We Have (GOOD)
- **4 Strategies Implemented:**
  1. BollingerBounce (33% allocation) - 58.6% WR
  2. RSIMeanReversion (33% allocation) - 57.5% WR
  3. BreakoutMomentum (34% allocation) - Active
  4. MACrossover - Available but inactive
  
- **2 Bots Running:**
  - Equity bot (CT 100/101): 100 symbols, 3 strategies active
  - Crypto bot (CT 100/101): 50 symbols, 3 strategies active
  
- **Infrastructure:**
  - Primary/Standby failover (CT 100 primary, CT 101 standby)
  - Redis state management with replication
  - PostgreSQL database for positions/performance
  - Prometheus metrics + Grafana dashboards
  - Web app with blue-green deployment

- **Risk Management (PARTIAL):**
  - RiskManager class active (10% max portfolio heat)
  - Circuit breakers (5% daily loss, 15% max drawdown)
  - Correlation limits (0.7 max)
  - Sector exposure limits (30% max)
  - ML regime detection (91.7% accuracy)

- **Broker-Side Protection (IMPLEMENTED):**
  - Stop-loss orders placed after entry (AlpacaExecutor)
  - Take-profit orders placed after entry (AlpacaExecutor)
  - Orders live on broker servers (survive bot crashes)
  - Coinbase executor has stop-loss/take-profit methods

### ❌ Critical Gaps (MUST FIX)

1. **No Emergency Kill Switch**
   - Can't remotely stop bot if something goes wrong
   - No manual override capability

2. **No Hard Position Limits in Code**
   - Limits in config can be accidentally changed
   - No enforcement at code level

3. **No Position Recovery on Startup**
   - Bot doesn't sync with broker on restart
   - Risk of "ghost positions" (in DB but not broker)
   - Risk of "orphaned positions" (in broker but not DB)

4. **Race Conditions in Performance Tracking**
   - Position close detection not atomic
   - Could double-count P&L if bot crashes mid-update

5. **No Graceful Strategy Failure Handling**
   - One bad strategy crashes entire bot
   - No circuit breaker per strategy

6. **Crypto Bot Not Trading**
   - Running but no positions opened since deployment
   - Need to investigate why (likely signal generation issue)

7. **Stop-Loss Orders Not Bracket Orders**
   - Currently: Place entry, wait for fill, then place SL/TP separately
   - Risk: Bot crashes between entry and SL placement → unprotected position
   - Should use: Bracket orders (entry + SL + TP in single atomic operation)

---

## 🚨 PHASE 0: Critical Safety Features (Week 1) - MUST DO BEFORE LIVE

**Goal:** Make system safe enough to risk real money

**Timeline:** 5-7 days  
**Effort:** ~24 hours total

### 0.1 Emergency Kill Switch (2 hours) - HIGHEST PRIORITY
**Why:** You need ability to stop bot instantly if something goes wrong

**Implementation:**
```python
# Add to run_bot_v3.py main loop
def check_emergency_stop(self):
    """Check Redis for emergency stop flag."""
    try:
        stop_flag = self.state_manager.redis_client.get(
            f"bot:{self.bot_name}:emergency_stop"
        )
        if stop_flag == "true":
            logger.critical("EMERGENCY_STOP_TRIGGERED")
            self.close_all_positions_emergency()
            self.running = False
            return True
    except Exception as e:
        logger.error("emergency_stop_check_failed", error=str(e))
    return False

def close_all_positions_emergency(self):
    """Close all positions immediately at market price."""
    positions = self.executor.get_positions()
    for pos in positions:
        try:
            self.executor.close_position(pos.symbol, pos.quantity)
            logger.critical("emergency_position_closed", symbol=pos.symbol)
        except Exception as e:
            logger.error("emergency_close_failed", symbol=pos.symbol, error=str(e))
```

**Trigger:**
```bash
# From anywhere with Redis access
redis-cli SET bot:quantshift-equity:emergency_stop true
redis-cli SET bot:quantshift-crypto:emergency_stop true
```

**Testing:**
- Set flag while bot has open positions
- Verify all positions close within 30 seconds
- Verify bot stops trading

### 0.2 Hard Position Limits (2 hours) - HIGHEST PRIORITY
**Why:** Prevent catastrophic losses from bugs or bad strategies

**Implementation:**
```python
# Add to packages/core/src/quantshift_core/position_limits.py
class PositionLimits:
    """Hard-coded position limits that cannot be changed via config."""
    
    # ABSOLUTE MAXIMUMS - DO NOT CHANGE WITHOUT EXTREME CAUTION
    MAX_POSITION_PCT = 0.10  # 10% max per position (was 5%, relaxed for $2600 portfolio)
    MAX_POSITIONS = 5        # Max 5 positions total
    MAX_DAILY_LOSS_PCT = 0.03  # Stop trading if down 3% in a day
    MAX_TOTAL_RISK_PCT = 0.15  # Max 15% total portfolio at risk
    MIN_POSITION_VALUE = 100   # Minimum $100 per position (avoid tiny positions)
    
    @staticmethod
    def validate_position(symbol, quantity, price, account):
        """Validate position against hard limits. Returns (valid, reason)."""
        position_value = quantity * price
        portfolio_value = account.equity
        
        # Check position size
        position_pct = position_value / portfolio_value
        if position_pct > PositionLimits.MAX_POSITION_PCT:
            return False, f"Position {position_pct:.1%} exceeds max {PositionLimits.MAX_POSITION_PCT:.1%}"
        
        # Check minimum position size
        if position_value < PositionLimits.MIN_POSITION_VALUE:
            return False, f"Position ${position_value:.0f} below minimum ${PositionLimits.MIN_POSITION_VALUE}"
        
        # Check total positions
        if len(account.positions) >= PositionLimits.MAX_POSITIONS:
            return False, f"Already at max {PositionLimits.MAX_POSITIONS} positions"
        
        # Check daily loss
        daily_loss_pct = abs(account.daily_pnl / portfolio_value) if account.daily_pnl < 0 else 0
        if daily_loss_pct > PositionLimits.MAX_DAILY_LOSS_PCT:
            return False, f"Daily loss {daily_loss_pct:.1%} exceeds limit {PositionLimits.MAX_DAILY_LOSS_PCT:.1%}"
        
        return True, "OK"
```

**Integration:**
- Add validation to `AlpacaExecutor.execute_signal()`
- Add validation to `CoinbaseExecutor.execute_signal()`
- Log all rejections with reason
- Add Prometheus metric: `quantshift_position_rejections_total{reason="max_positions"}`

**Testing:**
- Try to open 6th position → should reject
- Try to open position >10% of portfolio → should reject
- Simulate 3% daily loss → should stop trading

### 0.3 Bracket Orders (4 hours) - HIGHEST PRIORITY
**Why:** Protect positions even if bot crashes immediately after entry

**Current Risk:**
```python
# DANGEROUS: 3 separate operations
order = submit_order(BUY)  # 1. Entry
wait_for_fill()            # 2. Wait
submit_order(STOP_LOSS)    # 3. Stop loss (bot could crash here!)
submit_order(TAKE_PROFIT)  # 4. Take profit
```

**Safe Implementation:**
```python
# SAFE: Single atomic bracket order
from alpaca.trading.enums import OrderClass
from alpaca.trading.requests import TakeProfitRequest, StopLossRequest

def execute_signal_with_bracket(self, signal: Signal):
    """Execute signal with bracket order (entry + SL + TP in one operation)."""
    
    # Calculate stop-loss and take-profit prices
    entry_price = signal.price
    stop_loss_price = signal.stop_loss or (entry_price * 0.97)  # 3% default
    take_profit_price = signal.take_profit or (entry_price * 1.05)  # 5% default
    
    # Place bracket order (atomic operation)
    order = self.alpaca_client.submit_order(
        MarketOrderRequest(
            symbol=signal.symbol,
            qty=signal.position_size,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            order_class=OrderClass.BRACKET,  # ← KEY: Bracket order
            take_profit=TakeProfitRequest(
                limit_price=round(take_profit_price, 2)
            ),
            stop_loss=StopLossRequest(
                stop_price=round(stop_loss_price, 2)
            )
        )
    )
    
    logger.info(
        "bracket_order_placed",
        symbol=signal.symbol,
        entry=entry_price,
        stop_loss=stop_loss_price,
        take_profit=take_profit_price,
        max_loss_pct=(entry_price - stop_loss_price) / entry_price * 100,
        max_gain_pct=(take_profit_price - entry_price) / entry_price * 100
    )
    
    return order
```

**Benefits:**
- ✅ If bot crashes after order submission → position still protected
- ✅ If bot offline for days → Alpaca manages exits
- ✅ Maximum loss per trade: 3% (enforced by broker)
- ✅ No orphaned positions without stops

**Testing:**
- Place bracket order in paper trading
- Kill bot immediately after order submission
- Verify stop-loss and take-profit orders exist on Alpaca
- Verify orders trigger correctly

### 0.4 Position Recovery on Startup (3 hours) - HIGH PRIORITY
**Why:** Ensure database always matches broker reality

**Implementation:**
```python
def recover_positions_on_startup(self):
    """Sync positions from broker to database on startup."""
    logger.info("position_recovery_starting")
    
    # Get actual positions from broker
    broker_positions = self.executor.get_positions()
    broker_symbols = {p.symbol for p in broker_positions}
    
    # Get positions from database
    cursor = self.db_conn.cursor()
    cursor.execute("SELECT symbol FROM positions WHERE bot_name = %s", (self.bot_name,))
    db_symbols = {row[0] for row in cursor.fetchall()}
    
    # Find discrepancies
    orphaned = broker_symbols - db_symbols  # In broker but not DB
    ghost = db_symbols - broker_symbols      # In DB but not broker
    
    if orphaned:
        logger.warning("orphaned_positions_found", symbols=list(orphaned), count=len(orphaned))
        # Add to database
        for pos in broker_positions:
            if pos.symbol in orphaned:
                self._sync_position_to_db(pos, strategy="RECOVERED")
    
    if ghost:
        logger.warning("ghost_positions_found", symbols=list(ghost), count=len(ghost))
        # Remove from database
        cursor.execute(
            "DELETE FROM positions WHERE bot_name = %s AND symbol = ANY(%s)",
            (self.bot_name, list(ghost))
        )
        self.db_conn.commit()
    
    logger.info(
        "position_recovery_complete",
        broker_positions=len(broker_symbols),
        db_positions=len(db_symbols),
        orphaned=len(orphaned),
        ghost=len(ghost)
    )
```

**Testing:**
- Manually add position to database (not in broker) → should remove
- Manually open position in broker (not in DB) → should add
- Verify logs show discrepancies

### 0.5 Graceful Strategy Failure Handling (3 hours) - HIGH PRIORITY
**Why:** One bad strategy shouldn't crash entire bot

**Implementation:**
```python
class StrategyOrchestrator:
    def __init__(self):
        self.strategy_failures = defaultdict(int)
        self.disabled_strategies = set()
        self.failure_threshold = 3  # Disable after 3 consecutive failures
    
    def execute_strategy_safe(self, strategy, market_data):
        """Execute strategy with failure isolation."""
        if strategy.name in self.disabled_strategies:
            logger.debug("strategy_disabled_skipping", strategy=strategy.name)
            return []
        
        try:
            signals = strategy.generate_signals(market_data)
            
            # Reset failure counter on success
            if self.strategy_failures[strategy.name] > 0:
                logger.info("strategy_recovered", strategy=strategy.name)
                self.strategy_failures[strategy.name] = 0
            
            return signals
            
        except Exception as e:
            logger.error(
                "strategy_failed",
                strategy=strategy.name,
                error=str(e),
                exc_info=True
            )
            
            # Increment failure counter
            self.strategy_failures[strategy.name] += 1
            
            # Disable if too many failures
            if self.strategy_failures[strategy.name] >= self.failure_threshold:
                logger.critical(
                    "strategy_disabled",
                    strategy=strategy.name,
                    failures=self.strategy_failures[strategy.name],
                    reason="too_many_consecutive_failures"
                )
                self.disabled_strategies.add(strategy.name)
                
                # Send alert (future: email/Slack)
                self.metrics.inc_strategy_disabled(strategy.name)
            
            return []  # Return empty signals, don't crash
```

**Testing:**
- Inject exception in one strategy → verify others continue
- Trigger 3 failures → verify strategy disabled
- Verify metrics updated

### 0.6 Fix Crypto Bot (4 hours) - HIGH PRIORITY
**Why:** Crypto bot running but not trading - need to diagnose

**Investigation Steps:**
1. Check if signals being generated
2. Check if signals being filtered out by risk manager
3. Check if Coinbase API calls failing
4. Check if position size calculations failing
5. Review logs for errors

**Likely Issues:**
- Coinbase API authentication
- Symbol format mismatch (BTC-USD vs BTCUSD)
- Minimum position size too high for $10K paper account
- Risk limits too conservative

**Fix Plan:**
- Add detailed logging to CoinbaseExecutor
- Test signal generation in isolation
- Verify API connectivity
- Adjust risk parameters if needed

### 0.7 Atomic Performance Tracking (2 hours) - MEDIUM PRIORITY
**Why:** Prevent double-counting P&L if bot crashes

**Implementation:**
```python
def _sync_positions_to_db(self, positions):
    """Sync positions with atomic performance updates."""
    try:
        cursor = self.db_conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN")
        
        # Find closed positions
        current_symbols = [p.symbol for p in positions] if positions else []
        cursor.execute("""
            SELECT symbol, unrealized_pl, entry_price, current_price, strategy
            FROM positions 
            WHERE bot_name = %s AND (symbol != ALL(%s) OR %s = 0)
            FOR UPDATE  -- Lock rows to prevent race conditions
        """, (self.bot_name, current_symbols if current_symbols else [''], len(current_symbols)))
        
        closed_positions = cursor.fetchall()
        
        # Update performance for closed positions
        for symbol, unrealized_pl, entry_price, current_price, strategy_name in closed_positions:
            if unrealized_pl is not None and self.performance_tracker:
                self.performance_tracker.update_strategy_performance(
                    bot_name=self.bot_name,
                    strategy_name=strategy_name or 'Unknown',
                    trade_pnl=float(unrealized_pl),
                    trade_pnl_pct=((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0,
                    is_win=unrealized_pl > 0
                )
        
        # Delete closed positions
        if current_symbols:
            cursor.execute(
                "DELETE FROM positions WHERE bot_name = %s AND symbol != ALL(%s)",
                (self.bot_name, current_symbols)
            )
        else:
            cursor.execute("DELETE FROM positions WHERE bot_name = %s", (self.bot_name,))
        
        # Upsert current positions
        for pos in positions:
            # ... existing upsert logic ...
            pass
        
        # Commit transaction (atomic)
        cursor.execute("COMMIT")
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        logger.error("position_sync_failed", error=str(e), exc_info=True)
```

### 0.8 Comprehensive Testing (8 hours) - MEDIUM PRIORITY
**Test Scenarios:**

1. **Bot Crash During Entry**
   - Place bracket order
   - Kill bot before fill
   - Restart bot
   - Verify position recovered
   - Verify stop-loss active

2. **Bot Crash During Exit**
   - Open position with bracket order
   - Trigger stop-loss
   - Kill bot before exit confirmation
   - Restart bot
   - Verify position closed
   - Verify P&L recorded

3. **Redis Failure**
   - Stop Redis
   - Verify bot continues trading (degrades gracefully)
   - Verify positions still protected by broker

4. **Database Failure**
   - Stop PostgreSQL
   - Verify bot continues trading
   - Verify positions still protected
   - Restart database
   - Verify sync recovers

5. **Strategy Failure**
   - Inject exception in one strategy
   - Verify other strategies continue
   - Verify failed strategy disabled after 3 failures

6. **Emergency Stop**
   - Set emergency stop flag
   - Verify all positions close
   - Verify bot stops trading

7. **Position Limit Tests**
   - Try to open 6th position → reject
   - Try to open 15% position → reject
   - Simulate 3% daily loss → stop trading

**Deliverable:** Test report showing all scenarios pass

---

## 📈 PHASE 1: Paper Trading Validation (Weeks 2-5)

**Goal:** Prove system is safe with simulated money before risking real capital

**Timeline:** 2-4 weeks  
**Capital:** $100K paper (Alpaca), $10K paper (Coinbase)

### 1.1 Deploy Safety Features to Paper Trading (Week 2)
- Deploy all Phase 0 features to production
- Run equity bot with $100K paper money
- Run crypto bot with $10K paper money
- Monitor daily for issues

### 1.2 Monitor Key Metrics (Weeks 2-5)
**Daily Checks:**
- Any stuck positions? (should be 0)
- Any limit violations? (should be 0)
- Any strategy failures? (track count)
- Any emergency stops triggered? (should be 0)
- P&L tracking accurate? (compare to broker)

**Weekly Review:**
- Strategy performance (win rate, P&L, Sharpe)
- Risk metrics (max drawdown, portfolio heat)
- System reliability (uptime, error rate)
- Bracket order execution (all positions protected?)

### 1.3 Success Criteria (Must Pass Before Live)
- ✅ Zero stuck positions (4 weeks)
- ✅ Zero limit violations (4 weeks)
- ✅ All bracket orders execute correctly (100%)
- ✅ Bot recovers from all crashes (tested)
- ✅ Performance tracking accurate (±1%)
- ✅ Crypto bot trading (at least 5 positions opened)
- ✅ Emergency stop works (tested)

**If ANY criteria fail → fix and restart 4-week validation**

---

## 💰 PHASE 2: Live Trading - Gradual Capital Deployment (Weeks 6-10)

**Goal:** Start with small capital, scale gradually as confidence builds

**Approach:** Start tiny, double every 2 weeks if successful

### 2.1 Week 6-7: $200 Live ($100 equity, $100 crypto)
**Why start so small?**
- Test with money you can afford to lose completely
- Verify real broker execution (not just paper)
- Catch any paper-to-live differences

**Monitoring:**
- Check positions 2x per day (morning, evening)
- Verify bracket orders active on all positions
- Track P&L vs paper trading performance

**Success Criteria:**
- No stuck positions
- No limit violations
- Performance within 20% of paper trading
- All safety features working

### 2.2 Week 8-9: $500 Live ($250 equity, $250 crypto)
**Prerequisites:**
- Week 6-7 successful (no major issues)
- Confidence in system reliability

**Monitoring:**
- Check positions 1x per day
- Weekly performance review
- Compare to paper trading

### 2.3 Week 10-11: $1000 Live ($500 equity, $500 crypto)
**Prerequisites:**
- Week 8-9 successful
- System proven reliable

### 2.4 Week 12-13: $2000 Live ($1000 equity, $1000 crypto)
**Prerequisites:**
- Week 10-11 successful
- Ready for full deployment

### 2.5 Week 14+: Full $2600 Live ($1300 equity, $1300 crypto)
**Prerequisites:**
- All previous phases successful
- High confidence in system

**Ongoing:**
- Add new capital slowly ($100-500 at a time)
- Wait 1-2 weeks after deposit before deploying
- Never deploy more than 50% of new capital immediately

---

## 🎯 PHASE 3: Advanced Features (After Live Trading Stable)

**Only implement after 4+ weeks of successful live trading**

### 3.1 Kelly Criterion Position Sizing
- Calculate optimal position size based on win rate
- Use 25% Kelly for safety
- Requires 30+ trades for accuracy

### 3.2 Email Alerts
- Circuit breaker trips
- Emergency stop triggers
- Daily performance summary
- Strategy failures

### 3.3 Dashboard Enhancements
- Current regime indicator
- Strategy performance breakdown
- Risk metrics visualization
- Position heat map

### 3.4 Additional Strategies
**From archived roadmap:**
- Statistical arbitrage
- VWAP strategies
- Volume profile
- Order flow analysis

**Add one strategy at a time, validate for 2 weeks before adding next**

---

## 🚫 What NOT to Do (Anti-Patterns)

### ❌ Don't Rush to Live Trading
- **Bad:** "Safety features done, let's go live with $2600"
- **Good:** "Safety features done, let's paper trade for 4 weeks, then start with $200"

### ❌ Don't Skip Testing
- **Bad:** "It works in dev, ship it"
- **Good:** "Test all failure scenarios, then paper trade, then tiny live"

### ❌ Don't Ignore Warnings
- **Bad:** "Strategy failed 3 times but still running, it's fine"
- **Good:** "Strategy failed 3 times, disable it and investigate"

### ❌ Don't Deploy All Capital at Once
- **Bad:** "System works with $200, let's deploy $2600"
- **Good:** "System works with $200, let's try $500 for 2 weeks"

### ❌ Don't Add Features While Live Trading
- **Bad:** "Let's add Kelly Criterion while trading with $2600"
- **Good:** "Let's paper trade Kelly Criterion for 2 weeks first"

---

## 📊 Risk Budget - Conservative Approach

**For $2600 portfolio:**

| Limit | Value | Reasoning |
|-------|-------|-----------|
| Max position size | 10% ($260) | Small enough to survive 5 losses |
| Max positions | 5 | Diversification without over-trading |
| Max daily loss | 3% ($78) | Stop trading if bad day |
| Max total risk | 15% ($390) | All positions combined |
| Stop-loss per trade | 3% | Broker-enforced via bracket orders |
| Take-profit per trade | 5% | 1.67:1 reward-risk ratio |

**Expected Outcomes:**
- **Worst case (all 5 positions hit stop):** -15% ($390 loss)
- **Bad day (3% daily loss limit):** -3% ($78 loss)
- **Single bad trade:** -3% of position (~$8-26 loss)

**With 57% win rate (backtested):**
- Expected monthly return: 2-5%
- Expected monthly loss (bad month): -5% to -10%
- Probability of -15% month: <5%

---

## 🎯 Success Metrics

### Phase 0 (Safety Features)
- ✅ All 7 safety features implemented
- ✅ All tests passing
- ✅ Code reviewed and deployed

### Phase 1 (Paper Trading)
- ✅ 4 weeks with zero stuck positions
- ✅ 4 weeks with zero limit violations
- ✅ Crypto bot trading (5+ positions)
- ✅ Performance tracking accurate

### Phase 2 (Live Trading)
- ✅ Week 6-7: $200 live, no major issues
- ✅ Week 8-9: $500 live, performance on track
- ✅ Week 10-11: $1000 live, confidence high
- ✅ Week 12+: $2600 live, system proven

### Phase 3 (Advanced Features)
- ✅ Kelly Criterion tested and deployed
- ✅ Email alerts working
- ✅ Dashboard enhanced
- ✅ Additional strategies validated

---

## 🔄 Continuous Improvement

**Weekly:**
- Review strategy performance
- Check for new failures or warnings
- Update risk limits if needed

**Monthly:**
- Retrain ML models
- Review and optimize parameters
- Add new strategies (one at a time)

**Quarterly:**
- Full system audit
- Review all safety features
- Update documentation

---

## 📞 Emergency Procedures

### If Bot Crashes
1. Check if positions still open on broker
2. Verify bracket orders active
3. Restart bot
4. Run position recovery
5. Review logs for root cause

### If Positions Stuck
1. Trigger emergency stop
2. Manually close positions on broker
3. Investigate root cause
4. Fix issue
5. Test in paper trading before resuming

### If Daily Loss Limit Hit
1. Bot automatically stops trading
2. Review what went wrong
3. Adjust strategy parameters if needed
4. Resume next day (automatic)

### If You Need to Stop Everything
```bash
# Emergency stop (closes all positions and stops bot)
redis-cli SET bot:quantshift-equity:emergency_stop true
redis-cli SET bot:quantshift-crypto:emergency_stop true

# Or manually on broker
# Log into Alpaca/Coinbase and close all positions
```

---

## 📝 Documentation Requirements

**Before Live Trading:**
- [ ] All safety features documented
- [ ] Emergency procedures documented
- [ ] Risk limits documented
- [ ] Testing results documented

**During Live Trading:**
- [ ] Daily trading journal (first 2 weeks)
- [ ] Weekly performance review
- [ ] Monthly system audit

---

## ✅ Final Checklist Before Live Trading

- [ ] Emergency kill switch implemented and tested
- [ ] Hard position limits enforced in code
- [ ] Bracket orders working (all positions protected)
- [ ] Position recovery on startup working
- [ ] Graceful strategy failure handling working
- [ ] Crypto bot trading (issue diagnosed and fixed)
- [ ] Atomic performance tracking implemented
- [ ] All test scenarios passing
- [ ] 4 weeks successful paper trading
- [ ] Emergency procedures documented
- [ ] You understand all risks
- [ ] You can afford to lose $200 (first deployment)

**Only check this box when ALL above are complete:** [ ] Ready for live trading

---

**Last Updated:** 2026-02-27  
**Next Review:** After Phase 0 completion  
**Owner:** Development Team
