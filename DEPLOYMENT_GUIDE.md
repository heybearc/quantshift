# QuantShift Production Deployment Guide

## 🎯 Overview

Deploy the QuantShift Admin Platform and Equity Bot to production infrastructure with hot-standby failover.

---

## 📦 Infrastructure

### **Containers**
- **Admin Platform:** LXC 137 (10.92.3.29) - Next.js on port 3001
- **Equity Bot Primary:** LXC 100 (10.92.3.27) - Hot-standby active
- **Equity Bot Standby:** LXC 101 (10.92.3.28) - Hot-standby passive
- **Database:** LXC 131 (10.92.3.21) - PostgreSQL shared

### **Domains**
- `trader.cloudigan.net` - Main dashboard
- `api.trader.cloudigan.net` - Bot APIs (optional)

---

## 🚀 Deployment Steps

### **Step 1: Deploy Admin Platform to LXC 137**

**SSH to LXC 137:**
```bash
ssh root@10.92.3.29
```

**Clone repository:**
```bash
cd /opt
git clone https://github.com/heybearc/quantshift.git
cd quantshift/apps/admin-web
```

**Install dependencies:**
```bash
npm install
```

**Create environment file:**
```bash
cat > .env.local << 'EOF'
DATABASE_URL="postgresql://quantshift:Cloudy_92!@10.92.3.21:5432/quantshift"
JWT_SECRET="your-secret-key-change-in-production-make-it-long-and-random"
NEXTAUTH_URL="http://trader.cloudigan.net:3001"
NODE_ENV="production"
EOF
```

**Build application:**
```bash
npm run build
```

**Create systemd service:**
```bash
cat > /etc/systemd/system/quantshift-admin.service << 'EOF'
[Unit]
Description=QuantShift Admin Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/quantshift/apps/admin-web
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF
```

**Start service:**
```bash
systemctl daemon-reload
systemctl enable quantshift-admin
systemctl start quantshift-admin
systemctl status quantshift-admin
```

**Verify:**
```bash
curl http://localhost:3001
```

---

### **Step 2: Deploy Equity Bot to LXC 100 (Primary)**

**SSH to LXC 100:**
```bash
ssh root@10.92.3.27
```

**Clone repository:**
```bash
cd /opt
git clone https://github.com/heybearc/quantshift.git
cd quantshift/apps/bots/equity
```

**Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
pip install -e /opt/quantshift/packages/core
```

**Create environment file:**
```bash
cat > .env << 'EOF'
APCA_API_KEY_ID=your_alpaca_key
APCA_API_SECRET_KEY=your_alpaca_secret
APCA_API_BASE_URL=https://paper-api.alpaca.markets
DATABASE_URL=postgresql://quantshift:Cloudy_92!@10.92.3.21:5432/quantshift
EOF
```

**Create systemd service:**
```bash
cat > /etc/systemd/system/quantshift-equity-bot.service << 'EOF'
[Unit]
Description=QuantShift Equity Bot
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/quantshift/apps/bots/equity
ExecStart=/opt/quantshift/apps/bots/equity/venv/bin/python run_bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
```

**Start service:**
```bash
systemctl daemon-reload
systemctl enable quantshift-equity-bot
systemctl start quantshift-equity-bot
systemctl status quantshift-equity-bot
```

**Check logs:**
```bash
journalctl -u quantshift-equity-bot -f
```

---

### **Step 3: Deploy Equity Bot to LXC 101 (Standby)**

**Repeat Step 2 on LXC 101 (10.92.3.28)**

Same exact process as LXC 100. Both containers run identical code.

---

### **Step 4: Initialize Database**

**SSH to admin platform (LXC 137):**
```bash
ssh root@10.92.3.29
cd /opt/quantshift/apps/admin-web
```

**Run Prisma migrations:**
```bash
npx prisma generate
npx prisma db push
```

**Seed admin user:**
```bash
npm run db:init
```

**Verify database:**
```bash
psql -h 10.92.3.21 -U quantshift -d quantshift -c "SELECT * FROM \"User\";"
```

---

### **Step 5: Configure Nginx/NPM**

**Point domain to admin platform:**
- Domain: `trader.cloudigan.net`
- Target: `http://10.92.3.29:3001`
- SSL: Enable with Let's Encrypt

**Optional API domain:**
- Domain: `api.trader.cloudigan.net`
- Target: Load balance between LXC 100 & 101

---

### **Step 6: Configure HA Proxy (Optional)**

For hot-standby failover between LXC 100 & 101:

