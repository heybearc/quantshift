# QuantShift Current State Documentation
**Last Updated:** December 26, 2025

## Alpaca Paper Trading Account

**Account Status:**
- **Account Balance:** $99,796.61
- **Total Equity:** $99,796.61
- **Buying Power:** $199,593.22 (2x leverage available)
- **Portfolio Value:** $99,796.61
- **Open Positions:** 0
- **Unrealized P&L:** $0.00
- **Pattern Day Trader:** No
- **Day Trade Count:** 0/3

**Account Configuration:**
- **API Key ID:** PKUNCOV2CO3Y7XBI47CWOPCTBX
- **API Base URL:** https://paper-api.alpaca.markets
- **Trading Mode:** Paper Trading
- **Account Type:** Paper (Simulated)

## Previous Trading Activity

**Crypto Positions (Now Closed):**
- Previously held BTCUSD and AAVEUSD positions
- These were crypto assets traded through Alpaca
- Account has been reset/positions closed
- Starting fresh for equity trading

## Infrastructure Status

**Bot Deployment:**
- **Primary Container:** LXC 100 (10.92.3.27) - Running
- **Standby Container:** LXC 101 (10.92.3.28) - Not configured
- **Dashboard Container:** LXC 137 (10.92.3.29) - Running
- **Database:** PostgreSQL on 10.92.3.21
- **Redis:** Running on 10.92.3.27

**Bot Status:**
- **Equity Bot:** Running (monitoring only, no trading logic)
- **Crypto Bot:** Not deployed
- **Dashboard:** Operational, showing live data

**Current Bot Behavior:**
- Fetches account data every 60 seconds
- Sends heartbeat every 30 seconds
- Syncs trades to database every 5 minutes
- **Does NOT execute trades** - monitoring only

## Configuration Files

**Existing:**
- `/opt/quantshift/apps/bots/equity/run_bot.py` - Bot runner
- `/opt/quantshift/packages/core/src/quantshift_core/state_manager.py` - State management
- `/opt/quantshift/apps/bots/equity/alpaca_trading/core/strategy.py` - Strategy implementation

**New (Created Today):**
- `config/equity_strategy.yaml` - Strategy configuration
- `IMPLEMENTATION_ROADMAP.md` - Development roadmap
- `CURRENT_STATE.md` - This file

## Strategy Implementation Status

**Existing Strategy Code:**
- Moving Average Crossover (MA 20/50)
- ATR-based position sizing
- Stop loss and take profit logic
- Volume confirmation
- Weekly trend confirmation
- Support/resistance filters

**Status:** Strategy code exists but NOT integrated with bot
- Strategy is in `alpaca_trading/core/strategy.py`
- Bot in `run_bot.py` only monitors, doesn't trade
- Need to integrate strategy execution into bot loop

## Next Steps (Phase 0)

1. ✅ Create strategy configuration file
2. ✅ Document current account state
3. ⏳ Update bot to use stock symbols (SPY, QQQ, AAPL)
4. ⏳ Remove crypto asset references
5. ⏳ Test configuration
6. ⏳ Prepare for backtesting (Phase 1)

## Capital Allocation Plan

**Paper Trading:**
- Current: $99,796.61 available
- Will use for validation testing
- No real money at risk

**Live Trading (Future):**
- Expected Capital: $10,000
- Risk per trade: 2% ($200)
- Max positions: 5
- Max portfolio heat: 10% ($1,000)

## Risk Management Settings

**Per Trade:**
- Risk: 2% of capital
- Stop loss: ATR-based (2x ATR)
- Take profit: 2:1 reward-to-risk
- Position size: Calculated based on ATR

**Portfolio Level:**
- Max positions: 5
- Max portfolio heat: 10%
- Max daily loss: 5% (circuit breaker)
- Max drawdown: 15% (circuit breaker)

## Validation Requirements

**Before Live Trading:**
1. Backtest on 2+ years of data
2. Sharpe ratio > 1.5
3. Max drawdown < 15%
4. Win rate > 50%
5. 30 days paper trading validation
6. No critical bugs or execution failures

## Known Issues

1. **Bot Configuration:** Equity bot previously trading crypto assets
2. **No Trading Logic:** Bot only monitors, doesn't execute trades
3. **Strategy Integration:** Strategy code exists but not integrated
4. **No Backtesting:** Strategy not validated with historical data
5. **No Performance Tracking:** No historical metrics available

## Timeline

**Phase 0 (Today):** Configuration and cleanup
**Phase 1 (This Week):** Backtesting and validation
**Phase 2 (Next Week):** Strategy integration
**Phase 3 (Week 3):** Enhanced risk management
**Phase 4 (Weeks 4-7):** Paper trading validation
**Live Trading:** ~2 months from now (if validation successful)
