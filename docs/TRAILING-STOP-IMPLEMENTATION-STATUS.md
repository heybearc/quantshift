# Trailing Stop-Loss Implementation Status

**Date:** 2026-03-06 12:30 PM EST  
**Status:** Phase 1 Complete - Integration Pending  
**Priority:** HIGH

---

## Implementation Progress

### ✅ Phase 1: Core Infrastructure (COMPLETE)

**Files Created:**
1. `packages/core/src/quantshift_core/position_tracker.py` (220 lines)
   - PositionTracker dataclass for tracking position state
   - High water mark tracking
   - Trailing stop calculation logic
   - Stop update validation

2. `packages/core/src/quantshift_core/trailing_stop_manager.py` (350 lines)
   - TrailingStopManager class for position monitoring
   - Position update loop (every 30 seconds)
   - Broker API integration for stop order updates
   - Database persistence

3. `apps/bots/migrations/add_trailing_stop_columns.sql`
   - Database schema updates for positions table
   - Columns: high_water_mark, trailing_stop_active, current_stop_loss, stop_order_id, take_profit_order_id, last_stop_update
   - Indexes for performance

**Files Modified:**
1. `packages/core/src/quantshift_core/executors/alpaca_executor.py`
   - Added `place_stop_order()` method
   - Added `cancel_order()` method

2. `config/equity_config.yaml`
   - Added trailing_stops configuration section
   - Parameters: enabled, activation_threshold_pct, trail_distance_atr_mult, etc.

---

### ⏳ Phase 2: Integration (IN PROGRESS)

**Remaining Tasks:**

1. **Database Writer Methods** (30 minutes)
   - Add `update_position_trailing_stop()` to database_writer.py
   - Add `get_open_positions_with_trailing_stops()` to database_writer.py
   - Update position sync to include trailing stop fields

2. **Main Bot Integration** (1 hour)
   - Import TrailingStopManager in run_bot_v3.py
   - Initialize TrailingStopManager with config
   - Add position tracking when signals execute
   - Add trailing stop update loop (every 30 seconds)
   - Fetch current prices and ATR values
   - Call trailing_stop_manager.update_positions()

3. **Database Migration** (15 minutes)
   - Run migration on PRIMARY bot container (CT 100)
   - Run migration on STANDBY bot container (CT 101)
   - Verify columns added successfully

---

### 🧪 Phase 3: Testing (PENDING)

**Test Plan:**

1. **Unit Tests**
   - Test PositionTracker high water mark updates
   - Test trailing stop price calculations
   - Test stop update validation logic

2. **Integration Tests**
   - Deploy to STANDBY (BLUE web container)
   - Open test position manually
   - Monitor logs for trailing stop updates
   - Verify stop orders being placed/cancelled in Alpaca
   - Verify database updates

3. **Paper Trading Validation** (24-48 hours)
   - Monitor existing positions (WFC, EL)
   - Verify trailing stops activate after +1% gain
   - Verify stops adjust as price moves
   - Check for any API errors or failures

---

### 🚀 Phase 4: Production Deployment (PENDING)

**Deployment Steps:**

1. Merge to main branch
2. Deploy to PRIMARY bot container (CT 100)
3. Run database migration
4. Restart bot service
5. Monitor first few trailing stop updates
6. Verify no order placement errors
7. Document in release notes

---

## Configuration

**Current Settings (equity_config.yaml):**
```yaml
trailing_stops:
  enabled: true
  activation_threshold_pct: 0.01     # Activate after +1% gain
  trail_distance_atr_mult: 1.5       # Trail 1.5×ATR below high
  min_trail_distance_pct: 0.005      # Minimum 0.5% trail
  update_frequency_seconds: 30       # Update every 30 seconds
  only_improve_stop: true            # Never worsen stop
```

---

## How It Works

### 1. Position Entry
- Strategy generates BUY signal with stop_loss and take_profit
- AlpacaExecutor places bracket order (entry + SL + TP)
- TrailingStopManager.add_position() called with stop_order_id
- PositionTracker created: high_water_mark = entry_price

