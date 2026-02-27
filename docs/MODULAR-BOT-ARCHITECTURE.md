# QuantShift Modular Bot Architecture

**Last Updated:** 2026-02-27  
**Status:** Implemented and Running in Production

---

## 🎯 Architecture Vision

**Goal:** Build a resilient, scalable trading bot with independent, loosely-coupled components that can be developed, tested, and deployed independently.

**Key Principles:**
1. **Strategy Independence:** Each strategy is self-contained and pluggable
2. **Loose Coupling:** Components communicate through well-defined interfaces
3. **Single Responsibility:** Each component has one clear purpose
4. **Observable:** All components emit structured logs and metrics
5. **Testable:** Each component can be tested in isolation

---

## 📊 Current Architecture (As Implemented)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Bot Core (run_bot_v3.py)                    │
│                                                                     │
│  Responsibilities:                                                  │
│  • Primary/Standby failover coordination                           │
│  • Heartbeat & health monitoring (30s interval)                    │
│  • Database connection management (PostgreSQL)                     │
│  • Prometheus metrics collection & HTTP server                     │
│  • Redis state management integration                              │
│  • Main event loop (60s trading cycles)                            │
│                                                                     │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    ┌────▼────────┐    ┌────▼──────────────────────────────────┐
    │  Executor   │    │      StrategyOrchestrator             │
    │  (Alpaca/   │    │                                       │
    │  Coinbase)  │    │  Responsibilities:                    │
    │             │    │  • Multi-strategy coordination        │
    │ Responsi-   │    │  • Capital allocation (33/33/34)      │
    │ bilities:   │    │  • Signal aggregation                 │
    │ • Market    │    │  • Conflict resolution                │
    │   data      │    │  • Regime-based adaptation            │
    │ • Order     │    │  • Risk management integration        │
    │   execution │    │  • Sentiment analysis filtering       │
    │ • Position  │    │                                       │
    │   tracking  │    └────┬──────────────────────────────────┘
    │ • Account   │         │
    │   info      │         │ Strategies (Pluggable Modules)
    └────┬────────┘         │
         │            ┌─────┴──────┬──────────┬──────────────┐
         │            │            │          │              │
         │       ┌────▼─────┐ ┌───▼────┐ ┌──▼─────────┐ ┌──▼────────┐
         │       │Bollinger │ │  RSI   │ │ Breakout   │ │    MA     │
         │       │  Bounce  │ │  Mean  │ │ Momentum   │ │ Crossover │
         │       │ Strategy │ │Reversion│ │ Strategy   │ │ Strategy  │
         │       │          │ │Strategy │ │            │ │(inactive) │
         │       │ 33% cap  │ │ 33% cap│ │  34% cap   │ │           │
         │       └────┬─────┘ └───┬────┘ └──┬─────────┘ └───────────┘
         │            │           │          │
         │            └───────────┼──────────┘
         │                        │
         │                  ┌─────▼──────────┐
         │                  │    Signals     │
         │                  │   (with meta)  │
         │                  │                │
         │                  │  Each signal:  │
         │                  │  • strategy    │
         │                  │  • regime      │
         │                  │  • sentiment   │
         │                  │  • stop_loss   │
         │                  │  • take_profit │
         │                  └─────┬──────────┘
         │                        │
         └────────────────────────▼
                          Execute Orders
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼────┐  ┌───▼─────┐  ┌──▼──────────────┐
              │ Position │  │  Redis  │  │   Performance   │
              │ Database │  │  State  │  │     Tracker     │
              │ (Postgres)│  │ Manager │  │ (strategy_perf) │
              └──────────┘  └─────────┘  └─────────────────┘