**Create HAProxy config:**
```haproxy
frontend equity_bot_api
    bind *:8080
    default_backend equity_bots

backend equity_bots
    balance roundrobin
    option httpchk GET /health
    server primary 10.92.3.27:8080 check
    server standby 10.92.3.28:8080 check backup
```

---

## ✅ Verification

### **1. Admin Platform**
```bash
curl http://trader.cloudigan.net:3001
# Should return HTML
```

### **2. Login**
- URL: http://trader.cloudigan.net:3001
- Email: corya1992@gmail.com
- Password: admin123

### **3. Dashboard**
- Wait 60 seconds for bot data
- Verify bot status shows "RUNNING"
- Check account equity displays
- Verify positions appear (if any)

### **4. Bot Logs**
```bash
# On LXC 100
journalctl -u quantshift-equity-bot -f

# Should see:
# - Connected to Alpaca
# - Connected to database
# - State updated
# - No errors
```

### **5. Database**
```bash
psql -h 10.92.3.21 -U quantshift -d quantshift

# Check bot status
SELECT * FROM "BotStatus" WHERE "botName" = 'equity-bot';

# Check positions
SELECT * FROM "Position" WHERE "botName" = 'equity-bot';
```

---

## 🔧 Troubleshooting

### **Admin Platform Won't Start**
```bash
# Check logs
journalctl -u quantshift-admin -n 50

# Check port
netstat -tlnp | grep 3001

# Rebuild
cd /opt/quantshift/apps/admin-web
npm run build
systemctl restart quantshift-admin
```

### **Bot Won't Connect to Database**
```bash
# Test connection
psql -h 10.92.3.21 -U quantshift -d quantshift

# Check password in .env
cat /opt/quantshift/apps/bots/equity/.env

# Check DATABASE_URL
echo $DATABASE_URL
```

### **Bot Won't Connect to Alpaca**
```bash
# Check API keys
cat /opt/quantshift/apps/bots/equity/.env | grep APCA

# Test API
curl -H "APCA-API-KEY-ID: your_key" \
     -H "APCA-API-SECRET-KEY: your_secret" \
     https://paper-api.alpaca.markets/v2/account
```

---

## 📊 Monitoring

### **Service Status**
```bash
# Admin platform
systemctl status quantshift-admin

# Equity bot (primary)
ssh root@10.92.3.27 'systemctl status quantshift-equity-bot'

# Equity bot (standby)
ssh root@10.92.3.28 'systemctl status quantshift-equity-bot'
```

### **Logs**
```bash
# Admin platform
journalctl -u quantshift-admin -f

# Equity bot
journalctl -u quantshift-equity-bot -f
```

### **Database Queries**
```sql
-- Bot status
SELECT "botName", status, "lastHeartbeat", "accountEquity" 
FROM "BotStatus" 
ORDER BY "lastHeartbeat" DESC;

-- Recent trades
SELECT symbol, side, quantity, "entryPrice", "exitPrice", pnl 
FROM "Trade" 
WHERE "botName" = 'equity-bot' 
ORDER BY "enteredAt" DESC 
LIMIT 10;

-- Current positions
SELECT symbol, quantity, "currentPrice", "unrealizedPl" 
FROM "Position" 
WHERE "botName" = 'equity-bot';
```

---

## 🔄 Updates

### **Update Admin Platform**
```bash
ssh root@10.92.3.29
cd /opt/quantshift
git pull origin main
cd apps/admin-web
npm install
npm run build
systemctl restart quantshift-admin
```

### **Update Equity Bot**
```bash
# Primary
ssh root@10.92.3.27
cd /opt/quantshift
git pull origin main
cd apps/bots/equity
source venv/bin/activate
pip install -r requirements.txt
systemctl restart quantshift-equity-bot

# Standby
ssh root@10.92.3.28
cd /opt/quantshift
git pull origin main
cd apps/bots/equity
source venv/bin/activate
pip install -r requirements.txt
systemctl restart quantshift-equity-bot
```

---

## 🎉 Success Criteria

- ✅ Admin platform accessible at trader.cloudigan.net:3001
- ✅ Login works with admin credentials
- ✅ Dashboard shows bot status as "RUNNING"
- ✅ Account equity displays correctly
- ✅ Positions update in real-time
- ✅ Trades appear in trades page
- ✅ Performance metrics calculate
- ✅ Bot logs show no errors
- ✅ Database contains bot data
- ✅ Both LXC 100 & 101 running (hot-standby)

---

**Platform is ready for production! 🚀**
