# Deployment Strategy for Trading Bot Improvements
## How to Deploy Changes Without Interrupting Live Trading

---

## 🎯 The Challenge

**Problem:** You want to continuously improve your bots (add ML, better strategies, optimization) without:
- Interrupting live trades
- Losing money on bad code
- Causing downtime
- Creating split-brain scenarios

**Solution:** Multi-stage deployment with shadow mode and paper trading validation

---

## 🏗️ Recommended Architecture: 4-Environment Strategy

### **Environment 1: Development (Your Mac)**
**Purpose:** Write and test new code
- Full Agentic AI development (Windsurf + Claude)
- Unit tests and basic validation
- No real trading

### **Environment 2: Paper Trading (LXC 102 - NEW)**
**Purpose:** Test strategies with fake money
- Alpaca Paper Trading API
- Coinbase Sandbox API
- Real market data, fake orders
- Validate new strategies before risking capital

### **Environment 3: Shadow Mode (LXC 101 - Standby)**
**Purpose:** Run new code alongside production without trading
- Receives same market data as primary
- Generates signals but doesn't place orders
- Logs what it WOULD do
- Compare performance to primary

### **Environment 4: Production (LXC 100 - Primary)**
**Purpose:** Live trading with real money
- Only deploy after validation in all other environments
- Graceful deployment with position protection

---

## 📋 Deployment Workflow for Improvements

### **Phase 1: Development & Testing (1-3 days)**

```bash
# On your Mac
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift

# Create feature branch
git checkout -b feature/kelly-criterion-sizing

# Make changes with Windsurf/Claude
# ... implement improvements ...

# Run unit tests
pytest packages/core/tests -v
pytest apps/bots/equity/tests -v

# Commit changes
git add .
git commit -m "feat: add Kelly Criterion position sizing"
git push origin feature/kelly-criterion-sizing
```

**Validation:**
- ✅ Unit tests pass
- ✅ Type checking passes (mypy)
- ✅ Code review (if needed)

---

### **Phase 2: Paper Trading Validation (3-7 days)**

```bash
# Deploy to paper trading container (LXC 102)
ssh quantshift-paper
cd /opt/quantshift
git checkout feature/kelly-criterion-sizing
git pull

# Run with paper trading API
export APCA_API_BASE_URL=https://paper-api.alpaca.markets
systemctl restart quantshift-equity-paper

# Monitor for 3-7 days
tail -f /opt/quantshift/logs/equity-bot-paper.log
```

**Validation Metrics:**
- ✅ No crashes or errors
- ✅ Orders execute correctly
- ✅ Position sizing works as expected
- ✅ Win rate >= current production
- ✅ Risk metrics within bounds

**Decision Point:**
- If metrics good → Proceed to Phase 3
- If metrics bad → Back to development

---

### **Phase 3: Shadow Mode (7-14 days)**

```bash
# Merge to main
git checkout main
git merge feature/kelly-criterion-sizing
git push origin main

# Deploy to standby (shadow mode)
ssh quantshift-standby
cd /opt/quantshift
git pull origin main

# Enable shadow mode (don't place real orders)
export SHADOW_MODE=true
export LOG_SHADOW_TRADES=true
systemctl restart quantshift-equity

# Monitor shadow trades vs production
tail -f /opt/quantshift/logs/equity-bot-shadow.log
```

**Shadow Mode Logic:**
```python
class TradingBot:
    def __init__(self):
        self.shadow_mode = os.getenv("SHADOW_MODE", "false").lower() == "true"
    
    def execute_trade(self, signal):
        if self.shadow_mode:
            # Log what we WOULD do
            logger.info(
                "shadow_trade",
                action="would_execute",
                signal=signal,
                timestamp=datetime.now()
            )
            # Don't actually place order
            return
        
        # Real trading
        self.place_order(signal)
```

**Validation:**
- ✅ Shadow trades logged correctly
- ✅ Compare shadow performance to production
- ✅ No errors or crashes
- ✅ Resource usage acceptable
- ✅ Shadow performance >= production performance

**Decision Point:**
- If shadow performs better → Proceed to Phase 4
- If shadow performs worse → Investigate or rollback

---

### **Phase 4: Canary Deployment (1-3 days)**

```bash
# Disable shadow mode on standby
ssh quantshift-standby
export SHADOW_MODE=false
systemctl restart quantshift-equity

# Monitor standby with real trading (small positions)
# Standby will trade but primary is still main bot
```

**Validation:**
- ✅ Standby places real orders correctly
- ✅ No execution errors
- ✅ Position management works
- ✅ Risk controls functioning

---

### **Phase 5: Production Deployment (Graceful Switchover)**

```bash
# Deploy to primary with graceful shutdown
ssh quantshift-primary

# Graceful shutdown (closes positions, saves state)
systemctl stop quantshift-equity

# Update code
cd /opt/quantshift
git pull origin main

# Restart with new code
systemctl start quantshift-equity

# Verify startup
systemctl status quantshift-equity
tail -f /opt/quantshift/logs/equity-bot.log
```

**Graceful Shutdown Ensures:**
- ✅ All open positions closed or saved
- ✅ State persisted to Redis
- ✅ No orders left hanging
- ✅ Clean restart

---

## 🛡️ Protection Mechanisms

### **1. Position Protection During Deployment**

