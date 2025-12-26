# QuantShift Testing Guide

## Local Testing Setup

### Prerequisites

1. **PostgreSQL Database Running**
   - Database: `quantshift` on LXC 131 (10.92.3.21)
   - User: `quantshift`
   - Password: `Cloudy_92!`

2. **Environment Variables**
   - Alpaca API keys in equity bot
   - Database URL configured

---

## Test 1: Admin Platform Standalone

**Start the admin platform:**

```bash
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift/apps/admin-web
npm run dev
```

**Access:** http://localhost:3001

**Login:**
- Email: `corya1992@gmail.com`
- Password: `admin123`

**Verify:**
- ✅ Login successful
- ✅ Dashboard loads (shows "no data" initially)
- ✅ All pages accessible (Trades, Positions, Performance, Email, Users, Settings)
- ✅ Navigation works
- ✅ No console errors

---

## Test 2: Equity Bot Standalone

**Install dependencies:**

```bash
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift/apps/bots/equity
pip install -r requirements.txt
```

**Run the bot:**

```bash
python run_bot.py
```

**Expected Output:**

```
INFO - Initialized equity-bot with Alpaca paper trading
INFO - Connected to admin platform database
INFO - Starting equity-bot...
INFO - State updated - Balance: $10,000.00, Positions: 0, Unrealized P&L: $0.00
```

**Verify:**
- ✅ Bot starts without errors
- ✅ Connects to PostgreSQL
- ✅ Fetches Alpaca account data
- ✅ Updates every 60 seconds

---

## Test 3: End-to-End Integration

**Terminal 1: Admin Platform**

```bash
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift/apps/admin-web
npm run dev
```

**Terminal 2: Equity Bot**

```bash
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift/apps/bots/equity
python run_bot.py
```

**Wait 60 seconds for first update, then verify:**

### Dashboard Page
- ✅ Bot status shows "RUNNING" (green)
- ✅ Account equity displays correctly
- ✅ Stats cards show real data
- ✅ Last heartbeat timestamp updates

### Trades Page
- ✅ Shows trades from Alpaca (if any)
- ✅ Search and filters work
- ✅ Pagination works

### Positions Page
- ✅ Shows current positions (if any)
- ✅ P&L calculations correct
- ✅ Market values update

### Performance Page
- ✅ Metrics calculate correctly
- ✅ Win rate displays
- ✅ Daily performance table populates

---

## Test 4: Database Verification

**Connect to PostgreSQL:**

```bash
psql -h 10.92.3.21 -U quantshift -d quantshift
```

**Check bot status:**

```sql
SELECT * FROM "BotStatus" WHERE "botName" = 'equity-bot';
```

**Expected:**
- Status: RUNNING
- Last heartbeat within last 60 seconds
- Account values populated

**Check positions:**

```sql
SELECT * FROM "Position" WHERE "botName" = 'equity-bot';
```

**Check trades:**

```sql
SELECT * FROM "Trade" WHERE "botName" = 'equity-bot' ORDER BY "enteredAt" DESC LIMIT 10;
```

---

## Test 5: Error Handling

### Test Database Connection Failure

**Stop PostgreSQL temporarily:**

```bash
# On LXC 131
sudo systemctl stop postgresql
```

**Verify bot handles gracefully:**
- ✅ Bot continues running
- ✅ Logs warning about database connection
- ✅ No crashes

**Restart PostgreSQL:**

```bash
sudo systemctl start postgresql
```

### Test Alpaca API Failure

**Use invalid API keys temporarily**

**Verify:**
- ✅ Bot logs error
- ✅ Falls back to default state
- ✅ Continues running

---

## Test 6: Real Trading Simulation

**If bot has positions:**

1. **Check Dashboard**
   - Real-time position updates
   - Unrealized P&L changes with market

2. **Check Positions Page**
   - Current prices update
   - Market values recalculate
   - P&L percentages accurate

3. **Wait for Trade**
   - New trade appears in Trades page
   - Position updates in Positions page
   - Dashboard stats update

---

## Common Issues & Solutions

### Issue: "Could not connect to admin platform database"

**Solution:**
```bash
# Test connection
psql -h 10.92.3.21 -U quantshift -d quantshift

# If fails, check:
# 1. PostgreSQL is running on LXC 131
# 2. Network connectivity
# 3. Firewall rules
```

### Issue: "Module 'database_writer' not found"

**Solution:**
```bash
# Make sure you're in the equity bot directory
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift/apps/bots/equity
python run_bot.py
```

### Issue: Admin platform shows "No data"

**Solution:**
```bash
# Wait 60 seconds for first bot update
# Check bot logs for database errors
# Verify bot is running
```

### Issue: "psycopg2 not found"

**Solution:**
```bash
pip install psycopg2-binary
```

---

## Success Criteria

**✅ All tests pass when:**

1. Admin platform loads and all pages work
2. Equity bot starts and connects to database
3. Dashboard shows real bot data within 60 seconds
4. Positions and trades display correctly
5. No errors in bot logs or browser console
6. Database tables populate with correct data
7. Bot handles connection failures gracefully

---

## Next Steps After Testing

1. **If all tests pass:**
   - Deploy admin platform to LXC 137
   - Deploy equity bot to LXC 100/101
   - Configure production environment variables
   - Set up monitoring

2. **If tests fail:**
   - Check logs for specific errors
   - Verify database connectivity
   - Confirm API credentials
   - Review error messages

---

## Production Deployment Checklist

- [ ] Local testing complete
- [ ] Database schema verified
- [ ] Admin platform builds successfully
- [ ] Bot runs without errors
- [ ] All pages display data correctly
- [ ] Error handling tested
- [ ] Ready for LXC deployment

---

**Status: Ready for Testing** 🚀

Run the tests above to verify the complete integration works correctly before deploying to production.