```

---

## 🔧 Component Details

### 1. Bot Core (`run_bot_v3.py`)
**Purpose:** Orchestrate all components and manage bot lifecycle

**Responsibilities:**
- Initialize all subsystems (executor, strategies, orchestrator, metrics)
- Run main event loop (60-second trading cycles)
- Manage primary/standby failover via Redis
- Send heartbeats to database (30-second interval)
- Collect and expose Prometheus metrics (port 9200/9201)
- Handle graceful shutdown and error recovery

**Key Methods:**
- `_init_executor()` - Initialize broker connection
- `_init_strategies()` - Load strategies from config
- `_init_state_manager()` - Connect to Redis
- `run()` - Main event loop
- `send_heartbeat()` - Update database with bot status

**Configuration:** `config/equity_config.yaml` or `config/crypto_config.yaml`

---

### 2. StrategyOrchestrator (`strategy_orchestrator.py`)
**Purpose:** Coordinate multiple strategies and aggregate signals

**Responsibilities:**
- Load and manage multiple strategy instances
- Allocate capital per strategy (configurable percentages)
- Aggregate signals from all active strategies
- Resolve conflicts (multiple strategies signaling same symbol)
- Apply regime-based risk adjustments
- Filter signals via sentiment analysis
- Tag signals with strategy metadata

**Key Features:**
- **Capital Allocation:** 33% Bollinger, 33% RSI, 34% Breakout
- **Regime Detection:** ML classifier adjusts allocation dynamically
- **Risk Management:** Portfolio-level limits enforced
- **Sentiment Analysis:** FinBERT filtering for signal quality

**Configuration:**
```yaml
orchestrator:
  capital_allocation:
    BollingerBounce: 0.33
    RSIMeanReversion: 0.33
    BreakoutMomentum: 0.34
  use_regime_detection: true
  use_ml_regime: true
  use_risk_management: true
  use_sentiment_analysis: true
```

---

### 3. Strategy Modules (Pluggable)

#### BaseStrategy Interface
All strategies implement this interface:
```python
class BaseStrategy:
    def generate_signals(
        self, 
        market_data: Dict[str, pd.DataFrame],
        account: Account,
        positions: List[Position]
    ) -> List[Signal]:
        """Generate trading signals based on market data"""
        pass
```

#### Active Strategies

**BollingerBounce** (`bollinger_bounce.py`)
- Entry: Price touches lower Bollinger Band + RSI < 45
- Exit: Price reaches upper Bollinger Band OR stop loss
- Stop Loss: 1.5×ATR below entry
- Backtest: 58.6% WR
- **Status:** Active (33% capital)

**RSIMeanReversion** (`rsi_mean_reversion.py`)
- Entry: RSI < 35 (oversold)
- Exit: RSI > 65 (overbought)
- Stop Loss: 2.0×ATR, Take Profit: 3.0×ATR
- Backtest: 57.5% WR, 16.82% return, 1.99x profit factor
- **Status:** Active (33% capital)

**BreakoutMomentum** (`breakout_momentum.py`)
- Entry: Price breaks 20-day high + volume > 1.5x average
- Exit: Trailing stop at 1.5×ATR OR price breaks 10-day low
- Risk: 1% per trade, 3:1 reward-risk ratio
- **Status:** Active (34% capital)

**MACrossoverStrategy** (`ma_crossover.py`)
- Entry: Fast MA crosses above slow MA (golden cross)
- Exit: Fast MA crosses below slow MA (death cross)
- **Status:** Implemented but inactive (can be enabled via config)

---

### 4. Executor (`alpaca_executor.py` / `coinbase_executor.py`)
**Purpose:** Interface with broker APIs for market data and order execution

**Responsibilities:**
- Fetch market data (bars, quotes, positions)
- Execute orders (market, limit, stop)
- Place stop-loss and take-profit orders
- Track account balance and buying power
- Manage position lifecycle
- Check market hours (equity only)

**Key Methods:**
- `get_market_data()` - Fetch historical bars for symbols
- `execute_signal()` - Convert signal to order and execute
- `get_positions()` - Fetch current open positions
- `get_account()` - Get account balance and equity
- `is_market_open()` - Check if market is open for trading

---

### 5. State Manager (`state_manager.py`)
**Purpose:** Manage bot state in Redis for failover and recovery

**Responsibilities:**
- Store position data in Redis (24-hour TTL)
- Track bot heartbeat (60-second TTL)
- Manage primary/standby lock (30-second TTL)
- Load state on failover
- Handle read-only Redis replica gracefully

**Key Methods:**
- `save_position()` - Store position with strategy metadata
- `load_positions()` - Retrieve all positions from Redis
- `is_primary()` - Check if this bot should be primary
- `heartbeat()` - Update Redis heartbeat timestamp

**Failover Logic:**
- Primary bot holds Redis lock (30s TTL)
- Standby bot checks lock every 5 seconds
- If lock expires, standby promotes to primary
- State loaded from Redis on promotion

---

### 6. Risk Manager (`risk_manager.py`)
**Purpose:** Enforce portfolio-level risk limits

**Responsibilities:**
- Track total portfolio heat (max 10%)
- Monitor position correlation (max 0.7)
- Enforce sector exposure limits (max 30%)
- Implement circuit breakers (5% daily loss, 15% max drawdown)
- Reduce position sizes in high-risk conditions

**Key Features:**
- **Portfolio Heat:** Sum of all position risks ≤ 10%
- **Correlation Limits:** Block correlated positions
- **Sector Limits:** Max 30% in any sector
- **Circuit Breakers:** Halt trading on excessive losses

**Configuration:**
```yaml
risk_management:
  max_portfolio_heat: 0.10
  max_position_correlation: 0.7
  max_sector_exposure: 0.30
  daily_loss_limit: 0.05
  max_drawdown_limit: 0.15
