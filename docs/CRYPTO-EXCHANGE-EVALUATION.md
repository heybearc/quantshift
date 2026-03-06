# Crypto Exchange API Evaluation & Recommendations

**Date:** 2026-03-06  
**Purpose:** Evaluate crypto exchanges for algorithmic trading with shorting capability

---

## Executive Summary

**Current:** Coinbase Advanced Trade API (no shorting, spot only)  
**Recommendation:** **Kraken** for US-based trading with margin/futures shorting  
**Alternative:** Binance.com (non-US) if you can access it

### Quick Comparison

| Exchange | Shorting | API Quality | Fees | US Access | Recommendation |
|----------|----------|-------------|------|-----------|----------------|
| **Kraken** | ✅ Margin + Futures | ⭐⭐⭐⭐⭐ | Low | ✅ Yes | **Best for US** |
| Coinbase | ❌ Spot only | ⭐⭐⭐⭐ | High | ✅ Yes | Current (limited) |
| Binance.us | ❌ Spot only | ⭐⭐⭐ | Medium | ✅ Yes | Not recommended |
| Binance.com | ✅ Full margin/futures | ⭐⭐⭐⭐⭐ | Lowest | ❌ No | Best (if accessible) |

---

## Detailed Analysis

### 1. Kraken ⭐ RECOMMENDED FOR US

**Why Kraken is the Best Choice:**

**Shorting Capabilities:**
- ✅ **Margin Trading:** Up to 5× leverage on spot markets
- ✅ **Perpetual Futures:** Up to 50× leverage (use cautiously)
- ✅ **Tokenized Equity Futures:** New in 2026, regulated
- ✅ **Both long and short positions**

**API Quality:**
- ✅ Excellent REST API documentation
- ✅ WebSocket support for real-time data
- ✅ Python SDK available
- ✅ Rate limits: 15-20 requests/second (generous)
- ✅ Historical data access
- ✅ Order types: Market, Limit, Stop-Loss, Stop-Limit, Take-Profit

**Trading Fees:**
- **Maker:** 0.16% (volume-based, can go down to 0%)
- **Taker:** 0.26% (volume-based, can go down to 0.10%)
- **Futures:** 0.02% maker / 0.05% taker
- **Much lower than Coinbase**

**Asset Coverage:**
- 200+ cryptocurrencies
- Major pairs: BTC, ETH, SOL, ADA, DOT, MATIC, etc.
- Fiat support: USD, EUR, GBP, CAD, JPY

**US Compliance:**
- ✅ Fully regulated in the US
- ✅ Available in all 50 states (with some restrictions)
- ✅ Proper licensing and compliance

**API Endpoints:**
```python
# Kraken API Example
from krakenex import API

# Place short order with margin
api.query_private('AddOrder', {
    'pair': 'XXBTZUSD',
    'type': 'sell',
    'ordertype': 'market',
    'volume': '0.1',
    'leverage': '2'  # 2x leverage for short
})

# Futures API
from kraken_futures import KrakenFutures
futures = KrakenFutures()
futures.place_order(
    symbol='PI_XBTUSD',
    side='sell',  # Short
    size=1000,
    order_type='lmt',
    limit_price=68000
)
```

**Pros:**
- ✅ Full shorting capability (margin + futures)
- ✅ Excellent API for algo trading
- ✅ Lower fees than Coinbase
- ✅ US-compliant and regulated
- ✅ Strong security track record
- ✅ Good liquidity on major pairs
- ✅ Advanced order types
- ✅ Instant margining system

**Cons:**
- ⚠️ UI less beginner-friendly than Coinbase
- ⚠️ Margin trading requires verification
- ⚠️ Futures have higher risk (but optional)

---

### 2. Coinbase Advanced Trade (CURRENT)

**Current Status:**
- ✅ What we're using now
- ❌ **No shorting capability** (spot trading only)
- ❌ No margin trading
- ❌ No futures

**API Quality:**
- ✅ Good REST API
- ✅ WebSocket support
- ✅ Python SDK (coinbase-advanced-py)
- ⚠️ Rate limits: More restrictive than Kraken
- ✅ Stop-limit orders supported (we implemented this)

