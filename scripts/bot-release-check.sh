#!/bin/bash
# Bot-host check for a QuantShift release that restarted equity, crypto, or Kraken.
# Confirms each bot is alive, the latest regime name is real, and Kraken is not
# skipping cycles for lack of candles.

set -euo pipefail

HOST="${BOT_HOST:-root@10.92.3.27}"

ssh -o BatchMode=yes -o ConnectTimeout=12 "$HOST" 'python3 -' << 'PY'
import pathlib, subprocess, sys
from datetime import datetime, timezone

services = ("quantshift-equity", "quantshift-crypto", "quantshift-kraken")
for service in services:
    state = subprocess.check_output(["systemctl", "is-active", service], text=True).strip()
    if state != "active":
        print(f"FAIL {service} is {state}")
        sys.exit(1)
    print(f"OK {service} active")

pid = subprocess.check_output(
    ["systemctl", "show", "-p", "MainPID", "--value", "quantshift-kraken"], text=True
).strip()
url = None
for item in pathlib.Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
    if item.startswith(b"DATABASE_URL="):
        url = item.split(b"=", 1)[1].decode()
if not url:
    print("FAIL database connection is missing")
    sys.exit(1)

def psql(sql):
    proc = subprocess.run(["psql", url, "-At", "-F", "|", "-c", sql], text=True, capture_output=True)
    if proc.returncode != 0:
        err = (proc.stderr or "query failed").replace(url, "[redacted]")
        print("FAIL", err.strip()[:300])
        sys.exit(1)
    return [line for line in proc.stdout.splitlines() if line.strip()]

now = datetime.now(timezone.utc)
heartbeats = psql("""
SELECT bot_name, extract(epoch FROM (NOW() - last_heartbeat))::int
FROM bot_status ORDER BY bot_name
""")
for row in heartbeats:
    name, age = row.split("|", 1)
    if int(age) > 180:
        print(f"FAIL {name} heartbeat is {age}s old")
        sys.exit(1)
    print(f"OK {name} heartbeat {age}s")

known = {
    "BULL_TRENDING", "BEAR_TRENDING", "HIGH_VOL_CHOPPY",
    "LOW_VOL_RANGE", "CRISIS", "UNKNOWN",
}
regimes = psql("""
SELECT DISTINCT ON (bot_name) bot_name, regime,
       extract(epoch FROM (NOW() - timestamp))::int
FROM regime_history
ORDER BY bot_name, timestamp DESC
""")
seen = set()
for row in regimes:
    name, regime, age = row.split("|")
    seen.add(name)
    if regime not in known:
        print(f"FAIL {name} regime {regime!r} is not a known label")
        sys.exit(1)
    limit = 1800 if name == "quantshift-equity" else 600
    if int(age) > limit:
        print(f"FAIL {name} regime is {age}s old")
        sys.exit(1)
    print(f"OK {name} regime {regime} age {age}s")

for name in services:
    if name not in seen:
        print(f"FAIL {name} has no regime row")
        sys.exit(1)

log = subprocess.check_output(
    ["journalctl", "-u", "quantshift-kraken", "--since", "5 min ago", "-o", "cat", "--no-pager"],
    text=True, errors="replace",
)
if "OHLC error" in log or "No market data" in log:
    print("FAIL Kraken skipped a cycle because candle data failed")
    sys.exit(1)
if "strategy_cycle_completed" not in log:
    print("FAIL Kraken has not finished a cycle in the last 5 minutes")
    sys.exit(1)
print("OK Kraken completed a cycle without a candle error")
print("bot-release-check passed")
PY