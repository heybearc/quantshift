# QuantShift Task State

**Last updated:** 2026-10-30
**Current branch:** main
**Working on:** Phase 1.5.9 paper validation — clock restarted 2026-10-19

---

## Current Task
**Phase 1.5.9 paper validation** — clock restarted 2026-10-19 because Coinbase and Kraken now trade different books. Do not start live capital. Window runs through about 2026-11-16.

Public https://quantshift.io is green LIVE on v1.18.7 (`97ccab1`). Blue STANDBY is ahead at `0c0effa` (quiet-hour panel, display-only result history). The dashboard result is closed trades plus the open book, with an estimated cost beside it. That cost is not taken from the account. Crypto and Kraken use the database VIP `10.92.3.23`. Writable Postgres is `10.92.3.31`. `10.92.3.21` is stopped, so there is no replica. Equity still runs its seven strategies. Coinbase is long only and no longer runs the band snap. Kraken may short, with no leverage, and still runs the band snap. Open positions stay open.

### What I'm doing right now
Coinbase trades the washout and the volatility break, long only. Kraken keeps the 15-minute band snap and stands it down when the hourly bar breaks out. A crypto setup with at least 30 closes, a hit rate under 35%, and a profit factor under 1 turns off.

### Recent completions
- ✅ `0c0effa` is on blue STANDBY. Coinbase product list times out at 5 seconds, FinBERT can load from `/opt/quantshift/models/finbert`, and the dashboard shows quiet-hour counts plus display-only performance history. Bot hosts have not pulled this commit.
- ✅ Shipped v1.18.7 (`97ccab1`) to green LIVE and synced blue. Standby can start Kraken. Failover waits until all three heartbeats are stale. Standby Redis is a replica again.
- ✅ Shipped v1.18.6 (`4b505b2`). Coinbase and Kraken can see both the daily and hourly chart for a volatility break. No washout or volatility-break fill since that restart.
- ✅ Shipped v1.18.5 (`09fccc5`) to green LIVE and synced blue. The dashboard shows an estimated fill cost beside the result. The cost is not taken from the account.
- ✅ Coinbase left the 15-minute band snap. Kraken kept it and stands it down when the hourly bar breaks out. A crypto setup turns off only when it has 30 closes, a hit rate under 35%, and a profit factor under 1.
- ✅ Paper clock restarted 2026-10-19 because the two crypto books no longer place the same trades. Window runs through about 2026-11-16.
- ✅ Shipped v1.17.0 (`f452a35`). Crypto and Kraken can trade a volatility squeeze as well as the daily washout

### Next steps
1. Pull `0c0effa` on the bot hosts so the product-list timeout, FinBERT cache, and quiet-hour log run. Do not switch LIVE.
2. Watch the three paper books through the window that ends about 2026-11-16
3. See whether Coinbase opens a washout or a volatility break. Score Kraken's band snap on its own.
4. Do not reset Kraken to explain the gap under the $5,000 start
5. Do not start Phase 1.5.10 live capital until four clean weeks pass
6. Leave the estimated cost beside the result. Putting that cost inside the fill waits until this window ends.

## Known Issues
- Kraken paper equity is below the $5,000 start. The gap was not diagnosed. Do not reset the book.
- No washout or volatility-break fill since the 2026-10-26 frame fix. The gates were left as they are.
- Bot hosts have not pulled `0c0effa`. Until they do, Coinbase `get_products()` can still hang and FinBERT can still take up to three minutes (startup limit 180 seconds).
- A quiet hour still produces no order until the hour is finished, the bar is in a squeeze, and price breaks a pivot. Those counts show on STANDBY after the bots publish them.

## Exact Next Command
Pull `0c0effa` on the bot hosts, then check that the three bots are still healthy and whether any new crypto or Kraken order used the washout or the volatility break.

```bash
bash scripts/bot-release-check.sh
```
