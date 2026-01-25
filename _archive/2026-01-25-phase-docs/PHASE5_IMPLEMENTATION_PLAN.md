# Phase 5: Advanced Features Implementation Plan

**Status:** In Progress  
**Started:** December 26, 2025  
**Goal:** Build all advanced features from user's previous successful bot

---

## Overview

While the bot validates in paper trading (Phase 3 - background), we'll build all Phase 5 features in parallel. These features work identically in paper trading and live trading, so we can test them immediately.

---

## Phase 5.1: Email Notification System ⏳ IN PROGRESS

**Goal:** Real-time alerts for trades, performance, and errors

**Duration:** 1-2 days

### Features:
1. **Trade Execution Alerts**
   - Buy/Sell notifications with entry price, stop, target
   - Position size and risk amount
   - Strategy signal details

2. **Daily Performance Summary**
   - End-of-day P&L report
   - Open positions summary
   - Win rate and trade statistics

3. **Weekly Performance Report**
   - Week-over-week comparison
   - Trade breakdown (winners/losers)
   - Strategy performance metrics
   - Charts and visualizations

4. **Error & Alert Notifications**
   - Bot errors or crashes
   - Risk limit breaches
   - Execution failures
   - System health alerts

### Implementation:
- Email service using Gmail SMTP (App Password)
- Email templates with HTML formatting
- Configuration for recipients and alert types
- Integration with bot event system

### Deliverables:
- `packages/core/src/quantshift_core/notifications/email_service.py`
- `config/email_config.yaml`
- Email templates in `templates/emails/`
- Integration with `run_bot_v2.py`

---

## Phase 5.2: Golden Cross Scanner 📊 PENDING

**Goal:** Daily pre-market scanner for 600+ stocks across major indices

**Duration:** 3-5 days

### Features:
1. **Universe Scanning**
   - SP500 (500 stocks)
   - NASDAQ100 (100 stocks)
   - DOW30 (30 stocks)
   - RUSSELL1000 (1000 stocks)
   - Total: ~1,600 unique stocks

2. **Golden Cross Detection**
   - MA 5/20 crossover (same as bot strategy)
   - Volume confirmation
   - Price filters ($5-$1,000)
   - Market cap filters (>$100M)

3. **Quality Filters**
   - Min volume: 100,000 shares/day
   - MA spread percentage
   - Price above MA5
   - Exclude REITs

4. **Daily Reports**
   - Pre-market email (before 9:30 AM ET)
   - Top 10-20 candidates
   - Entry prices, stops, targets
   - Risk/reward ratios

### Implementation:
- Scanner engine using Alpaca data
- Parallel processing for speed
- Caching to avoid rate limits
- Email integration for reports

### Deliverables:
- `apps/scanners/golden_cross_scanner.py`
- `config/scanner_config.yaml`
- Scheduled cron job for daily runs
- Email template for scanner reports

---

## Phase 5.3: Scale-Out Strategy 📈 PENDING

**Goal:** Partial profit-taking to improve win rate and reduce risk

**Duration:** 2-3 days

### Features:
1. **Tiered Exit Strategy**
   - Exit 50% at +1 ATR (first target)
   - Exit 33% at resistance levels
   - Let 17% run with trailing stop

2. **Dynamic Targets**
   - Calculate ATR-based targets
   - Identify resistance levels
   - Adjust based on market conditions

3. **Risk Reduction**
   - Move stop to breakeven after first exit
   - Lock in profits progressively
   - Reduce position risk over time

### Implementation:
- Extend `MACrossoverStrategy` with scale-out logic
- Track partial positions in Redis
- Update position management in `AlpacaExecutor`
- Add scale-out configuration

### Deliverables:
- Updated `packages/core/src/quantshift_core/strategies/ma_crossover.py`
- Scale-out configuration in `equity_strategy.yaml`
- Position tracking for partial exits
- Testing with paper trading

---

## Phase 5.4: Trailing Stops 🛡️ PENDING

**Goal:** Dynamic stop-loss that follows price to protect profits

**Duration:** 1-2 days

### Features:
1. **ATR-Based Trailing**
   - 1.5x ATR trailing distance
   - Updates as price moves favorably
   - Never moves against you