```python
class StateManager:
    def _handle_shutdown(self, signum, frame):
        logger.info("shutdown_initiated", saving_positions=True)
        
        # Get all open positions
        positions = self.bot.get_open_positions()
        
        # Save to Redis for recovery
        for pos in positions:
            self.save_position(pos['symbol'], {
                'quantity': pos['qty'],
                'entry_price': pos['avg_entry_price'],
                'stop_loss': pos['stop_loss'],
                'take_profit': pos['take_profit']
            })
        
        # Option 1: Close all positions (safest)
        if self.settings.close_on_shutdown:
            self.bot.close_all_positions()
        
        # Option 2: Leave positions open (riskier but maintains strategy)
        # Positions will be recovered on restart
        
        sys.exit(0)
```

### **2. Deployment Window Strategy**

**Best Times to Deploy:**
- ✅ **Market Close** (4:00 PM ET) - No active trading
- ✅ **Low Volatility Periods** - Less risk
- ✅ **Weekends** (for crypto bot) - Lower volume

**Avoid Deploying:**
- ❌ Market Open (9:30 AM ET) - High volatility
- ❌ During active trades - Risk of orphaned orders
- ❌ Major news events - Unpredictable moves

### **3. Rollback Plan**

```bash
# If something goes wrong, instant rollback
ssh quantshift-primary
cd /opt/quantshift

# Rollback to previous commit
git reset --hard HEAD~1

# Restart with old code
systemctl restart quantshift-equity

# Verify
systemctl status quantshift-equity
```

**Automated Rollback Triggers:**
- ❌ Error rate > 5%
- ❌ Win rate drops > 10%
- ❌ Drawdown > 15%
- ❌ Service crashes

---

## 🎯 Deployment Strategy by Improvement Type

### **Low-Risk Changes (Deploy Quickly)**
- Bug fixes
- Logging improvements
- Dashboard updates
- Documentation

**Process:** Dev → Paper (1 day) → Production

### **Medium-Risk Changes (Standard Process)**
- New indicators
- Parameter adjustments
- Stop loss improvements
- Position sizing tweaks

**Process:** Dev → Paper (3 days) → Shadow (7 days) → Production

### **High-Risk Changes (Full Validation)**
- New strategies
- Machine learning models
- Major algorithm changes
- Risk management overhauls

**Process:** Dev → Paper (7 days) → Shadow (14 days) → Canary (3 days) → Production

---

## 📊 Monitoring During Deployment

### **Real-Time Metrics to Watch:**

```python
class DeploymentMonitor:
    def check_health(self):
        metrics = {
            # Performance
            'win_rate': self.calculate_win_rate(),
            'profit_factor': self.calculate_profit_factor(),
            'sharpe_ratio': self.calculate_sharpe(),
            
            # Risk
            'max_drawdown': self.calculate_drawdown(),
            'current_exposure': self.get_total_exposure(),
            'position_count': len(self.get_positions()),
            
            # System
            'error_rate': self.get_error_rate(),
            'latency': self.get_avg_latency(),
            'uptime': self.get_uptime()
        }
        
        # Alert if any metric out of bounds
        if metrics['win_rate'] < 0.50:
            self.alert("Win rate dropped below 50%")
        if metrics['max_drawdown'] > 0.20:
            self.alert("Drawdown exceeded 20%")
        if metrics['error_rate'] > 0.05:
            self.alert("Error rate above 5%")
        
        return metrics
```

---

## 🚀 Recommended Setup for Your System

### **Add Paper Trading Container (LXC 102)**

```bash
# Create new container
pct create 102 local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
  --hostname quantshift-paper \
  --memory 4096 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=10.92.3.30/24,gw=10.92.3.1

# Start and configure
pct start 102
pct enter 102

# Clone repo and setup
git clone https://github.com/heybearc/quantshift.git /opt/quantshift
cd /opt/quantshift
python3 -m venv venv
source venv/bin/activate
pip install -e packages/core
pip install -e apps/bots/equity

# Configure for paper trading
cat > /opt/quantshift/.env << EOF
APCA_API_KEY_ID=your_paper_key
APCA_API_SECRET_KEY=your_paper_secret
APCA_API_BASE_URL=https://paper-api.alpaca.markets
DATABASE_URL=postgresql://quantshift_bot:Cloudy_92!@10.92.3.21:5432/quantshift
REDIS_URL=redis://:Cloudy_92!@localhost:6379/1
EOF
```

### **Update SSH Config**

```bash
# Add to ~/.ssh/config
Host quantshift-paper
    HostName 10.92.3.30
    User root
    IdentityFile ~/.ssh/id_rsa
```

---

## 💡 Best Practices

### **DO:**
- ✅ Test in paper trading first (always)
- ✅ Use shadow mode for new strategies
- ✅ Deploy during market close
- ✅ Monitor metrics closely after deployment
- ✅ Have rollback plan ready
- ✅ Save state before shutdown
- ✅ Use graceful shutdown handlers

### **DON'T:**
- ❌ Deploy during active trades
- ❌ Skip paper trading validation
- ❌ Deploy major changes on Friday (weekend risk)
- ❌ Deploy without monitoring
- ❌ Ignore error logs
- ❌ Force kill bot processes (use systemctl stop)

---

## 🎯 Summary: Your Deployment Strategy

**For Bot Improvements:**

1. **Develop** on Mac with Windsurf/Claude
2. **Test** in paper trading (3-7 days)
3. **Shadow** on standby (7-14 days)
4. **Canary** on standby with real trades (1-3 days)
5. **Deploy** to primary during market close

**This gives you:**
- ✅ Zero downtime
- ✅ No interrupted trades
- ✅ Full validation before production
- ✅ Easy rollback if needed
- ✅ Position protection
- ✅ Continuous improvement

**You DON'T need blue-green because:**
- You can't have two bots trading same account
- Hot-standby + canary is better for trading
- State management handles failover
- Graceful shutdown protects positions
