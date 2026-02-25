# QuantShift Production Roadmap

**Last Updated:** 2026-02-21
**Current Status:** Bollinger Bands strategy deployed, building production-ready adaptive trading system

---

## 🎯 MISSION: Production-Ready Adaptive Trading System

Build a fully adaptive, multi-strategy trading system with regime detection, advanced risk management, and institutional-grade monitoring — all while running continuous paper trading validation.

**Timeline:** 6-8 weeks to production-ready
**Approach:** Build and test incrementally, deploy features as they're completed
**Validation:** Continuous paper trading throughout development

---

## ✅ COMPLETED (Feb 21, 2026)

### Strategy Development
- ✅ Backtested 3 strategies (RSI 57.5% WR, Bollinger 58.6% WR, Breakout pending)
- ✅ Bollinger Bands strategy deployed to production (LIVE on qs-primary)
- ✅ Backtest framework created (Yahoo Finance data, reusable scripts)
- ✅ Bot framework supports BaseStrategy pattern

### Infrastructure
- ✅ Fixed positions duplicate key bug
- ✅ Fixed crypto bot positions sync issue
- ✅ Wired all dashboard pages for both bots (Trades, Positions, Performance)
- ✅ Dashboard shows combined portfolio + per-bot breakdown
- ✅ Blue-green deployment working
- ✅ Database schema supports multi-bot tracking

### Bot Status
- ✅ equity-bot: RUNNING with BollingerBounce strategy
- ✅ crypto-bot: RUNNING (needs strategy replacement - current strategy failed backtest)
- ✅ Both bots heartbeating to database every 30s

---

## 🚀 PRODUCTION ROADMAP

### **PHASE 0: Infrastructure & State Management** (Week 0 - Foundation)
**Goal:** Complete critical infrastructure for production reliability

#### 0.1 Redis Replication for Failover (30 min)
- [ ] Configure standby Redis as replica of primary
  - Set `replicaof 10.92.3.27 6379` on standby
  - Set `masterauth Cloudy_92!` for authentication
  - Verify replication status with `INFO replication`
  - Test state sync between primary and standby

#### 0.2 Position Recovery on Startup (2 hours)
- [ ] Implement position loading from Redis
  - Load positions from `bot:{bot_name}:position:*` keys
  - Reconcile with broker API (handle discrepancies)
  - Resume managing existing positions
  - Log recovery status (positions loaded, discrepancies found)
  
- [ ] Add graceful shutdown position saving
  - Save all open positions to Redis before shutdown
  - Close positions safely if configured
  - Test shutdown handler with SIGTERM

#### 0.3 Stop-Loss/Take-Profit Order Placement (3 hours)
- [ ] Implement Coinbase stop-loss orders
  - Use Coinbase Advanced Trade API stop orders
  - Handle order placement errors
  - Track SL/TP orders in database
  
- [ ] Implement Alpaca stop-loss orders
  - Use bracket orders for SL/TP
  - Handle partial fills
  - Update position tracking

#### 0.4 ML Model Training & Deployment (1 hour)
- [ ] Train ML regime classifier
  - Run `train_ml_regime_classifier.py` on 2 years SPY data
  - Validate 91.7% accuracy target
  - Save model to `/opt/quantshift/models/regime_classifier.pkl`
  - Deploy to primary and standby servers
  
- [ ] Train RL position sizing agent
  - Run `train_rl_agent.py` for PPO training
  - Validate Sharpe ratio improvement
  - Save model to `/opt/quantshift/models/rl_agent.pkl`
  - Deploy to servers

#### 0.5 ML Model Lifecycle Management (4 hours)
- [ ] **Automated Retraining Pipeline**
  - Cron job for weekly model retraining
  - Model performance monitoring (accuracy drift detection)
  - Automatic rollback if new model performs worse
  - Model versioning (keep last 3 versions)
  
- [ ] **Admin UI for ML Operations**
  - "Train Models" button (triggers training job)
  - Model performance dashboard (accuracy, last trained, version)
  - Manual model rollback capability
  - Training job status/logs viewer
  - Schedule configuration (weekly/monthly/manual)
  