**Trading Fees:**
- **Maker:** 0.40% (volume-based)
- **Taker:** 0.60% (volume-based)
- **Higher than competitors**

**Asset Coverage:**
- 250+ cryptocurrencies
- Good selection of major coins
- Strong fiat on/off ramps

**Pros:**
- ✅ Already integrated
- ✅ US-compliant
- ✅ Strong brand reputation
- ✅ Good security
- ✅ Easy fiat deposits

**Cons:**
- ❌ **No shorting** (deal breaker for your use case)
- ❌ Higher fees
- ❌ Limited to spot trading
- ❌ No leverage options

**Verdict:** Good for spot trading, but **insufficient for shorting strategies**.

---

### 3. Binance.us

**Status:** Not recommended

**Shorting Capabilities:**
- ❌ **No margin trading** (removed in 2023)
- ❌ **No futures** (removed in 2023)
- ❌ Spot trading only

**Why Not Binance.us:**
- Regulatory issues in the US
- Features stripped down compared to Binance.com
- Uncertain future due to SEC actions
- Limited functionality

**Verdict:** Avoid. Worse than Coinbase with no advantages.

---

### 4. Binance.com (Non-US)

**If you could access it (VPN/offshore entity):**

**Shorting Capabilities:**
- ✅ Full margin trading (up to 10×)
- ✅ Perpetual futures (up to 125×)
- ✅ Coin-margined futures
- ✅ Options trading
- ✅ Most advanced shorting tools

**API Quality:**
- ✅ Best-in-class API
- ✅ Extensive documentation
- ✅ Multiple SDKs
- ✅ WebSocket streams
- ✅ Highest rate limits

**Trading Fees:**
- **Spot:** 0.10% maker/taker (lowest in industry)
- **Futures:** 0.02% maker / 0.04% taker
- **Volume discounts with BNB**

**Asset Coverage:**
- 500+ cryptocurrencies
- Deepest liquidity
- Most trading pairs

**Pros:**
- ✅ Best API in the industry
- ✅ Lowest fees
- ✅ Most advanced features
- ✅ Highest liquidity
- ✅ Best for algo trading

**Cons:**
- ❌ **Not available to US residents**
- ❌ Regulatory uncertainty
- ❌ Risk of account closure if detected

**Verdict:** Best exchange globally, but **not accessible for US-based trading**.

---

### 5. Other Exchanges Worth Mentioning

**Bybit:**
- ✅ Excellent futures trading
- ✅ Good API
- ❌ Not US-compliant
- Use case: Non-US algo traders

**OKX:**
- ✅ Strong derivatives platform
- ✅ Good API
- ❌ Limited US access
- Use case: International traders

**dYdX:**
- ✅ Decentralized perpetuals
- ✅ No KYC
- ⚠️ Different architecture (blockchain-based)
- Use case: DeFi-native strategies

---

## Recommendation: Migrate to Kraken

### Why Kraken is the Right Choice

1. **Shorting Capability:** Full margin and futures support
2. **US Compliance:** Fully regulated, no legal risk
3. **API Quality:** Excellent for algorithmic trading
4. **Lower Fees:** 0.16%/0.26% vs Coinbase's 0.40%/0.60%
5. **Advanced Features:** Stop-loss, take-profit, trailing stops
6. **Liquidity:** Good on major pairs
7. **Security:** Strong track record

### Migration Path

**Phase 1: Setup (1-2 hours)**
- Create Kraken account
- Complete KYC verification
- Enable margin trading (requires additional verification)
- Generate API keys
- Fund account

**Phase 2: Integration (4-6 hours)**
- Create `KrakenExecutor` class (similar to `CoinbaseExecutor`)
- Implement margin trading methods
- Add short position support
- Test on Kraken testnet (if available) or small amounts
- Update `crypto_config.yaml` with Kraken settings

**Phase 3: Testing (1-2 days)**
- Deploy to STANDBY bot
- Run parallel with Coinbase bot
- Verify margin orders work
- Test short positions
- Monitor for issues

**Phase 4: Production (1 hour)**
- Switch PRIMARY bot to Kraken
- Disable Coinbase bot or keep for spot-only
- Monitor performance

**Estimated Total Time:** 1 week including testing

