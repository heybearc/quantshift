---
date: 2026-11-07
purpose: Scratchpad for today's discoveries (promote on /end-day)
---

## Today

### Focus
- Mid-day checkpoint after shipping v1.18.8 and restarting the paper window.

### Discoveries / Notes
- LIVE is blue `10.92.3.29` on v1.18.8 (`e3d8c5d`). STANDBY is green `10.92.3.30` at `9c94dda`.
- A paper exit now closes the trade row. Performance scores closed trades for equity, Coinbase, and Kraken.
- The 2026-10-19 window was voided. The clock runs 2026-11-06 through about 2026-12-04.
- Kraken closed INJUSD for +$1.64 on the reset. Equity holds SPY and QQQ. Kraken is short NEAR and SUI. Coinbase is flat at $10,000.
- Standby trading gate passed 45 tests plus the closed-trade checks. Bot heartbeats were fresh. Regime was low-volatility range.
- No urgent feedback items.

### Decisions to Promote
- D-QS-023 is in DECISIONS.md. Do not start live capital or loosen the quiet-hour gates.

### Blockers / Risks
- The quiet-hour squeeze gate is unchanged, so the books can stay flat until a finished hour, a squeeze, and a pivot break.
- Kraken's displayed equity was about $4,738 against a $5,000 start after the reset. Not re-checked at mid-day.

### Links / Commands
- STANDBY: http://10.92.3.30:3001
- Next: `bash scripts/bot-release-check.sh`

## 2026-11-07

### Discoveries / Notes
- LIVE is green `10.92.3.30` on v1.19.0 (`8ff3e86`). STANDBY is blue `10.92.3.29`, synced. Docs commit `ef2b89b` is on main only.
- Day 2 of the window, about 7:06pm ET. All four heartbeats were fresh. Crypto books are flat.
- Coinbase closed UNI at the target, +$43.62. About +$38 after the 60 bp estimate.
- Kraken closed three band-snap shorts, +$4.40. About +$3 after the 40 bp estimate.
- Sprint closed ADA at the target and LINK at the stop, net +$2.63. About −$2 after the 40 bp estimate. Two trades.
- Equity closed two SPY trades for +$1.02 and still holds SPY, QQQ, NVDA, and DIA, open about −$150. Market closed until Monday.
- No urgent feedback items.

### Decisions to Promote
- D-QS-024 records the sprint book. Do not move that setup onto the other books.

### Blockers / Risks
- Sprint does not clear its estimated cost yet. Too few closes to judge.
- Equity's open loss is the window's main red mark until Monday.