- [ ] **Model Monitoring & Alerts**
  - Track prediction accuracy vs actual outcomes
  - Alert if accuracy drops below 75%
  - Compare ML vs rule-based performance
  - Automatic fallback to rule-based if ML fails

**Deliverable:** Production-ready infrastructure with failover, position recovery, and ML lifecycle management

---

### **PHASE 1: Multi-Strategy Framework** (Week 1-2)
**Goal:** Run 3 uncorrelated strategies simultaneously for natural market adaptation

#### 1.1 Strategy Implementation
- [ ] **RSI Mean Reversion Strategy** (2 days)
  - Create `rsi_mean_reversion.py` in strategies module
  - Entry: RSI crosses below 30 (oversold)
  - Exit: RSI crosses above 70 (overbought) OR price hits target
  - Backtest validated: 57.5% WR, 16.82% return
  
- [ ] **Breakout Momentum Strategy** (2 days)
  - Create `breakout_momentum.py` in strategies module
  - Entry: Price breaks 20-day high + volume > 1.5x average
  - Exit: Trailing stop at 1.5×ATR OR price breaks 10-day low
  - Backtest on SPY/QQQ/AAPL/MSFT (target: >50% WR)

#### 1.2 Multi-Strategy Orchestration (3 days)
- [ ] Create `StrategyOrchestrator` class
  - Manages multiple strategies simultaneously
  - Capital allocation per strategy (configurable %)
  - Conflict resolution (if multiple strategies signal same symbol)
  - Aggregates signals from all active strategies
  
- [ ] Strategy allocation system
  - Default: 40% Bollinger, 30% RSI, 30% Breakout
  - Configurable via `config/strategy_allocation.yaml`
  - Per-strategy position limits
  
- [ ] Performance tracking per strategy
  - Track P&L, win rate, Sharpe per strategy
  - Store in `strategy_performance` table
  - API endpoint: `/api/bot/strategy-performance`

#### 1.3 Testing & Deployment (2 days)
- [ ] Unit tests for each strategy
- [ ] Integration test: all 3 strategies running simultaneously
- [ ] Deploy to qs-primary
- [ ] Monitor for 48 hours, verify no conflicts

**Deliverable:** Bot runs 3 strategies, each trading independently with allocated capital

---

### **PHASE 2: Market Regime Detection** (Week 3)
**Goal:** Detect market conditions and adapt strategy allocation dynamically

#### 2.1 Regime Indicators (2 days)
- [ ] Create `MarketRegimeDetector` class
  - **Trend:** 50-day SMA slope (degrees per day)
  - **Volatility:** 20-day ATR / 100-day ATR ratio
  - **Breadth:** % of SPY components above 200-day MA
  - **Fear:** VIX level (via Alpaca or Yahoo Finance)
  
- [ ] Historical regime calculation
  - Calculate regime for past 2 years
  - Validate regime changes align with known market events
  - Store in `market_regime` table

#### 2.2 Regime Classification (1 day)
- [ ] Define 5 regime types:
  - **Bull Trending:** Uptrend + low vol (ATR ratio < 1.2)
  - **Bear Trending:** Downtrend + low vol
  - **High Vol Choppy:** ATR ratio > 1.5, no clear trend
  - **Low Vol Range:** ATR ratio < 0.8, no trend
  - **Crisis:** VIX > 30 OR ATR ratio > 2.0
  
- [ ] Regime transition logic
  - Require 3 consecutive days to confirm regime change
  - Prevent rapid regime switching

#### 2.3 Regime-Based Adaptation (2 days)
- [ ] Strategy allocation by regime:
  ```yaml
  bull_trending:
    breakout: 50%
    bollinger: 30%
    rsi: 20%
  high_vol_choppy:
    bollinger: 60%
    rsi: 30%
    breakout: 10%
  crisis:
    cash: 80%
    bollinger: 20%  # Wide stops only
  ```
  
- [ ] Position sizing by regime:
  - Normal: 1% risk per trade
  - High vol: 0.5% risk per trade
  - Crisis: 0.25% risk per trade OR halt trading
  