### 2. Position Monitoring (Every 30 seconds)
- TrailingStopManager.update_positions() called
- For each open position:
  - Fetch current price
  - Update high water mark if price increased
  - Check if trailing stop should activate (+1% gain threshold)
  - If active: calculate new trailing stop price
  - If new stop is better: cancel old stop, place new stop
  - Update database with new state

### 3. Trailing Stop Activation
- Triggers when: (high_water_mark - entry_price) / entry_price >= 1%
- Example: Entry $78.41, activates at $79.20 (+1%)

### 4. Trailing Stop Calculation
```python
trail_distance = max(
    atr * 1.5,                    # ATR-based distance
    high_water_mark * 0.005       # Minimum 0.5% distance
)
new_stop = high_water_mark - trail_distance
```

### 5. Stop Update
- Only updates if new_stop > current_stop (improves position)
- Cancels existing stop order via Alpaca API
- Places new stop order at updated price
- Logs update with locked profit amount
- Persists to database

---

## Example: WFC Position

**Current State (Static Stop):**
```
Entry: $78.41
Current: $80.31 (+2.53%, +$613)
Stop: $75.41 (static, never moved)
Risk: Could lose entire $613 gain
```

**With Trailing Stop (After Implementation):**
```
Entry: $78.41
Current: $80.31
High Water Mark: $80.31
Trailing Stop: $79.11 (HWM - 1.5×ATR)
Locked Profit: $216 minimum

If price rises to $82:
  High Water Mark: $82.00
  Trailing Stop: $80.80
  Locked Profit: $739 minimum

If price rises to $85:
  High Water Mark: $85.00
  Trailing Stop: $83.80
  Locked Profit: $1,665 minimum
```

---

## Database Schema

**New Columns in `positions` table:**
```sql
high_water_mark DOUBLE PRECISION        -- Highest price reached
trailing_stop_active BOOLEAN            -- Whether trailing is active
current_stop_loss DOUBLE PRECISION      -- Current stop price
stop_order_id TEXT                      -- Alpaca stop order ID
take_profit_order_id TEXT               -- Alpaca TP order ID
last_stop_update TIMESTAMP              -- Last update time
```

---

## Next Steps

**Immediate (Today):**
1. Add database writer methods
2. Integrate into main bot loop
3. Run database migration
4. Test on STANDBY

**Short-term (This Week):**
1. Monitor paper trading for 24-48 hours
2. Verify trailing stops working correctly
3. Deploy to production
4. Update documentation

**Validation Criteria:**
- ✅ Trailing stops activate after +1% gain
- ✅ Stops adjust upward as price rises
- ✅ Stops never move downward (only improve)
- ✅ Database updates correctly
- ✅ No Alpaca API errors
- ✅ Logs show clear trailing stop activity

---

## Files Modified Summary

**Created (3 files):**
- `packages/core/src/quantshift_core/position_tracker.py`
- `packages/core/src/quantshift_core/trailing_stop_manager.py`
- `apps/bots/migrations/add_trailing_stop_columns.sql`

**Modified (2 files):**
- `packages/core/src/quantshift_core/executors/alpaca_executor.py`
- `config/equity_config.yaml`

**Pending (2 files):**
- `apps/bots/equity/database_writer.py` (add methods)
- `apps/bots/run_bot_v3.py` (integrate manager)

---

## Estimated Completion

**Remaining Effort:** 2-3 hours
- Database methods: 30 minutes
- Bot integration: 1 hour
- Migration + testing: 1-1.5 hours

**Target:** Complete by end of day (2026-03-06)

---

## Success Metrics

After deployment, we expect to see:
1. **Improved Win Rate:** 5-10% increase (fewer winners → losers)
2. **Better Sharpe Ratio:** 20-30% improvement
3. **Reduced Drawdowns:** 10-15% reduction
4. **Operational:** 2-5 stop updates per position per day, <1% API errors
