---
purpose: Archive of rolled daily notes
---


## 2026-10-09

_Rolled from NOTES-TODAY.md_

---
date: 2026-10-09
purpose: Scratchpad for today's discoveries (promote on /end-day)
---

## Today

### Focus
- Crypto paper orders must not hit the live Coinbase account

### Discoveries / Notes
- `simulated_capital` only changed account sizing; `market_order` still went to Coinbase and returned `INSUFFICIENT_FUND`
- Paper mode now fills an in-memory book and refuses live Coinbase orders (`170831b`, CT100)
- Equity cap is `risk_management.max_positions` (10). A bad default of 5 trimmed the paper book on 2026-10-08
- HAProxy: `quantshift.io` → green. MCP `get_deployment_status` still reports blue LIVE

### Decisions to Promote
- Crypto paper trading stays off the live Coinbase account while `simulated_capital` is set

### Blockers / Risks
- Web STANDBY deploy blocked until MCP and HAProxy agree on LIVE
- Phase 1.5.9 clock restarts 2026-10-09; do not go live

### Links / Commands
- Commits: `479c00c`, `66f8474`, `170831b`

## 2026-10-16

_Rolled from NOTES-TODAY.md_

---
date: 2026-10-16
purpose: Scratchpad for today's discoveries (promote on /end-day)
---

## Today

### Focus
- Crypto and Kraken now trade the washout setup and a volatility break. Equity stays on its seven strategies.

### Discoveries / Notes
- v1.15.1, v1.16.0, and v1.17.0 shipped. Live is green (`f452a35`). Standby is blue. Both nodes match.
- Coinbase is long only. Kraken may short. No leverage. Open positions were not flattened.
- Position caps are 12 on Coinbase and 8 on Kraken. Cash limits still bind first.
- The paper-window clock stays 2026-10-13 through about 2026-11-10.

### Decisions to Promote
- Do not put the licensed chart source in the repo. The decision rules are reimplemented in Python.

### Blockers / Risks
- Trades will still be uncommon. A squeeze needs a finished hour and a pivot break.
- Kraken paper equity is below the $5,000 start. Do not reset the book to explain the gap.

### Links / Commands
- https://github.com/heybearc/quantshift/releases/tag/v1.17.0

## 2026-10-19

_Rolled from NOTES-TODAY.md_

---
date: 2026-10-16
purpose: Scratchpad for today's discoveries (promote on /end-day)
---

## Today

### Focus
- Band snap added as a third crypto/Kraken paper setup. Washout and volatility break stay. Clock stays on 2026-10-13.

### Discoveries / Notes
- 

### Decisions to Promote
- 

### Blockers / Risks
- 

### Links / Commands
- 

## 2026-10-19

- Postgres failed over at 02:00. Writable node is 10.92.3.31. VIP 10.92.3.23. Old host 10.92.3.21 is stopped. No replica.
- QuantShift web and the three bots use the VIP.
- Dashboard v1.18.4 is live on blue. Total P&L is closed plus open. Crypto start $10,000. Kraken start $5,000. Equity has no start.
- Unknown is a missing strategy label, not a setup. Left unfixed.
- Custom dashboards stay off the plan.
- No crypto or Kraken rule change.

## 2026-10-20

_Rolled from NOTES-TODAY.md_

---
date: 2026-10-19
purpose: Scratchpad for today's discoveries (promote on /end-day)
---

## Today

### Focus
- 

### Discoveries / Notes
- Coinbase left the 15-minute band snap. Kraken kept it and stands down when the volatility break wants the symbol. Paper clock restarted 2026-10-19. 

### Decisions to Promote
- 

### Blockers / Risks
- 

### Links / Commands
- 

## 2026-10-27

_Rolled from NOTES-TODAY.md_

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