- [ ] Dashboard regime indicator
  - Show current regime on dashboard
  - Show regime history (last 30 days)

#### 2.4 Testing (1 day)
- [ ] Backtest regime detection on 2022-2024 data
- [ ] Verify regime-based allocation improves returns
- [ ] Deploy and monitor

**Deliverable:** Bot automatically adjusts strategy allocation based on market regime

---

### **PHASE 3: Advanced Risk Management** (Week 4)
**Goal:** Portfolio-level risk controls that prevent catastrophic losses

#### 3.1 Portfolio Heat Tracking (2 days)
- [ ] Create `RiskManager` class
  - Track total portfolio risk exposure
  - Max 10% total risk (sum of all position risks)
  - Reduce to 5% in high vol, 2% in crisis
  
- [ ] Position risk calculation
  - Risk per position = (entry - stop) × quantity
  - Total risk = sum of all open position risks
  - Block new trades if total risk > limit

#### 3.2 Correlation & Concentration Limits (2 days)
- [ ] Correlation monitoring
  - Calculate 30-day correlation between all positions
  - Block new position if correlation > 0.7 with existing
  - Use Yahoo Finance for correlation data
  
- [ ] Sector exposure limits
  - Max 30% of portfolio in any sector
  - Sector mapping: SPY→Equity, QQQ→Tech, etc.
  - Block trades that exceed sector limit

#### 3.3 Circuit Breakers (1 day)
- [ ] Daily loss limit
  - Halt trading if daily loss > 5% of starting equity
  - Require manual restart via admin UI
  - Email alert on circuit breaker trip
  
- [ ] Drawdown circuit breaker
  - Halt if drawdown > 15% from peak equity
  - Reduce position sizes at 10% drawdown
  - Email alert with recovery plan

#### 3.4 Kelly Criterion Position Sizing (1 day)
- [ ] Implement fractional Kelly
  - Kelly % = (Win Rate × Avg Win - (1 - Win Rate) × Avg Loss) / Avg Win
  - Use 25% Kelly for safety (0.25 × Kelly %)
  - Recalculate weekly based on last 30 trades
  
- [ ] Fallback to fixed fractional if insufficient data
  - Need minimum 20 trades for Kelly calculation
  - Default to 1% risk if < 20 trades

**Deliverable:** Bot has institutional-grade risk controls, won't blow up account

---

### **PHASE 4: Adaptive Optimization + ML Learning** (Week 5-6)
**Goal:** Self-optimizing parameters with AI/ML learning capabilities

#### 4.1 Traditional Walk-Forward Optimization (2 days)
- [ ] Create `ParameterOptimizer` class
  - Monthly re-optimization of strategy parameters
  - Train on last 6 months, test on next month
  - Grid search over parameter ranges
  
- [ ] Parameter ranges per strategy:
  ```python
  bollinger_ranges = {
      'bb_period': [15, 20, 25],
      'bb_std': [1.5, 2.0, 2.5],
      'rsi_threshold': [35, 40, 45]
  }
  ```
  
- [ ] Optimization metrics
  - Optimize for Sharpe ratio (not just return)
  - Penalize high drawdown
  - Require minimum 10 trades in test period

#### 4.2 ML-Based Regime Classifier (3 days)
- [ ] Create `MLRegimeClassifier` using scikit-learn
  - **Features:** SMA slope, ATR ratio, VIX, volume, RSI, MACD
  - **Labels:** Bull, Bear, High Vol Choppy, Low Vol Range, Crisis
  - **Model:** RandomForestClassifier (proven, explainable)
  - Train on 2 years of SPY historical data
  
- [ ] Feature engineering
  - Rolling 20/50/200 day SMA slopes
  - ATR ratios (20d/100d)
  - Volume z-scores
  - Price momentum indicators
  
- [ ] Model validation
  - 80/20 train/test split
  - Cross-validation (5-fold)
  - Compare accuracy vs rule-based regime detector
  - Deploy if accuracy > 75%
  
