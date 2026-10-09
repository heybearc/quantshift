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
