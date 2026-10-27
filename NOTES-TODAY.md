---
date: 2026-10-27
purpose: Scratchpad for today's discoveries (promote on /end-day)
---

## Today

### Focus
- Paper window after the candle-frame fix, then the standby Kraken gap

### Discoveries / Notes
- Coinbase stayed flat overnight: 1,172 cycles, no orders. Kraken placed 18 band snaps and no washout or volatility break.
- The volatility break was silent because each host attached only one timeframe. Fixed in v1.18.6. The gates were not loosened.
- Standby had no Kraken service. Equity and crypto units were disabled. Redis on that host was its own master.
- Kraken on standby reached the loop in 3.2 seconds and stayed read-only. Equity and crypto were still loading the sentiment model at 45 seconds.
- v1.18.7 is green LIVE. Blue matches. Bot standby is on the same commit and its services are stopped.

### Decisions to Promote
- D-QS-022: fail over only when all three heartbeats are stale.

### Blockers / Risks
- Kraken is still under the $5,000 start. Do not reset it.
- No washout or volatility break has filled. Revisit the squeeze line only if none prints before about 2026-11-16.

### Links / Commands
- `bash scripts/bot-release-check.sh`