- [ ] Integration
  - Drop-in replacement for `MarketRegimeDetector`
  - Save model to `/opt/quantshift/models/regime_classifier.pkl`
  - Retrain monthly with new data

#### 4.3 Strategy Performance Monitoring (1 day)
- [ ] Rolling 30-day metrics per strategy
  - Win rate, profit factor, Sharpe ratio
  - Compare to backtest expectations
  - Alert if performance degrades >20%
  
- [ ] Auto-disable underperforming strategies
  - Disable if win rate < 40% for 30 days
  - Disable if Sharpe < 0.5 for 30 days
  - Re-enable when backtest shows improvement
  
- [ ] ML model performance tracking
  - Track regime prediction accuracy
  - Compare ML vs rule-based regime detection
  - A/B test: 50% capital on ML, 50% on rules

**Deliverable:** Bot self-optimizes with traditional methods + ML regime prediction

---

### **PHASE 5: Dashboard & Monitoring** (Week 6)
**Goal:** Real-time visibility into bot performance and health

#### 5.1 Trading Pages Enhancement (2 days)
- [x] Trades page — DONE (bot filter tabs, exit reasons)
- [x] Positions page — DONE (bot badges, smart qty formatting)
- [x] Performance page — DONE (dark theme, bot filters)
- [ ] Add strategy breakdown to Performance page
  - P&L per strategy (Bollinger, RSI, Breakout)
  - Win rate per strategy
  - Active positions per strategy
- [ ] Add regime indicator to Dashboard
  - Current regime badge (bull/bear/high vol/low vol/crisis)
  - Regime history chart (last 30 days)
  - Strategy allocation by regime

#### 5.2 Real-Time Monitoring Dashboard (3 days)
- [ ] **Bot Health Section**
  - Last heartbeat timestamp
  - Uptime percentage
  - Error count (24h)
  - Current regime + active strategies
  - Portfolio heat gauge
  - Correlation warnings
  
- [ ] **Strategy Performance Section**
  - P&L per strategy (today, week, month, all-time)
  - Win rate per strategy
  - Sharpe ratio per strategy
  - Active positions per strategy
  - Strategy status (active/disabled/paused)
  
- [ ] **Risk Metrics Section**
  - Current portfolio heat (% of max)
  - Max drawdown from peak
  - Distance to circuit breakers (visual gauge)
  - Daily P&L vs daily loss limit
  - Open position count vs max positions
  
- [ ] **Market Regime Section**
  - Current regime with confidence score
  - Trend indicator (50-day SMA slope)
  - Volatility indicator (ATR ratio)
  - Market breadth (% stocks above 200-day MA)
  - VIX level

#### 5.3 Admin Control Center (3 days)
- [ ] **Settings Page**
  - Email configuration (Gmail + custom SMTP)
  - Platform settings (name, version)
  - Notification preferences
  - Test email functionality
  - Save/load from database
  
- [ ] **Session Management**
  - Active sessions list
  - User activity tracking
  - Session termination
  - IP address + user agent display
  - Last activity timestamps
  
- [ ] **Audit Logs Viewer**
  - System activity log
  - Filterable by user/action/date
  - Searchable
  - Exportable to CSV
  - Actions: login/logout, settings changes, trades, etc.

#### 5.4 Alerting System (2 days)
- [ ] **Email Alerts**
  - Circuit breaker triggered
  - Strategy disabled due to poor performance
  - Regime change detected
  - Daily P&L summary (configurable time)
  - Weekly performance report
  - Bot crash/restart
  - API connection failures
  
- [ ] **Alert Configuration UI**
  - Enable/disable alert types
  - Set alert thresholds
  - Add email recipients
  - Alert frequency settings
  - Test alert functionality

#### 5.5 System Operations (2 days)
- [ ] **Health Monitor Dashboard**
  - Database connection status + latency
  - API response times
  - Memory usage
  - CPU usage
  - Disk space
  - Bot service status
  
- [ ] **API Status Dashboard**
  - Endpoint health monitoring
  - Response time tracking
  - Error rate monitoring
  - Uptime statistics
  - External API status (Alpaca, Yahoo Finance)
  
