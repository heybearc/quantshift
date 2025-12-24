# Phase 2: Multi-Strategy Framework - Usage Guide

## Overview

Phase 2 adds a multi-strategy framework to the QuantShift trading system:
1. **Three Trading Strategies** - MA Crossover, Mean Reversion, Breakout
2. **Strategy Manager** - Capital allocation and performance tracking
3. **Consensus Signals** - Multiple strategies voting on trades

All strategies are in `quantshift-core` and automatically inherited by both equity and crypto bots.

---

## 🎯 **Three Strategies Implemented**

### **1. Moving Average Crossover**
**Capital Allocation:** 33% (default)

**Entry Signals:**
- **Buy:** Fast MA (20) crosses above Slow MA (50) - "Golden Cross"
- **Sell:** Fast MA crosses below Slow MA - "Death Cross"
- **Filter:** RSI not overbought/oversold

**Risk Management:**
- Stop Loss: 2x ATR below entry
- Take Profit: 3x ATR above entry

**Best For:** Trending markets

---

### **2. Mean Reversion**
**Capital Allocation:** 33% (default)

**Entry Signals:**
- **Buy:** RSI < 30 (oversold) + Price below lower Bollinger Band
- **Sell:** RSI > 70 (overbought) + Price above upper Bollinger Band

**Risk Management:**
- Stop Loss: Below lower Bollinger Band
- Take Profit: Middle Bollinger Band (mean)

**Best For:** Range-bound markets

---

### **3. Breakout**
**Capital Allocation:** 34% (default)

**Entry Signals:**
- **Buy:** Price breaks above resistance + Volume 1.5x average + ADX > 25
- **Sell:** Price breaks below support + Volume confirmation + ADX > 25

**Risk Management:**
- Stop Loss: 2.5x ATR below entry
- Take Profit: 5x ATR above entry

**Best For:** High volatility, strong trends

---

## 📊 **Using the Strategy Manager**

### **Basic Setup**

```python
from quantshift_core import (
    StrategyManager,
    MovingAverageCrossover,
    MeanReversion,
    Breakout
)

# Initialize strategies with capital allocation
strategies = [
    MovingAverageCrossover(capital_allocation=0.40),  # 40% of capital
    MeanReversion(capital_allocation=0.30),           # 30% of capital
    Breakout(capital_allocation=0.30)                 # 30% of capital
]

# Initialize strategy manager
manager = StrategyManager(
    strategies=strategies,
    account_balance=10000.0,
    max_positions=10
)
```

### **Generate Signals from All Strategies**

```python
# Get signals from all strategies
signals = manager.generate_signals(
    symbol="AAPL",
    data=current_df,
    daily_data=daily_df,
    hourly_data=hourly_df
)

# signals = {
#     "MA_Crossover": Signal.BUY,
#     "Mean_Reversion": Signal.HOLD,
#     "Breakout": Signal.BUY
# }

print(f"MA Crossover: {signals['MA_Crossover']}")
print(f"Mean Reversion: {signals['Mean_Reversion']}")
print(f"Breakout: {signals['Breakout']}")
```

### **Get Consensus Signal**

```python
# Require majority consensus (>50%)
consensus = manager.get_consensus_signal(signals)

if consensus == Signal.BUY:
    print("✅ Consensus: BUY - Majority of strategies agree")
elif consensus == Signal.SELL:
    print("✅ Consensus: SELL - Majority of strategies agree")
else:
    print("⏸️ No consensus - Strategies disagree")
```

### **Execute Trade with Strategy Manager**

```python
# If consensus to buy
if consensus == Signal.BUY:
    # Pick the strategy that generated the signal
    # (or use the one with best recent performance)
    strategy = strategies[0]  # MA Crossover
    
    # Calculate position details
    entry_price = current_df['close'].iloc[-1]
    stop_loss = strategy.calculate_stop_loss(entry_price, current_df)
    take_profit = strategy.calculate_take_profit(entry_price, current_df)
    
    # Calculate position size
    shares = manager.calculate_position_size(
        symbol="AAPL",
        strategy=strategy,
        entry_price=entry_price,
        stop_loss=stop_loss
    )
    
    if shares > 0:
        # Open position
        manager.open_position(
            symbol="AAPL",
            strategy=strategy,
            entry_price=entry_price,
            quantity=shares,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        print(f"✅ Position opened: {shares} shares @ ${entry_price:.2f}")
```

