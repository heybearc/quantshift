# Implementation Plan - QuantShift

**Last Updated:** 2026-02-20
**Current Phase:** v1.4.0 in production — Bot reactivation and production trading path

---

## 🚨 CRITICAL: Bot Status

**Bot is RUNNING** — equity-bot + crypto-bot both active on CT100, heartbeating every 30s. (2026-02-21)

**Bugs fixed (2026-02-21):**
- ✅ `positions` table duplicate key error — fixed with UPSERT in `database_writer.py`
- ✅ Trade recording wired into `run_strategy` — executed orders now written to `trades` table

**Paper trading validation — NOT COMPLETE. Reset required.**
- Dec 26 – Jan 26 validation period: **0 meaningful equity trades recorded**
- Feb 13: 500 SPY BUY orders fired simultaneously at market open — runaway loop bug (old bot version, not v2)
- Only real equity trade: AAPL BUY Jan 30 @ $260.49 (still open, +$4.09)
- **Go/no-go criteria cannot be evaluated** — insufficient trade history
- **Action required:** Reset paper account, restart 30-day validation clock with v2 bot

**Go/No-Go Criteria for Live Trading:**
- Minimum 10 trades in 30 days
- Win rate ≥ 45%
- Max drawdown < 20%
- No critical bugs

---

## 🎯 Active Work (This Week)

**Current Focus:** Reset paper trading validation, fix runaway order bug

- [x] Diagnose and fix stale bot status (effort: S) — DONE 2026-02-21
- [x] Fix positions duplicate key + wire trade recording (effort: S) — DONE 2026-02-21
- [ ] Investigate Feb 13 runaway SPY order bug — 500 orders in 2 min, find root cause (effort: S)
- [ ] Reset Alpaca paper account to clear runaway SPY positions (effort: S)
- [ ] Restart 30-day paper trading validation clock (effort: S)
- [ ] Monitor equity-bot v2 for first real MA crossover signal + trade record (effort: S)

---

## 📋 Backlog (Prioritized)

### 🔴 Critical — Bot Production Path

#### Phase 0: Paper Trading Reset (Do First)
- [x] SSH to bot container and check process status — DONE (effort: S)
- [x] Fix positions duplicate key bug — DONE (effort: S)
- [x] Wire trade recording to strategy cycle — DONE (effort: S)
- [ ] Find and fix root cause of Feb 13 runaway SPY order bug (effort: S)
- [ ] Reset Alpaca paper account (effort: S)
- [ ] Restart 30-day validation clock, monitor for real signals (effort: S)

#### Phase 1: Advanced Risk Management (Before Live Trading)
- [ ] Portfolio heat tracking — max 10% total risk exposure (effort: M)
- [ ] Kelly Criterion position sizing — fractional Kelly (0.25-0.5) (effort: M)
- [ ] Advanced stop losses — trailing ATR, Chandelier, Parabolic SAR (effort: M)
- [ ] Maximum drawdown circuit breakers — auto-halt trading (effort: M)
- [ ] Daily loss limits — hard stop at configurable threshold (effort: S)
- [ ] Position correlation monitoring — avoid correlated positions (effort: M)
- [ ] Sector exposure limits (effort: S)

#### Phase 2: Multi-Strategy Framework (Before Live Trading)
- [ ] Strategy base class / interface (effort: M)
- [ ] RSI Mean Reversion strategy (effort: M)
- [ ] Bollinger Band bounce strategy (effort: M)
- [ ] Breakout / momentum strategy (effort: M)
- [ ] Strategy allocation system — capital per strategy (effort: L)
- [ ] Strategy performance tracking per strategy (effort: M)
- [ ] Auto-reallocation based on performance (effort: L)
- [ ] Strategy correlation monitoring (effort: M)

