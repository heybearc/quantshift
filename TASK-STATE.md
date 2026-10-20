# QuantShift Task State

**Last updated:** 2026-10-19
**Current branch:** main
**Working on:** Phase 1.5.9 paper validation — clock restarted 2026-10-19

---

## Current Task
**Phase 1.5.9 paper validation** — clock restarted 2026-10-19 because Coinbase and Kraken now trade different books. Do not start live capital. Window runs through about 2026-11-16.

Public https://quantshift.io is blue LIVE on v1.18.4 (`87b4bfb`). Green standby matches. The dashboard result is closed trades plus the open book. Crypto and Kraken use the database VIP `10.92.3.23`. Writable Postgres is `10.92.3.31`. `10.92.3.21` is stopped, so there is no replica. Equity still runs its seven strategies. Coinbase is long only and no longer runs the band snap. Kraken may short, with no leverage, and still runs the band snap. Open positions stay open.

### What I'm doing right now
Coinbase trades the washout and the volatility break, long only. Kraken keeps the 15-minute band snap and stands it down when the hourly bar breaks out. A crypto setup with at least 30 closes, a hit rate under 35%, and a profit factor under 1 turns off.

### Recent completions
- ✅ Shipped v1.17.0 (`f452a35`). Crypto and Kraken can trade a volatility squeeze as well as the daily washout
- ✅ Shipped v1.16.0. Crypto and Kraken left the seven equity strategies for the washout setup
- ✅ Shipped v1.15.1. Crypto results stay with the strategy that opened them, and the equity regime reading continues after the close
- ✅ Coinbase position cap is 12. Kraken position cap is 8. Cash limits still stop a full book first
- ✅ Existing crypto, Kraken, and equity positions were left until their own stops or targets

### Next steps
1. Watch the three paper books through the window that ends about 2026-11-16
2. See whether Coinbase opens a washout or a volatility break. Score Kraken's band snap on its own.
3. Do not reset Kraken to explain the gap under the $5,000 start
4. Do not start Phase 1.5.10 live capital until four clean weeks pass

## Known Issues
- Kraken paper equity is below the $5,000 start. The gap was not diagnosed. Do not reset the book.
- A quiet hour can still produce no new crypto or Kraken orders. The break has to be on a finished hour, in a squeeze, through a pivot.
- Coinbase `get_products()` can hang. Crypto symbol loading already has a fallback.

## Exact Next Command
Check that the three bots are still healthy, then look at whether any new crypto or Kraken order used the washout or the volatility break.

```bash
bash scripts/bot-release-check.sh
```
