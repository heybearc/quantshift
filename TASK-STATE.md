# QuantShift Task State

**Last updated:** 2026-10-13  
**Current branch:** main  
**Working on:** Phase 1.5.9 paper validation — day 1 of the window that started 2026-10-13

---

## Current Task
**Phase 1.5.9 paper validation** — clock restarted 2026-10-13. The prior window failed must-pass checks: crypto had no stored stops, and equity was over its 10-position cap.

Crypto paper cash starts at $10,000. Kraken paper cash starts at $5,000 and stays in simulation. Alpaca paper equity is the broker account after the old book was closed. It was not rewritten to $100,000. Do not start live capital. Window runs through about 2026-11-10.

### What I'm doing right now
The three bots are running on `8ad01c1`. Crypto holds 3 positions, all with stops. Kraken holds 2 positions, both with stops. Equity was flattened at the open on 2026-10-13 after shorts appeared, then it opened 6 new longs. Those equity rows still have no stop stored in the database.

Public https://quantshift.io is still green LIVE on v1.13.3 (`5b715db`). The regime page, the −1.27% drawdown, and the Kraken optimization row are on blue standby from `0a6d733`. They have not been switched live.

### Recent completions
- ✅ Restarted the paper window on 2026-10-13 (`1f247ec`, `8ad01c1`)
- ✅ Crypto paper sells can close a fractional size, and a stored stop or target can exit the position
- ✅ Kraken paper fills longs and shorts again (`execute_signal` was missing)
- ✅ Strategies see open positions, and candle frames keep their symbol (the first Kraken fill had been stored as UNKNOWN)
- ✅ Equity blocks new buys when the book is over its leverage cap or the position read comes back empty
- ✅ Regime analysis, drawdown rounding, and the Kraken optimization row are on blue standby (`0a6d733`)

### Next steps
1. Confirm the new equity longs have working brackets at Alpaca, even though `positions.stop_loss` is still null
2. Watch crypto, Kraken, and equity through the window that started 2026-10-13
3. Ship the standby web fixes when a release is requested. Do not switch traffic until then
4. Do not start Phase 1.5.10 live capital until four clean weeks pass

## Known Issues
- Equity rows opened on 2026-10-13 have `stop_loss` null in the database. Crypto and Kraken stops are stored.
- Alpaca paper account equity was not reset to $100,000. Closing positions returned cash to that broker account.
- Public site is still v1.13.3. Regime analysis on green still expects the old nested payload.
- Coinbase `get_products()` can hang. Crypto uses the curated symbol list.

## Exact Next Command
Check the three books, then look at whether the new equity positions have Alpaca stop orders.

```bash
ssh root@10.92.3.27 "systemctl is-active quantshift-equity quantshift-crypto quantshift-kraken"
```

Then, on the bot host with the equity service environment, list Alpaca open orders for the new longs and compare them to `positions.stop_loss`.