#### Phase 3: Live Trading Go-Live Checklist
- [ ] Paper trading validation complete (30 days, 10+ trades, 45%+ win rate) (effort: N/A)
- [ ] Phase 1 risk management implemented (effort: N/A)
- [ ] Phase 2 multi-strategy framework implemented (effort: N/A)
- [ ] Alpaca live trading API credentials configured (effort: S)
- [ ] Hard position limits configured (effort: S)
- [ ] Daily loss limit configured (effort: S)
- [ ] Emergency kill switch tested (effort: S)
- [ ] Monitoring and alerting active (effort: N/A)
- [ ] Full audit trail logging active (effort: N/A)

### 🟡 High Priority — Platform Enhancements

#### Admin Platform — Trading Pages Integration
- [ ] Connect Trades page to live bot data (effort: M)
- [ ] Connect Positions page to live bot data (effort: M)
- [ ] Connect Performance page to live bot data (effort: M)
- [ ] Real-time bot monitoring dashboard (effort: L)
- [ ] Bot start/stop controls from admin UI (effort: M)

#### Dashboard Enhancements
- [ ] Historical data tracking — 7-day snapshots of key metrics (effort: L)
- [ ] Sparkline charts for 7-day trends on dashboard cards (effort: M)
- [ ] API status monitoring — external API health and response times (effort: M)
- [ ] Notification settings save functionality (effort: S) — currently a stub

#### Phase 6: Real-Time Data Streaming
- [ ] Alpaca WebSocket client — replace polling with streaming (effort: L)
- [ ] Real-time quote processing (effort: M)
- [ ] Sub-second latency monitoring (effort: M)
- [ ] Event-driven architecture for bot (effort: L)
- [ ] Real-time P&L tracking (effort: M)

#### Monitoring & Alerting
- [ ] Email reports — daily/weekly performance summary (effort: M)
- [ ] Critical event alerts — drawdown breach, bot crash, API failure (effort: M)
- [ ] Anomaly detection — unusual trade patterns (effort: L)
- [ ] Performance degradation alerts (effort: M)

### 🟢 Medium Priority

#### Phase 4: Market Regime Detection
- [ ] Regime classification — bull, bear, high vol, low vol, crisis (effort: L)
- [ ] Strategy performance tracking by regime (effort: M)
- [ ] Automatic strategy switching by regime (effort: L)
- [ ] Position sizing adjustment by regime (effort: M)
- [ ] Risk reduction in high volatility regimes (effort: M)

#### Phase 5: Execution Optimization
- [ ] TWAP order execution (effort: M)
- [ ] VWAP order execution (effort: M)
- [ ] Limit orders with price improvement (effort: M)
- [ ] Pre-trade cost analysis (effort: M)
- [ ] Slippage monitoring and reporting (effort: S)

#### Phase 7: Crypto Bot — Coinbase Integration
- [ ] Coinbase Advanced Trade API integration (effort: L)
- [ ] Crypto-specific risk parameters — wider stops, higher vol (effort: M)
- [ ] 24/7 trading support (effort: M)
- [ ] Funding rate monitoring (effort: M)
- [ ] BTC/equity correlation monitoring (effort: M)
- [ ] Paper trading validation for crypto (effort: L)
- [ ] Go/no-go decision for crypto live trading (effort: S)

#### Phase 8: Backtesting & Optimization
- [ ] Walk-forward analysis (effort: L)
- [ ] Monte Carlo simulation (effort: L)
- [ ] Out-of-sample testing (effort: M)
- [ ] Realistic slippage and commission modeling (effort: M)
- [ ] Parameter optimization — Bayesian / genetic algorithms (effort: XL)

#### Phase 9: Bot Monitoring Infrastructure
- [ ] Prometheus metrics collection for bot performance (effort: L)
- [ ] Grafana dashboard for bot trades/P&L/drawdown (effort: L)
- [ ] Sentry error tracking integration (effort: M)
- [ ] Complete trade audit trail with justification logging (effort: M)
- [ ] Pattern day trader monitoring (effort: S)

### 🔵 Low Priority / Future

