# Trailing Stop-Loss Implementation Plan

**Priority:** HIGH ⚠️  
**Status:** CRITICAL GAP IDENTIFIED  
**Created:** 2026-03-06 12:07 PM EST

---

## Problem Statement

**Current system has static stop-loss only - no trailing stops.**

### What We Have
- ✅ Static stop-loss calculated at entry (ATR-based)
- ✅ Bracket orders placed with Alpaca
- ✅ Protection from catastrophic losses

### What We're Missing
- ❌ Continuous position monitoring
- ❌ High water mark tracking
- ❌ Stop-loss adjustment as price moves favorably
- ❌ Profit locking mechanism

### Impact
- Winners can turn into losers (give back all gains)
- Suboptimal risk-adjusted returns
- Not maximizing edge from winning trades

**Example:** WFC position currently +$613 (+2.53%), but if price reverses, we could lose entire gain plus hit original stop for a net loss.

---

## Design Specification

### 1. Trailing Stop Parameters

```yaml
risk_management:
  trailing_stops:
    enabled: true
    activation_threshold_pct: 1.0    # Activate after +1% gain
    trail_distance_atr_mult: 1.5     # Trail 1.5×ATR below high
    min_trail_distance_pct: 0.5      # Minimum 0.5% trail distance
    update_frequency_seconds: 30     # Check every 30 seconds
    only_improve_stop: true          # Never move stop against us
```

### 2. High Water Mark Tracking

**Data Structure:**
```python
@dataclass
class PositionTracker:
    symbol: str
    entry_price: float
    current_price: float
    quantity: float
    original_stop_loss: float
    current_stop_loss: float
    high_water_mark: float           # Highest price reached
    trailing_stop_active: bool       # Activated after threshold
    last_stop_update: datetime
    stop_order_id: str               # Alpaca stop order ID
```

### 3. Position Monitoring Loop

**Frequency:** Every 30 seconds (aligned with heartbeat)

**Logic:**
```python
def update_trailing_stops():
    for position in open_positions:
        # Get current price
        current_price = get_current_price(position.symbol)
        
        # Update high water mark
        if current_price > position.high_water_mark:
            position.high_water_mark = current_price
        
        # Check if trailing stop should activate
        gain_pct = (current_price - position.entry_price) / position.entry_price
        if gain_pct >= activation_threshold_pct:
            position.trailing_stop_active = True
        
        # Calculate new trailing stop
        if position.trailing_stop_active:
            atr = get_atr(position.symbol)
            new_stop = position.high_water_mark - (trail_distance_atr_mult * atr)
            
            # Only update if new stop is better (higher for long positions)
            if new_stop > position.current_stop_loss:
                update_stop_order(position, new_stop)
                position.current_stop_loss = new_stop
                log_stop_update(position)
```

### 4. Alpaca API Integration

**Replace Stop Order:**
```python
def update_stop_order(position: PositionTracker, new_stop_price: float):
    # Cancel existing stop order
    alpaca_client.cancel_order(position.stop_order_id)
    
    # Place new stop order at updated price
    new_stop_request = StopOrderRequest(
        symbol=position.symbol,
        qty=position.quantity,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.GTC,
        stop_price=round(new_stop_price, 2)
    )
    
    new_order = alpaca_client.submit_order(new_stop_request)
    position.stop_order_id = new_order.id
    
    logger.info(
        f"Trailing stop updated: {position.symbol} "
        f"${position.current_stop_loss:.2f} → ${new_stop_price:.2f} "
        f"(High: ${position.high_water_mark:.2f})"
    )
```

---

## Implementation Steps

### Phase 1: Core Infrastructure (2-3 hours)

1. **Create PositionTracker class**
   - File: `packages/core/src/quantshift_core/position_tracker.py`
   - Track high water mark, trailing stop state
   - Persist to database

2. **Add database columns**
   ```sql
   ALTER TABLE positions ADD COLUMN high_water_mark FLOAT;
   ALTER TABLE positions ADD COLUMN trailing_stop_active BOOLEAN DEFAULT FALSE;
   ALTER TABLE positions ADD COLUMN current_stop_loss FLOAT;
   ALTER TABLE positions ADD COLUMN stop_order_id TEXT;
   ```

3. **Create TrailingStopManager**
   - File: `packages/core/src/quantshift_core/trailing_stop_manager.py`
   - Position monitoring loop
   - Stop adjustment logic
   - Alpaca API integration

### Phase 2: Integration (1-2 hours)

4. **Integrate with AlpacaExecutor**
   - Store stop order ID after placing bracket orders
   - Initialize PositionTracker for each new position
   - Call TrailingStopManager in main bot loop

5. **Add configuration**
   - Update `config/equity_config.yaml`
   - Add trailing stop parameters
   - Make it toggleable (enable/disable)

### Phase 3: Testing (2-3 hours)

6. **Unit tests**
   - Test high water mark tracking
   - Test stop adjustment logic
   - Test Alpaca API calls (mocked)

7. **Paper trading validation**
   - Deploy to STANDBY
   - Monitor for 24-48 hours
   - Verify stops are adjusting correctly
   - Check logs for any issues

### Phase 4: Production Deployment (1 hour)

8. **Deploy to production**
   - Update both BLUE and GREEN
   - Monitor first few trailing stop updates
   - Verify no order placement errors

---

## Code Locations