### **Monitor and Close Positions**

```python
# Update positions with current prices
market_prices = {"AAPL": 152.50, "MSFT": 380.00}
manager.update_positions(market_prices)

# Check if any stops hit
to_close = manager.check_stops(market_prices)

for symbol, exit_price, reason in to_close:
    manager.close_position(symbol, exit_price, reason)
    print(f"Position closed: {symbol} @ ${exit_price:.2f} ({reason})")
```

---

## 📈 **Strategy Performance Tracking**

### **Get Performance by Strategy**

```python
# Get performance metrics for all strategies
performance = manager.get_strategy_performance()

for perf in performance:
    print(f"\n{perf['strategy']}:")
    print(f"  Total Trades: {perf['total_trades']}")
    print(f"  Win Rate: {perf['win_rate']:.2f}%")
    print(f"  Profit Factor: {perf['profit_factor']:.2f}")
    print(f"  Total P&L: ${perf['total_pnl']:.2f}")
```

### **Automatic Rebalancing**

```python
# Rebalance capital allocations based on performance
# Increases allocation to winning strategies
manager.rebalance_allocations()

# Check new allocations
for strategy in strategies:
    print(f"{strategy.name}: {strategy.capital_allocation * 100:.1f}%")
```

### **Portfolio Summary**

```python
# Get complete portfolio summary
summary = manager.get_portfolio_summary()

print(f"Total Positions: {summary['total_positions']}")
print(f"Unrealized P&L: ${summary['total_unrealized_pnl']:.2f}")
print(f"\nPositions by Strategy:")
for strategy, count in summary['strategy_positions'].items():
    print(f"  {strategy}: {count} positions")
```

---

## 🔧 **Customizing Strategies**

### **Adjust Strategy Parameters**

```python
# Customize MA Crossover
ma_strategy = MovingAverageCrossover(
    capital_allocation=0.40,
    fast_period=10,      # Faster MA (default: 20)
    slow_period=30,      # Faster MA (default: 50)
    atr_multiplier=1.5   # Tighter stops (default: 2.0)
)

# Customize Mean Reversion
mr_strategy = MeanReversion(
    capital_allocation=0.30,
    rsi_period=21,           # Longer RSI (default: 14)
    rsi_oversold=25,         # More extreme (default: 30)
    rsi_overbought=75,       # More extreme (default: 70)
    bb_std=2.5               # Wider bands (default: 2.0)
)

# Customize Breakout
breakout_strategy = Breakout(
    capital_allocation=0.30,
    lookback_period=30,      # Longer lookback (default: 20)
    volume_multiplier=2.0,   # Higher volume requirement (default: 1.5)
    atr_multiplier=3.0       # Wider stops (default: 2.5)
)
```

---

## 💡 **Complete Trading Bot Example**