#### Phase 3: Machine Learning Integration
- [ ] Feature engineering — 50+ technical indicators (effort: XL)
- [ ] Random Forest price direction classifier (effort: XL)
- [ ] XGBoost gradient boosting model (effort: XL)
- [ ] LSTM time series model (effort: XL)
- [ ] Online learning — continuous model retraining (effort: XL)
- [ ] A/B testing of ML models (effort: L)

#### Advanced Features
- [ ] Options strategies — covered calls, cash-secured puts, iron condors (effort: XL)
- [ ] Alternative data — sentiment analysis, options flow, insider data (effort: XL)
- [ ] Multi-exchange support (effort: XL)
- [ ] Mobile app development (effort: XL)

#### Platform Polish
- [ ] Email verification for invited users (effort: M) — currently stubbed in invitations/accept
- [ ] User activity analytics — track engagement and feature usage (effort: M)
- [ ] Enhanced caching strategies — reduce database load (effort: M)
- [ ] Performance optimizations — query performance for large datasets (effort: M)
- [ ] Code quality improvements — TypeScript warnings, linting (effort: S)
- [ ] Help documentation for new features (effort: S)

---

## 🐛 Known Bugs

### Critical (Fix Immediately)
- [ ] **Runaway SPY order bug** — 500 BUY orders fired simultaneously on Feb 13 at market open. Root cause unknown — likely a loop in old bot code that ran on this account. Needs investigation before paper account reset.

### Non-Critical (Backlog)
None currently identified.

---

## 💡 User Feedback & Feature Requests

### From Users
- [ ] Additional trading metrics requested (effort: M) - More detailed performance indicators
- [ ] Historical performance tracking (effort: L) - Performance over time view

### From App (Observations)
- Dashboard cards well-received — positive feedback on v1.4.0 statistics cards
- Session management working well — max 3 sessions preventing session bloat

---

## 🗺️ Roadmap (Strategic)

### Q1 2026 (Jan-Mar) — Platform Foundation
- [x] Release notes standardization - COMPLETE
- [x] Blue-green deployment - COMPLETE
- [x] LIVE/STANDBY indicator - COMPLETE
- [x] Dashboard enhancements Phase 1-3 - COMPLETE
- [x] Session management - COMPLETE
- [x] /bump workflow integration - COMPLETE
- [x] v1.4.0 deployed to production - COMPLETE (2026-02-19)
- [x] D-025 PM2 naming compliance - COMPLETE (2026-02-19)
- [ ] **Bot reactivation** - IN PROGRESS
- [ ] Paper trading validation results review
- [ ] Admin platform trading pages

### Q2 2026 (Apr-Jun) — Bot Production Path
- [ ] Phase 1: Advanced risk management (before live trading)
- [ ] Phase 2: Multi-strategy framework (before live trading)
- [ ] Live trading go/no-go decision
- [ ] Real-time WebSocket data streaming
- [ ] Historical data tracking and sparkline charts
- [ ] Monitoring and alerting infrastructure

### Q3 2026 (Jul-Sep) — Scale & Diversify
- [ ] Phase 4: Market regime detection
- [ ] Phase 5: Execution optimization
- [ ] Phase 7: Crypto bot (Coinbase)
- [ ] Phase 8: Backtesting & optimization
- [ ] Phase 9: Prometheus/Grafana monitoring

### Q4 2026 and Beyond — Intelligence Layer
- [ ] Phase 3: Machine learning integration
- [ ] Options strategies
- [ ] Alternative data integration
- [ ] Multi-exchange support

---

## 🚦 Production Trading Checklist (Live Money Gate)

**ALL items must be checked before switching from paper to live trading:**

### Bot Validation
- [ ] 30-day paper trading validation complete
- [ ] Minimum 10 trades executed
- [ ] Win rate ≥ 45%
- [ ] Max drawdown < 20%
- [ ] No critical bugs in 30-day period

