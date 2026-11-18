---
date: 2026-11-18
purpose: Scratchpad for today's discoveries (promote on /end-day)
---

## 2026-11-18 mid-day

### Discoveries / Notes
- Equity on CT100 is `57b3635`, primary, 5 open paper positions. STANDBY is green `10.92.3.30`. LIVE stays blue on v1.19.2 (`09e0992`).
- Asset list is live again: 14,429 assets, 4,980 tradable, 100 large-cap names. TXSE no longer rejects the list.
- Washout plus volatility break will trade rarely. Coinbase and Kraken still have no fill on those setups since v1.18.6.
- Next product work is a candidate journal and regime scoring across the owned strategies. The regime model still names the old seven and does not pick a winner.
- Urgent feedback: 0.

### Decisions to Promote
- None recorded. Direction is the journal and the contest. Paper clock stays 2026-11-06. Live capital stays off.

### Blockers / Risks
- The two equity setups can stay flat for days. That is the gate, not a dead process.
- A start that never reaches the bar loop can still die at 90 seconds.

## 2026-11-18

### Discoveries / Notes
- D-QS-026. One process per book on CT100. CT101 bots stay stopped. The spare monitor logs stale heartbeats and does not promote Redis.
- `e675a1e` and `ab7c61e` are on main. Dashboard STANDBY is green `10.92.3.30`. LIVE stays green on v1.19.2 (`09e0992`).
- Equity and Coinbase were restarted onto `ab7c61e`. First start hit the 90-second watchdog; systemd restarted them. Equity is primary with 5 Alpaca paper positions. Coinbase paper completed a cycle with 0 orders.
- Kraken and Kraken Sprint stayed active from 22:53 UTC on `ab7c61e`. Both remain simulation. Do not flip `simulation_mode`.
- Urgent feedback: 0.

### Decisions to Promote
- D-QS-026 is in DECISIONS.md. It supersedes the promotion half of D-QS-022.

### Blockers / Risks
- Equity paper now runs the washout and the volatility break, long only. Open positions stay open. The paper clock stays on 2026-11-06. D-QS-027.
- A slow bot start can be killed at 90 seconds before the process notifies systemd.

## 2026-11-17

### Discoveries / Notes
- LIVE is green `10.92.3.30` CT138 on v1.19.2 (`09e0992`). STANDBY is blue `10.92.3.29` CT137, synced. HAProxy backend is green.
- Trading gate on green passed 48 tests plus the closed-bar spec before the bump. GitHub release v1.19.2 is cut.
- Equity on primary `10.92.3.27` uses the last finished daily bar. Standby equity on `10.92.3.28` stays stopped. Crypto and Kraken were not restarted for this release.
- Drawdown is the account-equity path. The old peak-profit formula had printed 288%.
- Paper window is still 2026-11-06 through about 2026-12-04. Do not restart the clock or loosen the 5% daily-loss limit.
- No urgent feedback items.

### Decisions to Promote
- None new. Daily-loss and quiet-hour gates stay as they are.

### Blockers / Risks
- Coinbase can stay quiet while the squeeze gate is unmet. That is the designed gate, not a stuck bot.

## 2026-11-11

### Discoveries / Notes
- LIVE is blue `10.92.3.29` on v1.19.1 (`473d88b`). STANDBY is green `10.92.3.30`, synced. Public site returned 200.
- qa-01 full gate passed, 112 tests, plus the bearer-login test. Bot release check passed.
- Day 4 of the window. On Monday, equity closed SPY at the target for +$4.54 and still held DIA, QQQ, and NVDA. Coinbase was flat at about $10,044.
- Kraken's Friday latch had been blocking every signal. After the fix it was short NEAR. Sprint was flat at $5,002.63.
- A restart had refilled Kraken cash from $5,000. Closed-trade results were restored. Kraken about +$3.39 after a −$1.01 NEAR round trip.
- No urgent feedback items.

### Decisions to Promote
- D-QS-025 is in DECISIONS.md. Do not loosen the 5% daily-loss limit.

### Blockers / Risks
- Equity's open NVDA loss was still the window's main red mark on Monday.
- Sprint still has too few closes to clear its estimated cost.

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
