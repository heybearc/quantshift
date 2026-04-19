# QuantShift Plan

**Last updated:** 2026-04-19  
**Current phase:** Phase 1.5.9 - Paper Trading Validation  
**Status:** Production-ready system with continuous validation

---

## Current Phase

### Active Work
- [ ] **Paper Trading Validation** - Continuous validation with all safeguards deployed and active
- [ ] **Kraken Account Setup** - User action required to enable margin trading and shorting capability
- [ ] **End-to-end Failover Testing** - Test automated failover from primary to standby

### Completed This Phase
- ✅ Phase 0: Monitoring & Automated Failover (2026-02-25)
  - Redis configuration and capacity planning
  - Prometheus metrics integration
  - Grafana dashboards (System Health, Trading Performance)
  - Automated failover monitor with systemd service
  - Systemd watchdog integration
- ✅ Kraken Integration Development (2026-03-06)
  - KrakenExecutor class with margin trading support
  - Short position capability
  - Configuration and bot integration
- ✅ Multi-strategy deployment
  - 3 strategies running (RSI, Bollinger, Breakout)
  - 100 equity symbols + 50 crypto symbols
  - Dual bot architecture (equity + crypto)

---

## Prioritized Backlog

### High Priority
- [ ] **Kraken Production Deployment** - Enable shorting capability for crypto trading (awaiting user account setup)
- [ ] **Phase 1: Adaptive Strategy Selection** - ML-based strategy selection with regime detection (2-3 weeks)
- [ ] **Phase 2: Advanced Risk Management** - Position sizing, portfolio optimization, correlation analysis (1-2 weeks)
- [ ] **Phase 3: ML Regime Detection** - Market regime classification and strategy adaptation (1 week)

### Medium Priority
- [ ] **Phase 4: Multi-Timeframe Analysis** - Combine signals from multiple timeframes (1 week)
- [ ] **Phase 5: Portfolio Optimization** - Modern Portfolio Theory integration (1 week)
- [ ] **Phase 6: Sentiment Analysis** - News sentiment integration with FinBERT (4-6 hours)
- [ ] **Enhanced Monitoring** - Component status dashboard, alert panels

### Low Priority
- [ ] **Advanced Features** - Streaming news feed, alternative data sources
- [ ] **Performance Optimization** - Latency improvements, caching strategies
- [ ] **Additional Exchanges** - Expand beyond Coinbase and Kraken

---

## Known Issues

### Pending Testing
- **End-to-end Failover Test** - Need to verify standby takes over in < 30 seconds with no data loss

### Operational Notes
- **Paper Trading Active** - Validation clock started Feb 21, 2026
- **Dual Bot Architecture** - equity-bot (CT 100) + crypto-bot (CT 100) both running
- **Monitoring Stack** - Prometheus (CT 150) + Grafana dashboards operational

---

## Roadmap

### Phase 0: Monitoring & Automated Failover
**Status:** Completed (2026-02-25)  
**Objectives:**
- Production-grade monitoring
- Automated failover for real money trading
- Active-Standby architecture

**Deliverables:**
- ✅ Redis master-slave replication with failover
- ✅ Prometheus metrics integration (health + business metrics)
- ✅ Grafana dashboards (System Health, Trading Performance)
- ✅ Automated failover monitor with systemd service
- ✅ Systemd watchdog integration

### Phase 1: Adaptive Strategy Selection
**Status:** Planned (2-3 weeks)  
**Objectives:**
- ML-based strategy selection
- Market regime detection
- Dynamic strategy weighting

**Deliverables:**
- Regime classifier (trending, ranging, volatile, calm)
- Strategy performance tracking by regime
- Adaptive strategy selector
- Backtesting with regime awareness

### Phase 2: Advanced Risk Management
**Status:** Planned (1-2 weeks)  
**Objectives:**
- Sophisticated position sizing
- Portfolio-level risk controls
- Correlation-aware trading

**Deliverables:**
- Kelly Criterion position sizing
- Portfolio heat limits
- Correlation matrix analysis
- Sector exposure limits

### Phase 3: ML Regime Detection
**Status:** Planned (1 week)  
**Objectives:**
- Automated market regime classification
- Strategy adaptation based on regime

**Deliverables:**
- Random Forest regime classifier
- Real-time regime detection
- Strategy switching logic
- Regime transition handling

### Phase 4: Multi-Timeframe Analysis
**Status:** Planned (1 week)  
**Objectives:**
- Combine signals from multiple timeframes
- Improve signal quality

**Deliverables:**
- Multi-timeframe signal aggregation
- Timeframe weighting system
- Trend alignment detection

### Phase 5: Portfolio Optimization
**Status:** Planned (1 week)  
**Objectives:**
- Modern Portfolio Theory integration
- Risk-adjusted returns optimization

**Deliverables:**
- Efficient frontier calculation
- Sharpe ratio optimization
- Portfolio rebalancing logic

### Phase 6: Sentiment Analysis
**Status:** Planned (4-6 hours)  
**Objectives:**
- News sentiment integration
- FinBERT sentiment scoring

**Deliverables:**
- NewsAPI.org integration
- Real-time sentiment gauges
- Sentiment vs price correlation
- News feed with sentiment scores

### Phase 7: Crypto Exchange Migration
**Status:** In Progress  
**Objectives:**
- Enable margin trading and shorting on crypto
- Reduce trading fees

**Deliverables:**
- ✅ Kraken integration development complete
- ⏳ User account setup (pending)
- ⏳ Testing and deployment (pending)

---

## Notes

### Mission
Build a fully adaptive, multi-strategy trading system with regime detection, advanced risk management, and institutional-grade monitoring — all while running continuous paper trading validation.

**Timeline:** 6-8 weeks to production-ready  
**Approach:** Build and test incrementally, deploy features as they're completed  
**Validation:** Continuous paper trading throughout development

### Success Metrics (Production Trading Targets)
**Performance:**
- Sharpe Ratio: > 2.0 (industry: 1.5-2.0)
- Max Drawdown: < 15% (industry: 15-20%)
- Win Rate: > 55% (industry: 50-55%)
- Profit Factor: > 2.0 (industry: 1.5-2.0)
- Annual Return: > 30% (industry: 15-25%)

**Operational:**
- Uptime: > 99.9%
- Order Latency: < 100ms
- Slippage: < 0.1%
- Deployment Time: < 5 minutes
- Failover Time: < 30 seconds

### Infrastructure
**Bots:**
- equity-bot: CT 100 (primary), CT 101 (standby) - 100 symbols, 3 strategies
- crypto-bot: CT 100 (primary), CT 101 (standby) - 50 symbols, 3 strategies
- kraken-bot: Pending deployment (margin trading + shorting)

**Monitoring:**
- Prometheus: CT 150 (10.92.3.2:9090)
- Grafana: CT 150 (10.92.3.2:3000)
- Redis: Master-slave replication (10.92.3.27 → 10.92.3.28)

**Deployment:**
- Web app: CT 137 (blue), CT 138 (green)
- Port: 3001 (standard)

### Strategies Deployed
1. **RSI Mean Reversion** - 57.5% win rate
2. **Bollinger Bounce** - 58.6% win rate
3. **Breakout Momentum** - Backtesting pending

### Effort Sizing Guide
- **S (Small):** 1-4 hours
- **M (Medium):** 1-2 days
- **L (Large):** 3-5 days
- **XL (Extra Large):** 1+ weeks

### Key Files
- **TASK-STATE.md** - Current work and daily context
- **PLAN.md** - This file - long-term planning and backlog