### Risk Management
- [ ] Portfolio heat tracking implemented (max 10% exposure)
- [ ] Kelly Criterion position sizing implemented
- [ ] Maximum drawdown circuit breaker implemented
- [ ] Daily loss limit implemented and tested
- [ ] Emergency kill switch tested

### Infrastructure
- [ ] Bot running on blue-green with hot-standby failover
- [ ] Monitoring and alerting active
- [ ] Full audit trail logging active
- [ ] Alpaca live API credentials configured and tested
- [ ] Database backup strategy confirmed

### Platform
- [ ] Admin trading pages connected to live data
- [ ] Real-time bot status visible in dashboard
- [ ] Bot start/stop controls working from admin UI

---

## 📝 Deferred Items

**Items explicitly deferred with rationale:**

- **Help documentation pages** — Deferred until feature set stabilizes. Current help page is functional. (2026-02-18)

> **Homelab infrastructure backlog** has been moved to the control plane: `_cloudy-ops/docs/infrastructure/homelab-backlog.md` and is tracked in the homelab-nexus repo.

---

## ✅ Recently Completed (Last 30 Days)

- [x] D-025 PM2 process naming compliance fixed — Blue: quantshift-blue, Green: quantshift-green - Date: 2026-02-19
- [x] MCP server config updated for QuantShift blue-green (correct IPs, containers, SSH) - Date: 2026-02-19
- [x] v1.4.0 deployed to production (Green, LIVE) - Date: 2026-02-19
- [x] STANDBY (Blue) synced with v1.4.0 - Date: 2026-02-19
- [x] Comprehensive E2E testing on STANDBY (81/81 tests passed) - Date: 2026-02-18
- [x] Version bump to v1.4.0 (Enhanced Dashboard Analytics) - Date: 2026-02-18
- [x] User-friendly release notes created - Date: 2026-02-18
- [x] /bump workflow validation and testing - Date: 2026-02-18
- [x] D-022 migration (single implementation plan standard) - Date: 2026-02-02
- [x] Document archival (6 historical planning docs) - Date: 2026-02-02
- [x] Governance sync (D-022 policy update) - Date: 2026-02-02
- [x] Dashboard statistics cards (Phase 1-3) - Date: 2026-01-30
- [x] Session management (max 3 per user) - Date: 2026-01-30
- [x] Admin stats API with JWT auth - Date: 2026-01-30
- [x] Trading metrics cards (Win Rate, Drawdown, Strategy) - Date: 2026-01-30
- [x] Trend indicator components - Date: 2026-01-30
- [x] Release notes 500 error fix - Date: 2026-01-30
- [x] LIVE/STANDBY indicator (v1.3.0) - Date: 2026-01-29
- [x] Blue-green deployment infrastructure - Date: 2026-01-26
- [x] HAProxy configuration and health checks - Date: 2026-01-26
- [x] Release notes system complete - Date: 2026-01-25
- [x] Monorepo restructure (apps/web/) - Date: 2026-01-25
- [x] Repository cleanup and archival - Date: 2026-01-25

---

## 📊 Effort Sizing Guide

- **S (Small):** 1-4 hours - Quick fixes, minor tweaks
- **M (Medium):** 1-2 days - Standard features, moderate bugs
- **L (Large):** 3-5 days - Complex features, major refactoring
- **XL (Extra Large):** 1+ weeks - Major modules, architectural changes

---

## 🎯 Success Metrics (Production Trading Targets)

### Performance Targets
- **Sharpe Ratio:** > 2.0 (industry standard: 1.5-2.0)
- **Max Drawdown:** < 15% (industry standard: 15-20%)
- **Win Rate:** > 55% (industry standard: 50-55%)
- **Profit Factor:** > 2.0 (industry standard: 1.5-2.0)
- **Annual Return:** > 30% (industry standard: 15-25%)

### Operational Targets
- **Uptime:** > 99.9%
- **Order Latency:** < 100ms
- **Slippage:** < 0.1%
- **Deployment Time:** < 5 minutes (blue-green)
- **Failover Time:** < 30 seconds
