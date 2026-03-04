# Dual-Bot Feature Parity Checklist

**Purpose:** Ensure all safety features are implemented consistently across both equity and crypto bots.

**Last Updated:** 2026-03-04

---

## Bot Architecture

Both bots use the **same unified code** (`run_bot_v3.py`) but different executors:

- **Equity Bot:** Uses `AlpacaExecutor` (Alpaca API)
- **Crypto Bot:** Uses `CoinbaseExecutor` (Coinbase Advanced Trade API)

**Critical Rule:** Any feature added to one executor MUST be added to the other.

---

## Feature Parity Matrix

| Feature | AlpacaExecutor | CoinbaseExecutor | Status |
|---------|----------------|------------------|--------|
| `execute_signal()` | ✅ | ✅ | Complete |
| `close_position()` | ✅ | ✅ | Complete |
| `get_positions()` | ✅ | ✅ | Complete |
| `get_account()` | ✅ | ✅ | Complete |
| `is_market_open()` | ✅ | ✅ | Complete |
| **Bracket Orders** | ✅ Atomic | ✅ Pattern | Complete |
| **Emergency Stop** | ✅ | ✅ | Complete |
| **Risk/Reward Logging** | ✅ | ✅ | Complete |

---

## Phase 1.5 Safety Features - Verification

### ✅ Phase 1.5.1: Emergency Kill Switch

**Shared Code (run_bot_v3.py):**
- ✅ `_check_emergency_stop()` - checks Redis flag
- ✅ `_execute_emergency_stop()` - closes all positions
- ✅ 100ms response time
- ✅ Position backup to Redis
- ✅ Database clearing
- ✅ Cache clearing

**Executor-Specific (must exist in both):**
- ✅ `AlpacaExecutor.close_position()` - market sell orders
- ✅ `CoinbaseExecutor.close_position()` - market sell orders

**Differences:**
- Equity: Only works during market hours (9:30 AM - 4:00 PM EST)
- Crypto: Works 24/7 (crypto markets always open)

### ✅ Phase 1.5.2: Bracket Orders

**AlpacaExecutor:**
- ✅ Uses `OrderClass.BRACKET` (native Alpaca feature)
- ✅ Truly atomic - all 3 orders in one API call
- ✅ Risk/reward calculation and logging

**CoinbaseExecutor:**
- ✅ Bracket order pattern (sequential submission)
- ✅ Entry → wait for fill → SL → TP
- ✅ Protection status tracking (fully_protected, partial, unprotected)
- ✅ Risk/reward calculation and logging

**Differences:**
- Alpaca: Atomic (broker-guaranteed)
- Coinbase: Best-effort (~1-2 second window)

---

## Verification Checklist

Before marking any feature complete, verify:

- [ ] Feature implemented in `AlpacaExecutor`
- [ ] Feature implemented in `CoinbaseExecutor`
- [ ] Same method signature (if applicable)
- [ ] Same logging format
- [ ] Same error handling
- [ ] Tested on equity bot
- [ ] Tested on crypto bot
- [ ] Documentation updated
- [ ] TASK-STATE.md updated

---

## Future Features - Dual-Bot Checklist

When implementing new features, follow this process:

### 1. Design Phase
- [ ] Identify if feature is executor-specific or shared
- [ ] Document differences between Alpaca and Coinbase APIs
- [ ] Plan implementation for both executors

### 2. Implementation Phase
- [ ] Implement in `AlpacaExecutor`
- [ ] Implement in `CoinbaseExecutor`
- [ ] Verify method signatures match
- [ ] Verify logging format matches

### 3. Testing Phase
- [ ] Test equity bot on standby
- [ ] Test crypto bot on standby
- [ ] Verify logs show same information
- [ ] Test emergency scenarios

### 4. Documentation Phase
- [ ] Update this checklist
- [ ] Update TASK-STATE.md
- [ ] Update IMPLEMENTATION-PLAN.md
- [ ] Create runbook if needed

---

## Common Pitfalls

### ❌ What NOT to Do
- Implement feature in one executor only
- Assume both APIs work the same way
- Skip testing on both bots
- Forget to update documentation

### ✅ What TO Do
- Always implement in both executors
- Research API differences first
- Test both bots thoroughly
- Document differences clearly

---

## API Differences Reference

### Order Submission

**Alpaca:**
```python
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderClass

order = MarketOrderRequest(
    symbol=symbol,
    qty=qty,
    side=OrderSide.BUY,
    order_class=OrderClass.BRACKET,
    stop_loss={'stop_price': sl_price},
    take_profit={'limit_price': tp_price}
)
```

**Coinbase:**
```python
order_config = {
    'product_id': symbol,
    'side': 'BUY',
    'order_configuration': {
        'market_market_ioc': {
            'base_size': str(qty)
        }
    }
}
response = client.market_order(**order_config)
```

### Position Closure

**Alpaca:**
```python
order = MarketOrderRequest(
    symbol=symbol,
    qty=qty,
    side=OrderSide.SELL,
    time_in_force=TimeInForce.DAY
)
```

**Coinbase:**
```python
order_config = {
    'product_id': symbol,
    'side': 'SELL',
    'order_configuration': {
        'market_market_ioc': {
            'base_size': str(qty)
        }
    }
}
```

---

## Executor Method Inventory

### Required Methods (Both Executors)

| Method | Purpose | AlpacaExecutor | CoinbaseExecutor |
|--------|---------|----------------|------------------|
| `__init__()` | Initialize executor | ✅ | ✅ |
| `execute_signal()` | Execute trading signal | ✅ | ✅ |
| `close_position()` | Close position (emergency stop) | ✅ | ✅ |
| `get_positions()` | Fetch open positions | ✅ | ✅ |
| `get_account()` | Fetch account info | ✅ | ✅ |
| `is_market_open()` | Check if market is open | ✅ | ✅ |
| `get_market_data()` | Fetch price data | ✅ | ✅ |

### Optional Helper Methods

| Method | Purpose | AlpacaExecutor | CoinbaseExecutor |
|--------|---------|----------------|------------------|
| `_wait_for_fill()` | Wait for order fill | ✅ | ✅ |
| `_place_stop_loss_order()` | Place SL order | ✅ | ✅ |
| `_place_take_profit_order()` | Place TP order | ✅ | ✅ |

---

## Maintenance

This document should be updated:
- After implementing any new feature
- After discovering API differences
- After fixing bugs in one executor
- Monthly review for accuracy

**Owner:** Development Team  
**Review Frequency:** Monthly or after major changes