### Files to Create
- `packages/core/src/quantshift_core/position_tracker.py` (new)
- `packages/core/src/quantshift_core/trailing_stop_manager.py` (new)

### Files to Modify
- `apps/bots/equity/alpaca_executor.py` - Store stop order IDs
- `apps/bots/run_bot_v3.py` - Add trailing stop manager to main loop
- `config/equity_config.yaml` - Add trailing stop config
- `packages/core/src/quantshift_core/executors/alpaca_executor.py` - Update stop orders
- Database migration script

---

## Configuration Example

```yaml
# config/equity_config.yaml

risk_management:
  # Existing settings...
  max_position_size: 0.05
  max_positions: 10
  
  # NEW: Trailing stop configuration
  trailing_stops:
    enabled: true                      # Enable trailing stops
    activation_threshold_pct: 0.01     # Activate after +1% gain
    trail_distance_atr_mult: 1.5       # Trail 1.5×ATR below high
    min_trail_distance_pct: 0.005      # Minimum 0.5% trail
    update_frequency_seconds: 30       # Update every 30 seconds
    only_improve_stop: true            # Never worsen stop
    
    # Strategy-specific overrides (optional)
    strategy_overrides:
      BreakoutMomentum:
        trail_distance_atr_mult: 2.0   # Wider trail for trends
      BollingerBounce:
        trail_distance_atr_mult: 1.0   # Tighter trail for mean reversion
```

---

## Example: WFC Position with Trailing Stop

**Current (Static Stop):**
```
Entry: $78.41
Current: $80.31 (+2.53%)
Stop: $75.41 (Entry - 2×ATR) ← NEVER MOVES
Risk: If reverses, lose $613 gain + hit stop = -$927 total
```

**With Trailing Stop:**
```
Entry: $78.41
Current: $80.31 (+2.53%)
High Water Mark: $80.31
Trailing Stop: $79.11 (High - 1.5×ATR)
Locked Profit: $216 minimum (if stopped out now)

If price rises to $82:
  High Water Mark: $82.00
  Trailing Stop: $80.80
  Locked Profit: $739 minimum

If price rises to $85:
  High Water Mark: $85.00
  Trailing Stop: $83.80
  Locked Profit: $1,665 minimum
```

**Benefit:** Locks in profits while letting winners run.

---

## Risk Considerations

### Potential Issues

1. **Over-trading / Whipsaws**
   - Tight trailing stops can get stopped out on normal volatility
   - **Mitigation:** Use ATR-based distance (adapts to volatility)

2. **API Rate Limits**
   - Updating stops every 30 seconds for multiple positions
   - **Mitigation:** Batch updates, respect Alpaca rate limits

3. **Order Rejection**
   - Stop order cancellation/replacement could fail
   - **Mitigation:** Retry logic, fallback to original stop

4. **Gap Risk**
   - Stops don't protect against overnight gaps
   - **Mitigation:** Already accepted risk, trailing stops don't worsen this

### Safety Measures

- ✅ Only improve stops (never move against us)
- ✅ Activation threshold prevents premature trailing
- ✅ Minimum trail distance prevents too-tight stops
- ✅ Persist state to database (survive bot restarts)
- ✅ Logging for all stop updates

---

## Success Metrics

**After implementation, we should see:**

1. **Improved Win Rate**
   - Fewer winners turning into losers
   - Target: 5-10% improvement in win rate

2. **Better Risk-Adjusted Returns**
   - Higher average win size
   - Lower average loss size (locked profits)
   - Target: 20-30% improvement in Sharpe ratio

3. **Reduced Drawdowns**
   - Profits locked in before reversals
   - Target: 10-15% reduction in max drawdown

4. **Operational Metrics**
   - Stop updates: 2-5 per position per day
   - API errors: <1% of update attempts
   - Latency: <2 seconds per update

---

## Timeline

**Total Effort:** 6-8 hours

- **Phase 1 (Core):** 2-3 hours
- **Phase 2 (Integration):** 1-2 hours
- **Phase 3 (Testing):** 2-3 hours
- **Phase 4 (Deploy):** 1 hour

**Recommended Schedule:**
- Day 1: Phase 1-2 (implementation)
- Day 2-3: Phase 3 (testing on STANDBY)
- Day 4: Phase 4 (production deployment)

---

## References

**Existing Implementations:**
- `equity/backtest/strategy_breakout_momentum.py:136-139` - Backtest trailing stop
- `equity/alpaca_trading/challenges/million_dollar_trader.py:631-648` - Challenge bot trailing stop
- `packages/core/src/quantshift_core/strategies/breakout_momentum.py:189-196` - Strategy-level trailing logic

**Alpaca API Documentation:**
- Order replacement: https://alpaca.markets/docs/api-references/trading-api/orders/
- Stop orders: https://alpaca.markets/docs/trading/orders/#stop-order

---

## Next Steps

1. **Immediate:** Update safety verification report to note this gap
2. **Short-term:** Implement trailing stops (this week)
3. **Medium-term:** Monitor performance improvement
4. **Long-term:** Consider advanced trailing methods (parabolic SAR, chandelier exit)

---

## Conclusion

**Trailing stop-loss is a CRITICAL missing feature** that significantly impacts risk-adjusted returns. Current static stops protect from catastrophic losses but don't optimize profit capture.

**Recommendation:** Implement trailing stops before increasing position sizes or going live with real capital.

**Priority:** HIGH - Should be implemented within 1 week.