- [ ] **Bot Controls**
  - Start/stop bot from UI
  - Restart bot
  - Emergency kill switch
  - Manual trade execution (admin only)
  - Position force-close (admin only)

**Deliverable:** Full visibility into bot operations, proactive alerts, admin control center

---

### **PHASE 6: Sentiment Analysis Integration** (Week 7)
**Goal:** Add news/social sentiment as signal filter and risk indicator

#### 6.1 Sentiment Data Pipeline (2 days)
- [ ] Create `SentimentAnalyzer` class
  - **News API:** NewsAPI.org or Alpha Vantage
  - **Social:** Twitter/X API (optional)
  - **Model:** FinBERT (pre-trained financial sentiment)
  
- [ ] Data collection
  - Fetch news for traded symbols (SPY, QQQ, etc.)
  - Analyze sentiment: Positive, Negative, Neutral
  - Calculate sentiment score (-1 to +1)
  - Store in `sentiment_data` table
  
- [ ] Real-time sentiment updates
  - Fetch news every 15 minutes
  - Cache results to avoid API limits
  - Track sentiment changes over time

#### 6.2 Sentiment-Based Signal Filtering (2 days)
- [ ] Signal enhancement rules
  - **Block BUY** if sentiment < -0.3 (very negative)
  - **Boost confidence** if sentiment aligns with signal
  - **Reduce position size** if sentiment conflicts
  
- [ ] Sentiment-regime interaction
  - Crisis regime + negative sentiment = halt trading
  - Bull regime + positive sentiment = increase allocation
  - Track sentiment accuracy vs actual price moves
  
- [ ] Dashboard integration
  - Show current sentiment for each symbol
  - Sentiment history chart (7-day trend)
  - Sentiment vs price correlation

#### 6.3 Sentiment Model Validation (1 day)
- [ ] Backtest with sentiment data
  - Compare returns with vs without sentiment filter
  - Measure false positive reduction
  - Validate sentiment improves Sharpe ratio
  
- [ ] A/B testing framework
  - 50% capital uses sentiment, 50% doesn't
  - Track performance difference
  - Deploy full sentiment if improvement > 5%

**Deliverable:** Bot uses AI sentiment analysis to filter bad trades and boost good ones

---

### **PHASE 7: Deep Reinforcement Learning Agent** (Week 8-10)
**Goal:** AI agent learns optimal position sizing and trade timing

#### 7.1 RL Environment Setup (3 days)
- [ ] Create `TradingEnvironment` (OpenAI Gym compatible)
  - **State:** Price, volume, indicators, positions, account balance
  - **Actions:** Buy (size 0-100%), Sell (size 0-100%), Hold
  - **Reward:** Sharpe ratio over rolling 30-day window
  
- [ ] Environment features
  - Historical price data (OHLCV)
  - Technical indicators (RSI, MACD, BB)
  - Current regime (from ML classifier)
  - Current sentiment score
  - Portfolio state (positions, P&L, risk)
  
- [ ] Reward shaping
  - Positive reward for profitable trades
  - Penalty for drawdown
  - Bonus for high Sharpe ratio
  - Penalty for excessive trading (transaction costs)

#### 7.2 RL Agent Training (5 days)
- [ ] Model selection: **PPO** (Proximal Policy Optimization)
  - Library: Stable-Baselines3
  - Proven for trading applications
  - Handles continuous action spaces
  
- [ ] Training pipeline
  - Train on 2 years of SPY historical data
  - Validate on 6 months of held-out data
  - Hyperparameter tuning (learning rate, batch size, etc.)
  - Track training metrics (reward, episode length, loss)
  
- [ ] Model checkpointing
  - Save best model based on validation Sharpe
  - Version models by date
  - Store in `/opt/quantshift/models/rl_agent_v{date}.zip`

#### 7.3 RL Agent Integration (3 days)
- [ ] Create `RLPositionSizer` class
  - Load trained RL model
  - Use for position sizing decisions
  - Override traditional position sizing
  
