# QuantShift Task State

**Last updated:** 2026-11-18
**Current branch:** main
**Working on:** Phase 1.5.9 paper validation — clock restarted 2026-11-06

---

## Current Task
**Phase 1.5.9 paper validation** — clock restarted 2026-11-06. The 2026-10-19 window was discarded because the trade table never stored a close. Do not start live capital. Window runs through about 2026-12-04.

Public https://quantshift.io is green LIVE on v1.19.2 (`09e0992`). Blue is STANDBY and is synced to that release. Bot code on CT100 is `ab7c61e`, ahead of the dashboard release: one process per book, no Redis promotion, stable order ids. Equity decides from the last finished daily bar. Drawdown is the drop in account equity. CT101 bots stay stopped. The dashboard result is closed trades plus the open book, with an estimated cost beside it. That cost is not taken from the account. Crypto and Kraken use the database VIP `10.92.3.23`. Writable Postgres is `10.92.3.31`. `10.92.3.21` is stopped, so there is no replica. Equity runs the washout and the volatility break, long only, one decision per finished day. Coinbase is long only and no longer runs the band snap. Kraken may short, with no leverage, and still runs the band snap. Kraken Sprint is a separate $5,000 paper book. Open positions on the three validation books stay open.

### What I'm doing right now
Equity now uses the same washout and volatility break as Coinbase, long only. Open equity positions stay open. Kraken keeps the 15-minute band snap and stands it down when the hourly bar breaks out. A crypto setup with at least 30 closes, a hit rate under 35%, and a profit factor under 1 turns off.

### Recent completions
- ✅ Shipped v1.19.2 (`09e0992`) to green LIVE and synced blue. Equity uses the last closed daily bar. Drawdown is account equity. A flat Kraken book stays valid. Trading gate passed 48 tests plus the closed-bar spec.
- ✅ Shipped v1.19.1 (`473d88b`) to blue LIVE and synced green. Login returns a bearer token. The daily-loss latch clears when the book is back inside the limit. A Kraken restart keeps closed-trade cash.
- ✅ Shipped v1.19.0 (`8ff3e86`) to green LIVE and synced blue. Kraken Sprint is its own paper book.
- ✅ Shipped v1.18.8 (`e3d8c5d`) to blue LIVE. Finished paper trades are stored as closed, and performance scores them for equity, Coinbase, and Kraken. The dashboard explains a quiet hour.
- ✅ Shipped v1.18.7 (`97ccab1`) to green LIVE and synced blue. Standby can start Kraken. Failover waits until all three heartbeats are stale. Standby Redis is a replica again.
- ✅ Shipped v1.18.6 (`4b505b2`). Coinbase and Kraken can see both the daily and hourly chart for a volatility break. No washout or volatility-break fill since that restart.
- ✅ Shipped v1.18.5 (`09fccc5`) to green LIVE and synced blue. The dashboard shows an estimated fill cost beside the result. The cost is not taken from the account.
- ✅ Coinbase left the 15-minute band snap. Kraken kept it and stands it down when the hourly bar breaks out. A crypto setup turns off only when it has 30 closes, a hit rate under 35%, and a profit factor under 1.
- ✅ Paper clock restarted 2026-10-19 because the two crypto books no longer place the same trades. Window runs through about 2026-11-16.
- ✅ Shipped v1.17.0 (`f452a35`). Crypto and Kraken can trade a volatility squeeze as well as the daily washout

### Next steps
1. Watch the paper books through the window that ends about 2026-12-04. Score closed trades on equity, Coinbase, and Kraken. The equity book now opens only washout and volatility-break trades.
2. See whether Coinbase opens a washout or a volatility break. Score Kraken's band snap on its own.
3. Do not start Phase 1.5.10 live capital until four clean weeks pass.
4. Leave the estimated cost beside the result. Putting that cost inside the fill waits until this window ends.

## Known Issues
- A quiet hour still produces no order until the hour is finished, the bar is in a squeeze, and price breaks a pivot. That gate was left as it is.
- Equity and Coinbase startup can exceed the 90-second watchdog. The 2026-11-17 restart was killed once and systemd brought both back. They then stayed primary.
- Live Kraken has order identity and no strategy cycle. Both Kraken books stay `simulation_mode: true`.

## Exact Next Command
```bash
bash scripts/bot-release-check.sh
```
