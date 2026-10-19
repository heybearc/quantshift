# QuantShift Task State

**Last updated:** 2026-10-19
**Current branch:** main
**Working on:** Phase 1.5.9 paper validation — day 7 of the window that started 2026-10-13

---

## Current Task
**Phase 1.5.9 paper validation** — clock stays on 2026-10-13. Do not move it. Do not start live capital. Window runs through about 2026-11-10.

Public https://quantshift.io is blue LIVE on v1.18.4 (`87b4bfb`). Green standby matches. The dashboard result is closed trades plus the open book. Crypto and Kraken use the database VIP `10.92.3.23`. Writable Postgres is `10.92.3.31`. `10.92.3.21` is stopped, so there is no replica. Equity still runs its seven strategies. Coinbase is long only. Kraken may short, with no leverage. Open positions stay open. The band snap is scored on its own. The 2026-10-13 clock does not move.

### What I'm doing right now
Watching the paper books. No crypto or Kraken retune. No custom dashboard.

### Recent completions
- ✅ Shipped v1.17.0 (`f452a35`). Crypto and Kraken can trade a volatility squeeze as well as the daily washout
- ✅ Shipped v1.16.0. Crypto and Kraken left the seven equity strategies for the washout setup
- ✅ Shipped v1.15.1. Crypto results stay with the strategy that opened them, and the equity regime reading continues after the close
- ✅ Coinbase position cap is 12. Kraken position cap is 8. Cash limits still stop a full book first
- ✅ Existing crypto, Kraken, and equity positions were left until their own stops or targets

### Next steps
1. Watch the three paper books through the window that ends about 2026-11-10
2. See whether crypto or Kraken open a washout, a volatility break, or a band snap. Score the band snap on its own.
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
