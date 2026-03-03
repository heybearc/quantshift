# Emergency Stop Runbook

**Purpose:** Remote emergency stop capability for QuantShift trading bots  
**Created:** 2026-03-03  
**Phase:** 1.5.1 Critical Safety Features

---

## Overview

The emergency stop system allows you to remotely halt trading and close all positions immediately via a Redis flag. This is a critical safety feature for protecting capital during:

- Unexpected market conditions
- Bot malfunction or erratic behavior
- System maintenance requiring immediate shutdown
- Any situation requiring immediate position closure

---

## How It Works

1. **Redis Flag Check:** Bot checks `bot:{bot_name}:emergency_stop` flag every cycle (every second)
2. **Immediate Action:** If flag is `true`, bot immediately:
   - Closes all open positions at market price
   - Updates database status to `EMERGENCY_STOPPED`
   - Records event in Prometheus metrics
   - Stops trading loop
3. **Logging:** All actions logged with CRITICAL level for audit trail

---

## Emergency Stop Commands

### Method 1: Admin Dashboard UI (Recommended)

**Steps:**
1. Log in to QuantShift dashboard as admin
2. Navigate to Dashboard page
3. Scroll to "Emergency Stop Controls" section (admin-only)
4. Click "Emergency Stop Equity Bot" or "Emergency Stop Crypto Bot"
5. Confirm in the dialog that appears
6. Bot will stop within 5 seconds

**Advantages:**
- ✅ Accessible from anywhere (mobile, desktop, tablet)
- ✅ No SSH or Redis CLI required
- ✅ Clear confirmation dialog prevents accidents
- ✅ Visual feedback on success/failure
- ✅ Audit trail via API logs

### Method 2: Redis CLI (Backup/Advanced)

**For Equity Bot:**
```bash
# From any machine with Redis access
redis-cli -h 10.92.3.27 -a 'Cloudy_92!' SET bot:quantshift-equity:emergency_stop true

# Or SSH to primary bot container
ssh qs-bot-primary
redis-cli -a 'Cloudy_92!' SET bot:quantshift-equity:emergency_stop true
```

**For Crypto Bot:**
```bash
# From any machine with Redis access
redis-cli -h 10.92.3.27 -a 'Cloudy_92!' SET bot:quantshift-crypto:emergency_stop true

# Or SSH to primary bot container
ssh qs-bot-primary
redis-cli -a 'Cloudy_92!' SET bot:quantshift-crypto:emergency_stop true
```

**Use CLI method when:**
- Dashboard is unavailable
- Network issues prevent web access
- You need to script emergency stops
- You're already SSH'd into the bot container

### Check Emergency Stop Status

```bash
# Check if emergency stop is active
redis-cli -h 10.92.3.27 -a 'Cloudy_92!' GET bot:quantshift-equity:emergency_stop
redis-cli -h 10.92.3.27 -a 'Cloudy_92!' GET bot:quantshift-crypto:emergency_stop

# Returns: "true" if active, (nil) if not set
```

### Clear Emergency Stop (Resume Trading)

```bash
# Clear the flag
redis-cli -h 10.92.3.27 -a 'Cloudy_92!' DEL bot:quantshift-equity:emergency_stop
redis-cli -h 10.92.3.27 -a 'Cloudy_92!' DEL bot:quantshift-crypto:emergency_stop

# Then restart the bot service
ssh qs-bot-primary
sudo systemctl restart quantshift-equity
sudo systemctl restart quantshift-crypto
```

---

## What Happens During Emergency Stop

### Immediate Actions (< 5 seconds)

1. **Flag Detection:** Bot detects emergency stop flag in main loop
2. **Position Closure:** Bot closes all open positions at market price
3. **Database Update:** Bot status set to `EMERGENCY_STOPPED`
4. **Metrics Recording:** Prometheus counter incremented
5. **Bot Shutdown:** Trading loop stops

### Logging Output

```json
{
  "event": "emergency_stop_flag_detected",
  "timestamp": "2026-03-03T17:45:23Z"
}
{
  "event": "emergency_stop_triggered",
  "reason": "Emergency stop flag set in Redis",
  "bot_name": "quantshift-equity"
}
{
  "event": "emergency_stop_closing_positions",
  "count": 3,
  "symbols": ["SPY", "QQQ", "AAPL"]
}
{
  "event": "emergency_stop_position_closed",
  "symbol": "SPY"
}
{
  "event": "emergency_stop_positions_closed",
  "attempted": 3
}
{
  "event": "emergency_stop_complete",
  "bot_name": "quantshift-equity",
  "reason": "Emergency stop flag set in Redis"
}
```

### Database Changes

```sql
-- Bot status updated
UPDATE bot_status 
SET status = 'EMERGENCY_STOPPED', updated_at = NOW() 
WHERE bot_name = 'quantshift-equity';

-- Positions removed (closed)
DELETE FROM positions WHERE bot_name = 'quantshift-equity';
```

### Prometheus Metrics

```
# Emergency stop counter incremented
quantshift_equity_emergency_stops_total{component="quantshift_equity"} 1

# Positions count goes to zero
quantshift_equity_positions_open{component="quantshift_equity",bot="quantshift-equity"} 0
```

---

## Verification Steps

### 1. Check Bot Stopped

```bash
# Check systemd service status
ssh qs-bot-primary
sudo systemctl status quantshift-equity

# Should show: inactive (dead) or failed
```

### 2. Verify Positions Closed

```bash
# Check database
psql -h 10.92.3.21 -U quantshift -d quantshift -c \
  "SELECT * FROM positions WHERE bot_name = 'quantshift-equity';"

# Should return 0 rows
```

