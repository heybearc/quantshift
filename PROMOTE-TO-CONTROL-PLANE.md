# Promotions to Control Plane

## Decision: AI/ML Retraining Frequency for Financial Markets
**Type:** decision
**Target:** DECISIONS.md
**Affects:** all trading/finance apps
**Date:** 2026-02-21

**Context:** Building ML regime classifier and RL agent for QuantShift trading platform. Initial plan suggested monthly retraining, but financial markets exhibit rapid concept drift.

**Discovery/Decision:** 
- **ML Models (Classification/Regression):** Weekly full retraining (not monthly)
- **RL Agents:** Daily online learning + weekly full retraining
- **Rationale:** Financial markets change in days, not months. Concept drift happens rapidly. Fresh data is more relevant than old data. Competitive edge requires fast adaptation.

**Implementation:**
- ML regime classifier: Weekly retraining on 2 years of data
- RL position sizer: Daily online learning from trades + weekly full retraining
- Continuous validation vs baseline performance
- Auto-rollback if performance degrades

**Impact:** All trading/finance AI/ML systems should adopt aggressive retraining schedules. Monthly retraining is too slow for financial markets.

**References:** QuantShift Phase 4-7 implementation

---

## Infrastructure: Multi-Layer AI Trading Platform Architecture
**Type:** infrastructure
**Target:** docs/infrastructure/ai-ml-trading-platform.md
**Affects:** trading/finance apps
**Date:** 2026-02-21

**Discovery:** Successfully implemented institutional-grade multi-layer AI trading platform with:

**Architecture Layers:**
1. **Traditional ML Layer** - RandomForest regime classifier (91.7% accuracy)
2. **Deep RL Layer** - PPO agent for position sizing with daily online learning
3. **NLP Layer** - FinBERT sentiment analysis for signal filtering

**Key Components:**
- `MLRegimeClassifier` - Market regime detection with 5 regimes
- `SentimentAnalyzer` - FinBERT-based news sentiment with caching
- `RLPositionSizer` - PPO agent with OpenAI Gym environment
- `StrategyOrchestrator` - Integrates all AI layers with fallback handling

**Design Patterns:**
- Fallback to rule-based if ML fails
- Configurable via YAML (can disable any layer)
- Backward compatible architecture
- Continuous validation vs baseline
- Auto-rollback safety mechanisms

**Retraining Schedule:**
- ML classifier: Weekly (2 years of data)
- RL agent: Daily online learning + weekly full retraining
- Sentiment: Real-time with 15-min caching

**Performance:**
- ML regime accuracy: 91.7% (93.3% ± 2.4% on 5-fold CV)
- Top features: ATR ratio, SMA slopes, MACD
- Sharpe ratio reward function for RL
- Transaction costs modeled (0.1% per trade)

**Deployment:**
- High availability failover ready
- Circuit breakers for risk management
- Real-time dashboard visualization
- Model versioning and rollback capability

**References:** QuantShift implementation (Phases 1-7)

---

## Documentation: AI/ML Best Practices for Trading Systems
**Type:** documentation
**Target:** docs/best-practices/ai-ml-trading.md
**Affects:** trading/finance apps
**Date:** 2026-02-21

**Discovery:** Key lessons learned from building production AI/ML trading platform:

**1. Retraining Frequency:**
- Financial markets exhibit rapid concept drift
- Weekly retraining minimum for classification/regression
- Daily online learning essential for RL agents
- Monthly retraining is too slow - markets change in days

**2. Hybrid Approach:**
- Combine traditional ML + Deep RL + NLP
- Each layer serves different purpose
- Fallback to rule-based if AI fails
- Validate continuously vs baseline

**3. Risk Management:**
- Circuit breakers at multiple levels
- Portfolio heat tracking
- Correlation limits
- Auto-rollback if performance degrades

**4. Production Readiness:**
- Model versioning and persistence
- Graceful degradation (fallback strategies)
- Real-time monitoring dashboards
- Comprehensive logging for debugging

**5. Feature Engineering:**
- ATR ratio (volatility normalization)
- SMA slopes (trend detection)
- MACD signals (momentum)
- Regime-based feature importance

**6. Reward Functions (RL):**
- Sharpe ratio over rolling window (not just returns)
- Transaction costs in environment
- Realistic trading simulation
- Risk-adjusted metrics

**7. Sentiment Analysis:**
- Use domain-specific models (FinBERT for finance)
- Cache results (15-min TTL)
- Fallback handling for API failures
- Filter signals, don't generate them

**References:** QuantShift AI/ML platform implementation