2. **Breakeven Protection**
   - Move to breakeven after +0.5 ATR
   - Ensures no loss on winning trades
   - Psychological comfort

3. **Profit Lock-In**
   - Automatically tightens as profit grows
   - Captures trends without premature exits
   - Reduces give-back on reversals

### Implementation:
- Add trailing stop logic to strategy
- Update stop prices in real-time
- Integrate with Alpaca bracket orders
- Track trailing stops in Redis

### Deliverables:
- Trailing stop module in strategy
- Configuration for trailing parameters
- Real-time stop updates
- Testing and validation

---

## Phase 5.5: Dashboard Enhancements 📊 PENDING

**Goal:** Better visualization and monitoring of bot performance

**Duration:** 3-4 days

### Features:
1. **Real-Time Strategy Metrics**
   - Live P&L tracking
   - Win rate and profit factor
   - Sharpe ratio (rolling)
   - Max drawdown monitoring

2. **Trade History & Analytics**
   - Trade log with entry/exit details
   - Performance by symbol
   - Time-based analysis
   - Trade distribution charts

3. **Position Management View**
   - Current positions with unrealized P&L
   - Stop and target levels
   - Time in trade
   - Risk exposure

4. **Performance Charts**
   - Equity curve
   - Daily/weekly returns
   - Drawdown chart
   - Win/loss distribution

### Implementation:
- Enhance existing dashboard
- Add new API endpoints
- Create visualization components
- Real-time updates via WebSocket (optional)

### Deliverables:
- Updated dashboard UI
- New API endpoints for metrics
- Performance charts and graphs
- Real-time data updates

---

## Implementation Order & Timeline

### Week 1 (Dec 26 - Jan 2):
**Phase 5.1: Email Notifications**
- Day 1-2: Build email service and templates
- Day 3: Integrate with bot
- Day 4: Test and deploy

### Week 2 (Jan 2 - Jan 9):
**Phase 5.2: Golden Cross Scanner**
- Day 1-2: Build scanner engine
- Day 3-4: Add quality filters and universe
- Day 5: Email integration and scheduling

### Week 3 (Jan 9 - Jan 16):
**Phase 5.3 & 5.4: Scale-Out + Trailing Stops**
- Day 1-2: Implement scale-out strategy
- Day 3: Implement trailing stops
- Day 4-5: Testing and integration

### Week 4 (Jan 16 - Jan 26):
**Phase 5.5: Dashboard Enhancements**
- Day 1-2: Build new metrics and charts
- Day 3-4: UI improvements
- Day 5: Testing and polish

---

## Success Criteria

### Email Notifications:
- ✓ Receive trade alerts within 1 minute of execution
- ✓ Daily summaries sent at market close
- ✓ Weekly reports sent Sunday evening
- ✓ Error alerts sent immediately

### Golden Cross Scanner:
- ✓ Scans 600+ stocks in under 10 minutes
- ✓ Identifies 10-20 quality candidates daily
- ✓ Email report sent before 9:30 AM ET
- ✓ No false positives (quality filters working)

### Scale-Out Strategy:
- ✓ Partial exits execute correctly
- ✓ Stops move to breakeven after first exit
- ✓ Position tracking accurate
- ✓ Improves win rate vs simple exits

### Trailing Stops:
- ✓ Stops trail price correctly
- ✓ Never moves against position
- ✓ Locks in profits on trends
- ✓ Reduces give-back on reversals

### Dashboard:
- ✓ Real-time metrics update correctly
- ✓ Charts render properly
- ✓ Trade history complete and accurate
- ✓ Performance tracking matches actual results

---

## Testing Strategy

All features will be tested in paper trading before any live deployment:

1. **Unit Tests:** Individual components tested in isolation
2. **Integration Tests:** Features tested with bot
3. **Paper Trading:** Real-world validation with paper money
4. **Performance Monitoring:** Track impact on strategy performance

---

## Parallel Execution

While building Phase 5 features:
- Phase 3 (paper trading validation) runs in background
- Bot trades automatically and logs everything
- We check performance weekly (not daily)
- After 30 days: Review results and make go/no-go decision

---

## Next Steps

**Starting NOW:** Phase 5.1 - Email Notification System

**First Task:** Build email service infrastructure and trade alert templates
