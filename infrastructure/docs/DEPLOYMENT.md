# QuantShift Deployment Guide

## Deployment Architecture

### Hot-Standby (Bots)
- **Primary**: LXC 100 (10.92.3.27) - Active trading
- **Standby**: LXC 101 (10.92.3.28) - Automatic failover
- **Failover**: Automatic via HA Proxy health checks
- **Downtime**: Zero (seamless failover)

### Single Instance (Dashboard)
- **Dashboard**: LXC 137 (10.92.3.29) - Next.js UI
- **Failover**: None (future: can add LXC 138)
- **Downtime**: Brief during deployment (acceptable)

## Initial Setup

### 1. Clone Repo to Containers

```bash
# On Primary (LXC 100)
ssh root@10.92.3.27
git clone https://github.com/heybearc/quantshift.git /opt/quantshift
cd /opt/quantshift

# On Standby (LXC 101)
ssh root@10.92.3.28
git clone https://github.com/heybearc/quantshift.git /opt/quantshift
cd /opt/quantshift

# On Dashboard (LXC 137)
ssh root@10.92.3.29
git clone https://github.com/heybearc/quantshift.git /opt/quantshift
cd /opt/quantshift
```

### 2. Configure Environment Variables

```bash
# On Bot Containers (100, 101)
cat > /opt/quantshift/.env << EOF
DATABASE_URL=postgresql://quantshift_bot:Cloudy_92!@10.92.3.21:5432/quantshift
REDIS_URL=redis://localhost:6379/0
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
COINBASE_API_KEY=your_key
COINBASE_API_SECRET=your_secret
EOF

# On Dashboard Container (137)
cat > /opt/quantshift/apps/dashboard/.env << EOF
DATABASE_URL=postgresql://quantshift_dashboard:Cloudy_92!@10.92.3.21:5432/quantshift
EOF
```

### 3. Install Dependencies

```bash
# On Bot Containers (100, 101)
cd /opt/quantshift
pip install -e packages/core
pip install -e apps/bots/equity
pip install -e apps/bots/crypto

# On Dashboard Container (137)
cd /opt/quantshift/apps/dashboard
npm install
npx prisma generate
npm run build
```

### 4. Setup Services

```bash
# On Bot Containers (100, 101)
cp infrastructure/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable quantshift-equity
systemctl enable quantshift-crypto
systemctl start quantshift-equity
systemctl start quantshift-crypto

# On Dashboard Container (137)
npm install -g pm2
pm2 start apps/dashboard/ecosystem.config.js
pm2 save
pm2 startup
```

## Regular Deployments

### Deploy Bots (Hot-Standby)

```bash
# From your Mac
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift
./infrastructure/deployment/deploy-bots.sh
```

This deploys to BOTH containers simultaneously. HA Proxy handles failover.

### Deploy Dashboard

```bash
# From your Mac
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift
./infrastructure/deployment/deploy-dashboard.sh
```

This deploys to single dashboard container with PM2 reload (brief downtime).

## Rollback

### Rollback Bots

```bash
# On both containers
ssh root@10.92.3.27 'cd /opt/quantshift && git reset --hard HEAD~1 && systemctl restart quantshift-*'
ssh root@10.92.3.28 'cd /opt/quantshift && git reset --hard HEAD~1 && systemctl restart quantshift-*'
```

### Rollback Dashboard

```bash
# On dashboard container
ssh root@10.92.3.29 'cd /opt/quantshift && git reset --hard HEAD~1 && cd apps/dashboard && npm run build && pm2 reload quantshift-dashboard'
```

## Testing Failover

### Test Hot-Standby Failover

```bash
# Stop primary bot
ssh root@10.92.3.27 'systemctl stop quantshift-equity'

# HA Proxy should automatically route to standby (10.92.3.28)
# Check HA Proxy stats: http://10.92.3.26:8404
# Credentials: admin / Cloudy_92!

# Restart primary
ssh root@10.92.3.27 'systemctl start quantshift-equity'

# HA Proxy should route back to primary
```

## Monitoring

### Check Bot Status

```bash
# Primary
ssh root@10.92.3.27 'systemctl status quantshift-*'

# Standby
ssh root@10.92.3.28 'systemctl status quantshift-*'
```

### Check Dashboard Status

```bash
ssh root@10.92.3.29 'pm2 status'
ssh root@10.92.3.29 'pm2 logs quantshift-dashboard'
```

### HA Proxy Stats

Open: http://10.92.3.26:8404
Credentials: admin / Cloudy_92!

## Future: Dashboard Blue-Green

To add blue-green deployment for dashboard:

1. Create LXC 138 (10.92.3.30)
2. Clone repo to LXC 138
3. Update HA Proxy config to route dashboard traffic
4. Deploy to "green" (138), test, then switch traffic
5. Keep "blue" (137) as rollback