```

---

### 7. ML Regime Classifier (`ml_regime_classifier.py`)
**Purpose:** Detect market regime and adjust strategy allocation

**Responsibilities:**
- Classify market into 5 regimes (Bull, Bear, High Vol, Low Vol, Range)
- Calculate features (ATR ratio, SMA slopes, MACD, RSI, volume)
- Predict regime using RandomForest (91.7% accuracy)
- Adjust strategy allocation based on regime
- Apply risk multipliers per regime

**Regime Types:**
- **Bull Trending:** Favor breakout strategies
- **Bear Trending:** Reduce exposure, tighter stops
- **High Volatility:** Favor mean reversion
- **Low Volatility:** Favor breakout
- **Range-Bound:** Favor Bollinger Bounce

**Training:**
- Weekly retraining (Sundays 2 AM UTC)
- 5-fold cross-validation: 93.3% ± 2.4%
- Model versioning (keep last 3 versions)

---

### 8. Sentiment Analyzer (`sentiment_analyzer.py`)
**Purpose:** Filter signals based on news sentiment

**Responsibilities:**
- Fetch news for symbols (NewsAPI, Alpaca News)
- Analyze sentiment using FinBERT
- Boost/penalty signal confidence based on sentiment
- Filter signals with negative sentiment
- Cache sentiment scores (1-hour TTL)

**Integration:**
- Integrated into StrategyOrchestrator
- Applied before signal execution
- Metadata added to signals

---

### 9. Performance Tracker (`strategy_performance_tracker.py`)
**Purpose:** Track per-strategy performance metrics

**Responsibilities:**
- Update `strategy_performance` table after each trade
- Calculate win rate, P&L, Sharpe ratio, profit factor
- Track avg win/loss, largest win/loss
- Calculate max drawdown per strategy
- Maintain peak equity for drawdown calculation

**Metrics Tracked:**
- Total trades, winning trades, losing trades
- Win rate percentage
- Total P&L (dollars and percentage)
- Average win, average loss
- Largest win, largest loss
- Sharpe ratio, profit factor
- Max drawdown, current drawdown

**Status:** Infrastructure complete, needs bot integration

---

### 10. Metrics Collector (`metrics.py`)
**Purpose:** Expose Prometheus metrics for monitoring

**Responsibilities:**
- Start HTTP server for metrics endpoint (port 9200/9201)
- Track bot health metrics (heartbeat, cycle duration, errors)
- Track business metrics (portfolio value, P&L, positions, signals)
- Expose metrics in Prometheus format

**Metrics Exposed:**
- `quantshift_heartbeat_seconds` - Last heartbeat timestamp
- `quantshift_cycle_duration_seconds` - Trading cycle duration
- `quantshift_portfolio_value_usd` - Current portfolio value
- `quantshift_daily_pnl_usd` - Daily P&L
- `quantshift_positions_open` - Number of open positions
- `quantshift_signals_generated_total` - Signals by strategy
- `quantshift_orders_executed_total` - Orders executed

---

## 🔄 Data Flow

### Trading Cycle Flow (Every 60 Seconds)

1. **Bot Core** checks if primary and market is open
2. **Executor** fetches market data for all symbols
3. **StrategyOrchestrator** calls each strategy's `generate_signals()`
4. Each **Strategy** analyzes data and returns signals
5. **StrategyOrchestrator** aggregates signals and tags with metadata
6. **ML Regime Classifier** adjusts signals based on regime
7. **Sentiment Analyzer** filters signals based on news
8. **Risk Manager** validates signals against portfolio limits
9. **Executor** executes approved signals
10. **State Manager** saves positions to Redis
11. **Bot Core** syncs positions to PostgreSQL database
12. **Metrics Collector** updates Prometheus metrics

### Heartbeat Flow (Every 30 Seconds)

1. **Bot Core** triggers heartbeat
2. **Executor** fetches account info and positions
3. Calculate total unrealized P&L from positions
4. Update `bot_status` table in PostgreSQL
5. **State Manager** updates Redis heartbeat
6. **Metrics Collector** updates Prometheus metrics

### Failover Flow (On Primary Failure)

1. **Standby Bot** detects primary heartbeat timeout (> 60s)
2. **State Manager** attempts to acquire Redis lock
3. If successful, **Standby Bot** promotes to PRIMARY
4. **State Manager** loads positions from Redis
5. **Bot Core** resumes trading cycles
6. **Metrics Collector** updates status to PRIMARY

---

## 🎯 Modularity Benefits Achieved

### 1. **Strategy Independence**
- ✅ New strategies can be added without modifying existing code
- ✅ Each strategy has its own file and configuration
- ✅ Strategies don't know about each other
- ✅ Easy to enable/disable strategies via config

### 2. **Loose Coupling**
- ✅ Components communicate through well-defined interfaces
- ✅ StrategyOrchestrator doesn't know strategy internals
- ✅ Executor doesn't know about strategies
- ✅ Easy to swap implementations (Alpaca ↔ Coinbase)

### 3. **Single Responsibility**
- ✅ Each component has one clear job
- ✅ Bot Core: lifecycle management
- ✅ Strategies: signal generation
- ✅ Executor: order execution
- ✅ Risk Manager: risk enforcement

### 4. **Observable**
- ✅ All components emit structured logs (structlog)
- ✅ Prometheus metrics for monitoring
- ✅ Grafana dashboards for visualization
- ✅ Database tracking for historical analysis

### 5. **Testable**
- ✅ Each strategy can be backtested independently
- ✅ Components can be unit tested in isolation
- ✅ Integration tests verify multi-strategy operation
- ⏳ Comprehensive test suite (deferred to Phase 5)

---

## 📈 Production Status

**Current Deployment:**
- **Primary Bot:** CT 100 (10.92.3.27) - ACTIVE
- **Standby Bot:** CT 101 (10.92.3.28) - HOT STANDBY
- **Strategies Active:** 3 (BollingerBounce, RSIMeanReversion, BreakoutMomentum)
- **Open Positions:** 14 with strategy attribution
- **Live P&L:** $1,785.63 (as of Feb 27, 6:41 AM)
- **Monitoring:** Prometheus + Grafana on CT 150 (10.92.3.2)

**Advanced Features Active:**
- ✅ ML Regime Detection (91.7% accuracy)
- ✅ Risk Management (10% max portfolio heat)
- ✅ Sentiment Analysis (FinBERT)
- ✅ Automated Failover (primary/standby)
- ✅ Performance Tracking (infrastructure ready)

---

## 🚀 Next Steps

### Immediate (Phase 1 Completion)
- [ ] Integrate StrategyPerformanceTracker into bot trade execution
- [ ] Verify per-strategy metrics are being tracked
- [ ] Test performance page displays strategy breakdown

### Future Enhancements
- [ ] Dashboard regime indicator visualization
- [ ] Email alerts for circuit breakers
- [ ] Kelly Criterion position sizing
- [ ] Comprehensive unit test suite
- [ ] Parameter optimization framework

---

## 📚 Related Documentation

- **Implementation Plan:** `IMPLEMENTATION-PLAN.md`
- **Deployment Status:** `docs/DEPLOYMENT-STATUS.md`
- **Risk Management:** `docs/RISK-MANAGEMENT-SYSTEM.md`
- **ML Lifecycle:** `docs/ML_LIFECYCLE_MANAGEMENT.md`
- **Redis Failover:** `docs/REDIS-FAILOVER-PROCEDURE.md`

---

**Last Review:** 2026-02-27  
**Reviewed By:** Cascade AI  
**Status:** Architecture implemented and running in production
