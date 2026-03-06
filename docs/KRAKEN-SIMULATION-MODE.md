# Kraken Simulation Mode - Testing Guide

**Created:** 2026-03-06  
**Status:** Ready for testing

---

## Overview

The Kraken bot can run in **simulation mode** for testing without real money. This mode:
- ✅ Uses real Kraken market data (live prices)
- ✅ Simulates all trading operations (orders, positions, P&L)
- ✅ Tracks positions and account balance in memory
- ✅ Tests all bot logic without financial risk
- ✅ No API keys required (optional for market data)

---

## How It Works

### Simulation Mode
- **Market Data:** Fetches real prices from Kraken API
- **Orders:** Simulated execution at current market price
- **Positions:** Tracked in memory with P&L calculations
- **Account:** Starts with $5,000 simulated capital (configurable)
- **Margin:** Simulates margin requirements and liquidation
- **Stops:** Simulates stop-loss and take-profit orders

### What Gets Tested
1. ✅ Strategy signal generation
2. ✅ Order placement logic
3. ✅ Position tracking
4. ✅ Margin calculations
5. ✅ Stop-loss/take-profit execution
6. ✅ Trailing stops
7. ✅ Risk management
8. ✅ P&L calculations
9. ✅ Long and short positions
10. ✅ Leverage handling

### What Doesn't Get Tested
- ❌ Real API order placement
- ❌ Actual slippage
- ❌ Real execution latency
- ❌ API rate limits
- ❌ Order rejection scenarios

---

## Configuration

### Enable Simulation Mode

Edit `config/kraken_config.yaml`:

```yaml
executor:
  type: "kraken"
  simulation_mode: true  # ← Set to true for simulation
  max_leverage: 2.0
  simulated_capital: 5000  # Starting capital for simulation
```

### Disable Simulation Mode (Go Live)

```yaml
executor:
  type: "kraken"
  simulation_mode: false  # ← Set to false for live trading
  max_leverage: 2.0
```

**IMPORTANT:** When `simulation_mode: false`, you MUST set environment variables:
```bash
export KRAKEN_API_KEY="your_real_api_key"
export KRAKEN_API_SECRET="your_real_api_secret"
```

---

## Running Simulation Mode

### On Local Machine (Mac)

```bash
cd /Users/cory/Projects/quantshift

# Activate virtual environment (if using one)
source venv/bin/activate

# Install krakenex if not already installed
pip install krakenex==2.2.0

# Run the bot
python apps/bots/run_bot_v3.py --config config/kraken_config.yaml
```

### On Bot Container (CT 100 or CT 101)

```bash
ssh root@10.92.3.27  # or 10.92.3.28 for standby

cd /opt/quantshift

# Install krakenex
source venv/bin/activate
pip install krakenex==2.2.0

# Run the bot
python apps/bots/run_bot_v3.py --config config/kraken_config.yaml
```

### As Systemd Service

Create `/etc/systemd/system/quantshift-kraken-sim.service`:

```ini
[Unit]
Description=QuantShift Kraken Bot (Simulation Mode)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/quantshift
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/quantshift/venv/bin/python apps/bots/run_bot_v3.py --config config/kraken_config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
systemctl daemon-reload
systemctl start quantshift-kraken-sim
systemctl enable quantshift-kraken-sim
systemctl status quantshift-kraken-sim
```

View logs:
```bash
journalctl -u quantshift-kraken-sim -f
```

---

## Monitoring Simulation

### Check Bot Logs

Look for simulation indicators:
```
[INFO] SimulatedKrakenExecutor initialized with ... starting capital=$5,000.00
[INFO] [SIMULATED] Margin order executed: BUY 0.1 XXBTZUSD @ $50000.00 leverage=2.0x
[INFO] [SIMULATED] Stop order placed: XXBTZUSD qty=0.1 stop=$49000.00
[INFO] [SIMULATED] Position closed: XXBTZUSD P&L=$150.00
```

### Get Simulation Stats

The executor tracks:
- Starting capital
- Current equity
- Total P&L ($ and %)
- Open positions
- Total trades
- Margin used
- Free margin

Access via bot logs or add API endpoint to expose stats.

---

## Testing Checklist

### Phase 1: Basic Functionality (1 hour)
- [ ] Bot starts without errors
- [ ] Fetches real market data from Kraken
- [ ] Generates signals from strategies
- [ ] Places simulated orders
- [ ] Tracks positions correctly
- [ ] Calculates P&L accurately

### Phase 2: Long Positions (2 hours)
- [ ] Opens long position (BUY)
- [ ] Tracks unrealized P&L
- [ ] Places stop-loss order
- [ ] Stop-loss triggers on price drop
- [ ] Position closes with realized P&L
- [ ] Cash balance updates correctly

### Phase 3: Short Positions (2 hours)
- [ ] Opens short position (SELL)
- [ ] Tracks unrealized P&L (inverse)
- [ ] Places stop-loss order
- [ ] Stop-loss triggers on price rise
- [ ] Position closes with realized P&L
- [ ] Cash balance updates correctly

### Phase 4: Margin & Leverage (2 hours)
- [ ] Uses 2x leverage correctly
- [ ] Calculates margin requirements
- [ ] Tracks margin usage
- [ ] Prevents over-leveraging
- [ ] Monitors margin levels
- [ ] Simulates liquidation scenarios

