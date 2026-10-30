---
date: 2026-10-30
purpose: Scratchpad for today's discoveries (promote on /end-day)
---

## Today

### Focus
- Mid-day checkpoint. Paper window still runs through about 2026-11-16.

### Discoveries / Notes
- `0c0effa` is on blue STANDBY. LIVE stays green at v1.18.7 (`97ccab1`).
- The product-list timeout, FinBERT disk cache, and quiet-hour log are in that commit. Bot hosts have not pulled it.
- Dashboard sparklines, expectancy, and payoff are display only. Estimated fill cost stays beside the result.
- No urgent feedback items.

### Decisions to Promote
- Do not switch LIVE for `0c0effa`. Pull it on the bot hosts first.

### Blockers / Risks
- Kraken paper equity is still under the $5,000 start. Leave that book alone.
- No washout or volatility-break fill since the 2026-10-26 frame fix.

### Links / Commands
- STANDBY: http://10.92.3.29:3001
- Next: pull `0c0effa` on the bot hosts, then `bash scripts/bot-release-check.sh`