---

## API Comparison: Coinbase vs Kraken

### Order Placement

**Coinbase (Current):**
```python
# Spot buy only
order = coinbase_client.create_order(
    product_id='BTC-USD',
    side='BUY',
    order_configuration={
        'market_market_ioc': {
            'base_size': '0.01'
        }
    }
)
```

**Kraken (Proposed):**
```python
# Margin short
order = kraken_api.query_private('AddOrder', {
    'pair': 'XXBTZUSD',
    'type': 'sell',      # Short
    'ordertype': 'market',
    'volume': '0.01',
    'leverage': '2',     # 2x margin
    'validate': False
})

# Futures short
futures_order = kraken_futures.place_order(
    symbol='PI_XBTUSD',
    side='sell',         # Short
    size=100,
    order_type='mkt'
)
```

### Stop Orders

**Both support stop-limit orders** (we already implemented for Coinbase)

---

## Cost Analysis

### Trading $10,000/day volume

**Coinbase:**
- Maker: $40/day (0.40%)
- Taker: $60/day (0.60%)
- **Monthly: $1,200 - $1,800**

**Kraken:**
- Maker: $16/day (0.16%)
- Taker: $26/day (0.26%)
- **Monthly: $480 - $780**

**Savings with Kraken: $720 - $1,020/month** (40-57% reduction)

---

## Risk Considerations

### Margin Trading Risks
- ⚠️ Leverage amplifies both gains and losses
- ⚠️ Liquidation risk if position moves against you
- ⚠️ Funding rates on perpetual futures
- ⚠️ Requires careful position sizing

### Mitigation Strategies
- ✅ Start with low leverage (2-3×)
- ✅ Use trailing stops (already implemented)
- ✅ Strict position limits
- ✅ Monitor margin levels
- ✅ Emergency stop functionality (already have)

### Recommended Leverage Limits
- **Conservative:** 2× leverage max
- **Moderate:** 3-5× leverage max
- **Aggressive:** 10× leverage max (not recommended for algo)
- **Never:** >10× leverage (too risky)

---

## Implementation Checklist

### Before Migration
- [ ] Research Kraken margin requirements
- [ ] Understand liquidation mechanics
- [ ] Review Kraken API documentation
- [ ] Test API with small amounts
- [ ] Update risk management for margin

### During Migration
- [ ] Create `KrakenExecutor` class
- [ ] Add margin trading methods
- [ ] Implement short position logic
- [ ] Update database schema (if needed)
- [ ] Add Kraken-specific config
- [ ] Test thoroughly on STANDBY

### After Migration
- [ ] Monitor margin levels
- [ ] Track liquidation risk
- [ ] Compare performance vs Coinbase
- [ ] Optimize leverage settings
- [ ] Document lessons learned

---

## Conclusion

**Recommendation: Migrate to Kraken**

**Reasons:**
1. ✅ Enables shorting strategies (your primary goal)
2. ✅ Lower fees (40-57% savings)
3. ✅ Better API for algo trading
4. ✅ US-compliant and regulated
5. ✅ Advanced order types
6. ✅ Good liquidity

**Timeline:** 1 week for full migration with testing

**Risk:** Low - Kraken is established, regulated, and has good API

**Alternative:** Keep Coinbase for spot-only strategies, add Kraken for margin/shorting

---

## Next Steps

1. **Decision:** Approve Kraken migration
2. **Account Setup:** Create Kraken account, complete KYC
3. **Development:** Build `KrakenExecutor` (4-6 hours)
4. **Testing:** Deploy to STANDBY, test with small amounts
5. **Production:** Switch PRIMARY bot to Kraken

**Estimated Cost:** $0 development (we do it), ~$100 in test trades

**Estimated Benefit:** $720-1,020/month in fee savings + shorting capability

---

## Questions to Consider

1. **Leverage:** What max leverage are you comfortable with? (Recommend 2-3×)
2. **Capital Split:** Keep some on Coinbase for spot, some on Kraken for margin?
3. **Timeline:** When do you want to start shorting? (Can be ready in 1 week)
4. **Risk Tolerance:** Comfortable with margin liquidation risk?

Let me know your thoughts and we can proceed with implementation.