- [ ] Hybrid approach (safety first)
  - Traditional strategies generate signals
  - RL agent decides position size
  - Risk manager validates final decision
  - Fallback to fixed sizing if RL fails
  
- [ ] Paper trading validation
  - Run RL agent in paper trading for 2 weeks
  - Compare to traditional position sizing
  - Deploy to live if Sharpe improves by >10%
  
- [ ] Continuous learning
  - Retrain RL agent monthly with new data
  - Track performance degradation
  - Auto-rollback if performance drops

#### 7.4 RL Monitoring & Explainability (2 days)
- [ ] RL metrics dashboard
  - Current policy performance
  - Action distribution (buy/sell/hold %)
  - Average position sizes by regime
  - Reward trends over time
  
- [ ] Explainability tools
  - SHAP values for action decisions
  - Feature importance visualization
  - Action heatmaps by market condition
  - Confidence scores per decision
  
- [ ] Safety controls
  - Max position size limits (RL can't exceed)
  - Emergency override (admin can disable RL)
  - Automatic fallback if RL behaves erratically

**Deliverable:** Deep RL agent optimizes position sizing, learns from market continuously

---

### **PHASE 8: Production Validation & Go-Live** (Week 11-12)
**Goal:** Comprehensive testing before live trading decision

#### 8.1 Integration Testing (3 days)
- [ ] Test all strategies simultaneously
- [ ] Test regime transitions (rule-based + ML)
- [ ] Test circuit breakers (simulate losses)
- [ ] Test correlation limits
- [ ] Test parameter optimization
- [ ] Test sentiment filtering
- [ ] Test RL agent position sizing
- [ ] Stress test with volatile market data

#### 8.2 Performance Validation (5 days)
- [ ] Run full system in paper trading for 2 weeks
- [ ] Verify all strategies generating signals
- [ ] Verify ML regime detection working correctly
- [ ] Verify sentiment analysis filtering bad trades
- [ ] Verify RL agent position sizing
- [ ] Verify risk limits enforced
- [ ] Compare paper results to backtest expectations

#### 8.3 Go-Live Checklist (2 days)
- [ ] All phases 1-7 complete and tested
- [ ] Paper trading shows positive results (Sharpe > 1.5)
- [ ] All circuit breakers tested
- [ ] Monitoring and alerting working
- [ ] Emergency kill switch tested
- [ ] ML models validated and performing
- [ ] RL agent outperforming traditional sizing
- [ ] Alpaca live API credentials configured
- [ ] Final review and approval

**Deliverable:** Production-ready system, decision to go live or continue paper trading

---

## 📋 Current Backlog (Deferred)

### 🔴 Critical — Bot Production Path

#### Phase 0: Paper Trading Reset (Do First)
- [x] SSH to bot container and check process status — DONE (effort: S)
- [x] Fix positions duplicate key bug — DONE (effort: S)
- [x] Wire trade recording to strategy cycle — DONE (effort: S)
- [x] Find root cause of Feb 13 runaway SPY bug — legacy bot service (effort: S) — DONE 2026-02-21
- [x] Stop legacy `alpaca-trader-million.service` (effort: S) — DONE 2026-02-21
- [x] Reset Alpaca paper account (effort: S) — DONE 2026-02-21
- [ ] Monitor for first real MA crossover signal + DB trade record (effort: S)
- [ ] Go/no-go decision by Mar 21, 2026 (effort: S)

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
None currently identified.

### Non-Critical (Backlog)

#### Bug: Coinbase `get_products()` API hangs indefinitely
- **Severity:** Medium (workaround in place)
- **Impact:** Cannot dynamically fetch crypto symbols from Coinbase API
- **Workaround:** Using curated top-50 crypto list (same symbols API would return)
- **Root Cause:** Coinbase REST client `get_products()` call hangs, no timeout support
- **Fix Plan (Phase 2):** 
  - Evaluate alternative: CoinGecko API for crypto symbol ranking
  - Or: Implement proper async/timeout wrapper for Coinbase API
  - Or: Use different Coinbase endpoint with better reliability
- **Tracked in:** D-QS-013
- **Date Identified:** 2026-02-25

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