### 3. Check Broker Positions

```bash
# SSH to bot container and check Alpaca
ssh qs-bot-primary
cd /opt/quantshift/apps/bots
source /opt/quantshift/venv/bin/activate
python -c "
from quantshift_core.executors import AlpacaExecutor
import yaml
with open('config/equity_config.yaml') as f:
    config = yaml.safe_load(f)
executor = AlpacaExecutor(config)
positions = executor.get_positions()
print(f'Open positions: {len(positions)}')
for pos in positions:
    print(f'  {pos.symbol}: {pos.quantity} @ {pos.current_price}')
"

# Should show 0 positions
```

### 4. Review Logs

```bash
# Check bot logs for emergency stop events
ssh qs-bot-primary
sudo journalctl -u quantshift-equity -n 100 --no-pager | grep emergency_stop
```

---

## Recovery Procedure

### After Emergency Stop

1. **Investigate Root Cause**
   - Why was emergency stop triggered?
   - Review logs for errors or anomalies
   - Check market conditions
   - Verify bot configuration

2. **Verify System State**
   - All positions closed? ✓
   - Database consistent? ✓
   - No pending orders? ✓
   - Redis state clean? ✓

3. **Clear Emergency Flag**
   ```bash
   redis-cli -h 10.92.3.27 -a 'Cloudy_92!' DEL bot:quantshift-equity:emergency_stop
   ```

4. **Restart Bot (if safe)**
   ```bash
   ssh qs-bot-primary
   sudo systemctl restart quantshift-equity
   ```

5. **Monitor Closely**
   - Watch logs for first 5-10 minutes
   - Verify normal operation
   - Check position entries are appropriate

---

## Testing Emergency Stop

### Paper Trading Test

```bash
# 1. Ensure bot is running in paper trading mode
ssh qs-bot-primary
sudo systemctl status quantshift-equity

# 2. Wait for bot to open at least 1 position
# Check positions table or Alpaca paper account

# 3. Trigger emergency stop
redis-cli -a 'Cloudy_92!' SET bot:quantshift-equity:emergency_stop true

# 4. Verify within 5 seconds:
#    - Bot stops
#    - Positions closed
#    - Database updated
#    - Logs show emergency stop events

# 5. Clear flag and restart
redis-cli -a 'Cloudy_92!' DEL bot:quantshift-equity:emergency_stop
sudo systemctl restart quantshift-equity
```

### Success Criteria

- ✅ Emergency stop detected within 1 second
- ✅ All positions closed within 5 seconds
- ✅ Database status updated to EMERGENCY_STOPPED
- ✅ Prometheus metric incremented
- ✅ Bot stops gracefully (no crashes)
- ✅ Logs show complete audit trail
- ✅ Bot can restart successfully after clearing flag

---

## Prometheus Alerts (Future)

**Recommended alert rules:**

```yaml
# Alert when emergency stop is triggered
- alert: QuantShiftEmergencyStop
  expr: increase(quantshift_equity_emergency_stops_total[5m]) > 0
  labels:
    severity: critical
  annotations:
    summary: "QuantShift emergency stop triggered"
    description: "Bot {{ $labels.component }} triggered emergency stop"

# Alert when bot status is EMERGENCY_STOPPED
- alert: QuantShiftBotEmergencyStopped
  expr: quantshift_bot_status{status="EMERGENCY_STOPPED"} == 1
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "QuantShift bot in emergency stopped state"
    description: "Bot {{ $labels.bot }} is in EMERGENCY_STOPPED state"
```

---

## Troubleshooting

### Emergency Stop Not Working

**Symptom:** Flag set but bot continues trading

**Possible Causes:**
1. Redis connection failed
2. Wrong bot name in Redis key
3. Bot not checking flag (code issue)

**Debug Steps:**
```bash
# 1. Verify Redis connectivity
redis-cli -h 10.92.3.27 -a 'Cloudy_92!' PING
# Should return: PONG

# 2. Verify flag is set correctly
redis-cli -h 10.92.3.27 -a 'Cloudy_92!' GET bot:quantshift-equity:emergency_stop
# Should return: "true"

# 3. Check bot logs for Redis errors
sudo journalctl -u quantshift-equity -n 50 --no-pager | grep -i redis

# 4. If all else fails, stop service manually
sudo systemctl stop quantshift-equity
```

### Positions Not Closing

**Symptom:** Emergency stop triggered but positions remain open

**Possible Causes:**
1. Broker API failure
2. Market closed (equity only)
3. Insufficient permissions

**Debug Steps:**
```bash
# 1. Check broker API status
# (Alpaca status page: https://status.alpaca.markets/)

# 2. Manually close positions via broker UI
# Alpaca paper: https://app.alpaca.markets/paper/dashboard/overview

# 3. Check bot logs for API errors
sudo journalctl -u quantshift-equity -n 100 --no-pager | grep -i "position_close"
```

---

## Security Considerations

1. **Redis Password:** Emergency stop requires Redis password (`Cloudy_92!`)
2. **Network Access:** Only accessible from homelab network (10.92.3.0/24)
3. **SSH Access:** Requires SSH key authentication to bot containers
4. **Audit Trail:** All emergency stops logged with timestamps and reasons

---

## Related Documentation

- `IMPLEMENTATION-PLAN.md` - Phase 1.5.1 Emergency Kill Switch
- `docs/REDIS-FAILOVER-PROCEDURE.md` - Redis master-slave failover
- `infrastructure/grafana/quantshift-system-health.json` - System health dashboard

---

**Last Updated:** 2026-03-03  
**Status:** Implemented, ready for testing
