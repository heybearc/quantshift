# Crypto Bot Setup Status

**Date:** February 21, 2026  
**Status:** ⚠️ Partially Configured - Needs Coinbase API Credentials

---

## ✅ Completed

### 1. Paper Trading Mode Enabled
- **Config:** `config/crypto_config.yaml`
- **Setting:** `simulated_capital: 10000` (was `null`)
- **Effect:** Bot will paper trade with $10,000 virtual capital instead of real money
- **Committed:** Yes (commit c6940c6)

### 2. Bot Heartbeat Fix
- **Issue:** Bots showing as STALE on dashboard
- **Root Cause:** `run_bot_v3.py` only sent heartbeats to Redis, not PostgreSQL
- **Fix:** Added `_update_db_heartbeat()` method to write to `bot_status` table
- **Status:** Deployed to primary server
- **Commits:** 
  - d8c83f0: Added database heartbeat
  - 4728abe: Fixed psycopg2 import
  - e085d69: Changed to UPDATE instead of INSERT

### 3. Bot Configuration
- **Symbols:** BTC-PERP-INTX, ETH-PERP-INTX (Coinbase perpetuals)
- **Strategies:**
  - Bollinger Bounce (60% capital allocation)
  - RSI Mean Reversion (40% capital allocation)
- **Features:**
  - ML regime detection: ✅ Enabled
  - Risk management: ✅ Enabled
  - Sentiment analysis: ❌ Disabled (crypto config)
- **Cycle Interval:** 300 seconds (5 minutes) - crypto is 24/7
- **Heartbeat Interval:** 30 seconds

---

## ❌ Blocking Issues

### 1. Invalid Coinbase API Credentials

**Error:**
```
Unable to load PEM file. InvalidData(InvalidPadding)
Are you sure you generated your key at https://cloud.coinbase.com/access/api ?
```

**Current State:**
- Systemd service has placeholder API credentials (BBBBB...)
- Bot runs but cannot connect to Coinbase
- Cannot fetch market data or execute trades (even paper trades)

**Required Fix:**
1. Generate real Coinbase API keys at https://cloud.coinbase.com/access/api
2. Update `/etc/systemd/system/quantshift-crypto.service` on primary server:
   ```bash
   Environment="COINBASE_API_KEY=organizations/YOUR-ORG-ID/apiKeys/YOUR-KEY-ID"
   Environment="COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n"
   ```
3. Restart crypto bot: `systemctl restart quantshift-crypto`

**API Key Permissions Needed:**
- View (read market data)
- Trade (for paper trading execution)
- View account balance

### 2. Bot Heartbeat Not Updating

**Symptoms:**
- Both bots show STALE status on dashboard
- Last heartbeat timestamps are hours old
- Equity bot: Last heartbeat 2.5+ hours ago
- Crypto bot: Last heartbeat 3.9+ hours ago

**Investigation Status:**
- Bot code has correct heartbeat logic (every 30 seconds)
- Database UPDATE query is correct
- Bots are running (confirmed via systemctl status)
- No heartbeat errors in recent logs (after latest restart)
- **Possible Issue:** Heartbeat may be silently failing or timing not triggering

**Next Steps:**
- Monitor logs for next heartbeat attempt
- Check if `executor.get_account()` is failing silently
- Verify database connection is working
- May need to add more logging to heartbeat function

---

## 📊 Current Bot Status

**Primary Server (CT100 @ 10.92.3.27):**

| Bot | Status | Last Heartbeat | Issue |
|-----|--------|---------------|-------|
| equity-bot | RUNNING | 2+ hours ago | Heartbeat not updating |
| crypto-bot | RUNNING | 4+ hours ago | Invalid API credentials + heartbeat |

**Database Status:**
```sql
SELECT bot_name, status, last_heartbeat, NOW() - last_heartbeat 
FROM bot_status;
```
- Both bots exist in database
- Status shows RUNNING
- Heartbeats are stale (> 5 minutes = STALE threshold)

---

## 🎯 To Get Crypto Bot Trading

### Immediate Actions Required:

1. **Get Coinbase API Credentials**
   - Go to https://cloud.coinbase.com/access/api
   - Create new API key with trading permissions
   - Download private key (PEM format)
   - Save securely

2. **Update Systemd Service**
   ```bash
   ssh quantshift-primary
   sudo nano /etc/systemd/system/quantshift-crypto.service
   # Update COINBASE_API_KEY and COINBASE_API_SECRET
   sudo systemctl daemon-reload
   sudo systemctl restart quantshift-crypto
   ```

3. **Verify Bot Starts Successfully**
   ```bash
   tail -f /opt/quantshift/logs/crypto-bot.log
   # Should see: "coinbase_executor_initialized" without errors
   ```

4. **Fix Heartbeat Issue**
   - Monitor equity bot logs to see if heartbeat fires
   - If not, may need to add debug logging
   - Verify database connection works from bot

### Optional Enhancements:

- Enable sentiment analysis for crypto (requires FinBERT)
- Train ML regime classifier for crypto markets
- Add more trading pairs (SOL-PERP-INTX, etc.)
- Implement RL position sizer for crypto

---

## 📝 Configuration Files

**Crypto Config:** `/opt/quantshift/config/crypto_config.yaml`
```yaml
simulated_capital: 10000  # Paper trading mode
symbols:
  - BTC-PERP-INTX
  - ETH-PERP-INTX
cycle_interval_seconds: 300  # 5 minutes
heartbeat_interval_seconds: 30
```

**Systemd Service:** `/etc/systemd/system/quantshift-crypto.service`
- Needs real Coinbase API credentials
- Currently has placeholder values

**Logs:**
- Output: `/opt/quantshift/logs/crypto-bot.log`
- Errors: `/opt/quantshift/logs/crypto-bot-error.log`

---

## 🔍 Debugging Commands

**Check bot status:**
```bash
ssh quantshift-primary "systemctl status quantshift-crypto"
```

**View logs:**
```bash
ssh quantshift-primary "tail -50 /opt/quantshift/logs/crypto-bot.log"
```

**Check database heartbeat:**
```bash
ssh quantshift-primary "PGPASSWORD='Cloudy_92!' psql -h 10.92.3.21 -U quantshift -d quantshift -c \"SELECT bot_name, status, last_heartbeat, NOW() - last_heartbeat FROM bot_status;\""
```

**Restart bot:**
```bash
ssh quantshift-primary "systemctl restart quantshift-crypto"
```

---

## 📚 Related Documentation

- **Bot Architecture:** `apps/bots/run_bot_v3.py`
- **Executor:** `packages/core/src/quantshift_core/executors/coinbase_executor.py`
- **Config:** `config/crypto_config.yaml`
- **Deployment:** Blue-green setup on CT100 (primary) and CT101 (standby)

---

**Summary:** Crypto bot is configured for paper trading but needs real Coinbase API credentials to function. Heartbeat issue affects both equity and crypto bots and needs investigation.