```python
from quantshift_core import (
    StrategyManager,
    MovingAverageCrossover,
    MeanReversion,
    Breakout,
    Signal
)

class MultiStrategyBot:
    def __init__(self, account_balance: float):
        # Initialize strategies
        strategies = [
            MovingAverageCrossover(capital_allocation=0.40),
            MeanReversion(capital_allocation=0.30),
            Breakout(capital_allocation=0.30)
        ]
        
        # Initialize manager
        self.manager = StrategyManager(
            strategies=strategies,
            account_balance=account_balance,
            max_positions=10
        )
    
    def run_trading_cycle(self, symbols: list, market_data: dict):
        """Run one trading cycle."""
        
        # 1. Update existing positions
        current_prices = {s: market_data[s]['current']['close'].iloc[-1] 
                         for s in symbols}
        self.manager.update_positions(current_prices)
        
        # 2. Check stops
        to_close = self.manager.check_stops(current_prices)
        for symbol, exit_price, reason in to_close:
            self.manager.close_position(symbol, exit_price, reason)
        
        # 3. Generate signals for new positions
        for symbol in symbols:
            if symbol in self.manager.positions:
                continue  # Already have position
            
            # Get signals from all strategies
            signals = self.manager.generate_signals(
                symbol=symbol,
                data=market_data[symbol]['current'],
                daily_data=market_data[symbol]['daily'],
                hourly_data=market_data[symbol]['hourly']
            )
            
            # Get consensus
            consensus = self.manager.get_consensus_signal(signals)
            
            if consensus == Signal.BUY:
                # Find best performing strategy
                performance = self.manager.get_strategy_performance()
                best_strategy = max(performance, 
                                  key=lambda x: x['win_rate'] * x['profit_factor'])
                
                # Get strategy instance
                strategy = next(s for s in self.manager.strategies 
                              if s.name == best_strategy['strategy'])
                
                # Calculate position details
                entry_price = current_prices[symbol]
                stop_loss = strategy.calculate_stop_loss(
                    entry_price, 
                    market_data[symbol]['current']
                )
                take_profit = strategy.calculate_take_profit(
                    entry_price,
                    market_data[symbol]['current']
                )
                
                # Calculate position size
                shares = self.manager.calculate_position_size(
                    symbol, strategy, entry_price, stop_loss
                )
                
                if shares > 0:
                    self.manager.open_position(
                        symbol, strategy, entry_price, 
                        shares, stop_loss, take_profit
                    )
        
        # 4. Rebalance allocations periodically (e.g., weekly)
        # self.manager.rebalance_allocations()
        
        # 5. Get portfolio summary
        return self.manager.get_portfolio_summary()

# Usage
bot = MultiStrategyBot(account_balance=10000.0)
summary = bot.run_trading_cycle(
    symbols=["AAPL", "MSFT", "GOOGL"],
    market_data=your_market_data
)
print(summary)
```

---

## 🎯 **Strategy Selection Logic**

### **When Each Strategy Works Best**

| Market Condition | Best Strategy | Why |
|-----------------|---------------|-----|
| **Strong Uptrend** | MA Crossover | Rides the trend |
| **Strong Downtrend** | MA Crossover | Catches reversals |
| **Range-Bound** | Mean Reversion | Profits from oscillations |
| **High Volatility** | Breakout | Catches big moves |
| **Low Volatility** | Mean Reversion | Small consistent gains |

### **Consensus Voting**

**Majority Rule (>50%):**
- 2 out of 3 strategies agree → Execute trade
- 1 out of 3 strategies → No trade (wait for consensus)

**Example:**
```
MA Crossover: BUY
Mean Reversion: BUY
Breakout: HOLD
→ Consensus: BUY (2/3 agree)
```

---

## 📊 **Expected Performance Improvements**

| Metric | Single Strategy | Multi-Strategy | Improvement |
|--------|----------------|----------------|-------------|
| Win Rate | 59% | 65-70% | +6-11% |
| Profit Factor | 1.5 | 2.0-2.5 | +33-67% |
| Max Drawdown | 25% | 15-20% | -20-40% |
| Consistency | Variable | More stable | Better |

**Why Multi-Strategy is Better:**
- ✅ Diversification reduces risk
- ✅ Different strategies work in different conditions
- ✅ Consensus reduces false signals
- ✅ Performance-based rebalancing optimizes allocation

---

## 🚀 **Next Steps**

1. ✅ Phase 2 deployed to standby (LXC 101)
2. ⏳ Test with paper trading (1-2 weeks)
3. ⏳ Compare to single-strategy performance
4. ⏳ Deploy to primary (LXC 100)
5. ⏳ Deploy crypto bot (inherits all 3 strategies automatically)

---

## 📝 **Integration with Existing Bot**

Your existing bot can easily adopt the multi-strategy framework:

```python
# Old way (single strategy)
if ma_crossover_signal():
    buy()

# New way (multi-strategy)
manager = StrategyManager(strategies, account_balance)
signals = manager.generate_signals(symbol, data, daily_data, hourly_data)
consensus = manager.get_consensus_signal(signals)
if consensus == Signal.BUY:
    # Manager handles position sizing and risk management
    manager.execute_trade(...)
```

Both equity and crypto bots automatically get all three strategies from `quantshift-core`.