### Phase 5: Trailing Stops (2 hours)
- [ ] Trailing stop activates on profit
- [ ] High water mark tracked
- [ ] Stop price trails correctly
- [ ] Stop triggers on pullback
- [ ] Position closes with profit locked

### Phase 6: Risk Management (2 hours)
- [ ] Position size limits enforced
- [ ] Max positions limit enforced
- [ ] Daily loss limit enforced
- [ ] Portfolio heat calculated
- [ ] Circuit breaker triggers

### Phase 7: Multi-Day Testing (1-2 days)
- [ ] Bot runs continuously for 24+ hours
- [ ] No memory leaks
- [ ] No crashes or errors
- [ ] Multiple trades executed
- [ ] P&L tracking accurate
- [ ] Positions sync correctly

---

## Success Criteria

**Before going live, simulation must demonstrate:**

1. ✅ **Stability:** 24+ hours without crashes
2. ✅ **Accuracy:** P&L calculations match expected
3. ✅ **Functionality:** All order types work (market, stop, limit)
4. ✅ **Risk Controls:** All limits enforced correctly
5. ✅ **Positions:** Long and short positions work
6. ✅ **Margin:** Leverage and margin calculations correct
7. ✅ **Stops:** Trailing stops activate and trigger
8. ✅ **Performance:** Strategies generate reasonable signals

**If ANY criteria fail:** Fix issues and restart testing

---

## Going Live - Transition Steps

### Step 1: Verify Simulation Success
- [ ] All test checklist items passed
- [ ] Bot ran for 24+ hours without issues
- [ ] P&L tracking accurate
- [ ] No errors in logs

### Step 2: Get Kraken Account Ready
- [ ] Account created and KYC verified
- [ ] Margin trading enabled
- [ ] Account funded ($500-5000)
- [ ] API keys generated with correct permissions

### Step 3: Update Configuration
Edit `config/kraken_config.yaml`:
```yaml
executor:
  simulation_mode: false  # ← CHANGE THIS
```

### Step 4: Set Environment Variables
On bot container:
```bash
# Add to /opt/quantshift/.env
KRAKEN_API_KEY=your_real_api_key_here
KRAKEN_API_SECRET=your_real_api_secret_here
```

### Step 5: Deploy to STANDBY First
```bash
ssh root@10.92.3.28  # STANDBY container

cd /opt/quantshift
git pull origin main

# Verify .env has real API keys
cat .env | grep KRAKEN

# Restart bot
systemctl restart quantshift-kraken
systemctl status quantshift-kraken

# Monitor logs closely
journalctl -u quantshift-kraken -f
```

### Step 6: Test on STANDBY (1-2 days)
- [ ] Bot connects to Kraken successfully
- [ ] Places real orders (small amounts)
- [ ] Orders appear in Kraken UI
- [ ] Positions tracked correctly
- [ ] Stop orders placed on exchange
- [ ] No API errors

### Step 7: Deploy to PRIMARY
```bash
ssh root@10.92.3.27  # PRIMARY container

cd /opt/quantshift
git pull origin main

# Verify .env has real API keys
cat .env | grep KRAKEN

# Start bot
systemctl start quantshift-kraken
systemctl enable quantshift-kraken
systemctl status quantshift-kraken

# Monitor logs
journalctl -u quantshift-kraken -f
```

### Step 8: Monitor Production
- Check dashboard for all 3 bots (equity, coinbase, kraken)
- Verify positions showing correctly
- Monitor P&L calculations
- Watch for any errors
- Start with small capital, increase gradually

---

## Troubleshooting

### "krakenex library not installed"
```bash
pip install krakenex==2.2.0
```

### "Kraken API credentials not found"
**In simulation mode:** This is OK, API keys are optional  
**In live mode:** Set KRAKEN_API_KEY and KRAKEN_API_SECRET environment variables

### "Cannot get price for symbol"
- Check internet connection
- Verify symbol format (XXBTZUSD not BTC-USD)
- Check Kraken API status

### Simulation shows $0 P&L
- Check if strategies are generating signals
- Verify market data is being fetched
- Check logs for errors

### Bot crashes on startup
- Check Python version (3.8+)
- Verify all dependencies installed
- Check config file syntax (YAML)
- Review logs for error details

---

## What You Need to Provide (When Ready for Live)

When simulation testing is complete and you're ready to go live, provide:

```bash
# Kraken API credentials
KRAKEN_API_KEY=your_api_key_here
KRAKEN_API_SECRET=your_private_key_here
```

**How to send securely:**
- DM in Slack/Discord
- Paste in terminal (not in chat history)
- Use password manager share feature
- Or add directly to container .env file yourself

**API Key Permissions (verify these are checked):**
- ✅ Query Funds
- ✅ Query Open Orders & Trades
- ✅ Query Closed Orders & Trades
- ✅ Create & Modify Orders
- ✅ Cancel/Close Orders
- ❌ Withdraw Funds (MUST be unchecked)

---

## Summary

**Simulation Mode:**
- Zero risk testing with real market data
- Tests all bot logic and strategies
- No API keys required
- Perfect for development and validation

**Live Mode:**
- Real money trading
- Requires Kraken account and API keys
- Start small ($500) and scale up
- Deploy to STANDBY first, then PRIMARY

**Timeline:**
- Simulation testing: 1-2 days
- Kraken account setup: 1-3 days (KYC + funding)
- STANDBY testing: 1-2 days
- Production deployment: 1 hour

**Total: ~1 week from simulation to production**
