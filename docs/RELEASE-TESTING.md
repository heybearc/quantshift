# Release testing

A version bump does not run all 82 browser tests. The full list is mostly repeated page-load checks, and a green run of it has still missed wrong dashboard numbers, a mislabeled regime, and a bot that never received candles.

## Every bump, on STANDBY

```bash
RELEASE_BASE_URL=https://<standby-host> bash scripts/release-test.sh gate
```

The gate checks login, that the target is STANDBY, that release notes have a version, that Pending Approvals loads, and that the equity regime name is one of the known labels.

Then run the area the change touched:

| Change | Command |
|---|---|
| Login, registration, invitations | `bash scripts/release-test.sh auth` |
| Users, approvals, admin pages | `bash scripts/release-test.sh admin` |
| Dashboard, trades, positions, bots | `bash scripts/release-test.sh trading` |

`auth`, `admin`, and `trading` include the gate. Do not pick individual tests at release time.

If the release restarts equity, crypto, or Kraken, also run:

```bash
bash scripts/bot-release-check.sh
```

That check is separate from Playwright. It confirms fresh heartbeats, a real regime name, and that Kraken finished a cycle without a candle error.

## Full suite

```bash
RELEASE_BASE_URL=https://<standby-host> bash scripts/release-test.sh full
```

Run this on a schedule, and before a release that changes login, order execution, or the database schema. A failed full run blocks the next release even when the gate was green.

## What a green gate does not prove

A passing gate means the standby site loads and a few values match. It does not prove the bots are healthy, and it does not prove pages that were not in the selected area.
