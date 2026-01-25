# QuantShift Trading Platform - User Guide

## Overview

The QuantShift Trading Platform is a real-time monitoring and management system for your algorithmic trading bots. It provides live visibility into bot status, positions, trades, and performance metrics.

## Access

- **URL**: https://trader.cloudigan.net
- **Platform Server**: 10.92.3.29:3001 (quantshift-platform)
- **Bot Server**: 10.92.3.27 (quantshift-primary)
- **Database**: 10.92.3.21 (PostgreSQL)

## Architecture

### Components

1. **Trading Bots**
   - **Equity Bot**: Paper trading on Alpaca Markets
   - **Crypto Bot**: (Not yet deployed)
   - Location: `/opt/quantshift/apps/bots/`
   - Service: `systemctl status quantshift-equity.service`

2. **Platform Dashboard**
   - Next.js 14 application with TypeScript
   - Real-time data updates every 5 seconds
   - Location: `/opt/quantshift/apps/dashboard/`
   - Process Manager: PM2 (`pm2 status quantshift-platform`)

3. **State Management**
   - Redis: Bot state, heartbeats, positions
   - PostgreSQL: Trade history, persistent data
   - Redis Keys: `bot:{bot-name}:state`, `bot:{bot-name}:heartbeat`, `bot:{bot-name}:position:{symbol}`

## Platform Features

### 1. Dashboard Home
- Real-time bot status (running/stopped)
- Active bot count
- Open positions count
- Today's trade count
- Account balance
- Quick navigation to all sections

### 2. Bots Page
- Detailed bot status for each bot
- Last heartbeat timestamp
- Bot state information (mode, strategy, balance)
- Position count per bot

### 3. Positions Page
- Live open positions across all bots
- Entry price, current price, unrealized P&L
- Position size and entry time
- Symbol and bot name

### 4. Trades Page
- Historical trade data
- Trade side (BUY/SELL), quantity, price
- Total value and commission
- Timestamp and order status
- Filterable by bot

### 5. Strategies Page
- Performance metrics by strategy
- Win rate, total trades, P&L
- Strategy-specific statistics
- (Currently showing placeholder data)

### 6. Analytics Page
- Performance charts and metrics
- Risk analysis
- (Under development)

### 7. Settings Page
- Bot configuration
- Risk management settings
- Notification preferences
- (Under development)

## Bot Management

### Check Bot Status

```bash
# SSH to primary container
ssh quantshift-primary

# Check service status
systemctl status quantshift-equity.service

# View logs
tail -f /opt/quantshift/logs/equity-bot.log
tail -f /opt/quantshift/logs/equity-bot-error.log

# Check Redis state
redis-cli -a "Cloudy_92!" get "bot:equity-bot:state"
redis-cli -a "Cloudy_92!" get "bot:equity-bot:heartbeat"
```

### Restart Bot

```bash
ssh quantshift-primary
systemctl restart quantshift-equity.service
```

### Update Bot Code

```bash
ssh quantshift-primary
cd /opt/quantshift
git pull origin main
systemctl restart quantshift-equity.service
```

## Platform Management

### Check Platform Status

```bash
# SSH to platform container
ssh quantshift-platform

# Check PM2 status
pm2 status

# View logs
pm2 logs quantshift-platform --lines 50
```

### Restart Platform

```bash
ssh quantshift-platform
pm2 restart quantshift-platform
```

### Update Platform Code

```bash
ssh quantshift-platform
cd /opt/quantshift
git pull origin main
cd apps/dashboard
npm run build
pm2 restart quantshift-platform
```

## API Endpoints

All endpoints are accessible at `http://10.92.3.29:3001/api/` or `https://trader.cloudigan.net/api/`

### GET /api/bots
Returns status of all bots including state, heartbeat, and position count.

**Response:**
```json
{
  "bots": [
    {
      "name": "equity-bot",
      "status": "running",
      "state": {
        "status": "running",
        "mode": "paper",
        "strategy": "multi-strategy",
        "account_balance": 10000,
        "positions_count": 0
      },
      "heartbeat": "2025-12-25T18:02:39.920623",
      "positions": 0,
      "lastUpdate": "2025-12-25T18:02:09.915776"
    }
  ]
}
```

### GET /api/stats
Returns overall portfolio statistics.

**Response:**
```json
{
  "totalPositions": 0,
  "unrealizedPnl": 0,
  "todayTrades": 0,
  "winRate": 0,
  "realizedPnl": 0,
  "accountBalance": 10000
}
```

### GET /api/positions
Returns all open positions across all bots.

**Response:**
```json
{
  "positions": []
}
```

### GET /api/trades?limit=50&bot=equity-bot
Returns trade history with optional filters.

**Query Parameters:**
- `limit`: Number of trades to return (default: 50)
- `bot`: Filter by bot name (optional)

## Database Schema

### Trades Table
```sql
CREATE TABLE trades (
  id SERIAL PRIMARY KEY,
  bot_name VARCHAR(50) NOT NULL,
  symbol VARCHAR(20) NOT NULL,
  side VARCHAR(10) NOT NULL,
  quantity DECIMAL(20,8) NOT NULL,
  price DECIMAL(20,8) NOT NULL,
  total_value DECIMAL(20,2) NOT NULL,
  commission DECIMAL(20,8) DEFAULT 0,
  order_id VARCHAR(100),
  status VARCHAR(20) NOT NULL,
  timestamp TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);
```

### Positions Table
```sql
CREATE TABLE positions (
  id SERIAL PRIMARY KEY,
  symbol VARCHAR(50) NOT NULL,
  quantity FLOAT NOT NULL,
  entry_price FLOAT NOT NULL,
  current_price FLOAT NOT NULL,
  entry_time TIMESTAMP NOT NULL,
  bot_name VARCHAR(50) NOT NULL
);
```

## Troubleshooting

### Bot Shows as Stopped
1. Check if bot service is running: `systemctl status quantshift-equity.service`
2. Check bot logs for errors: `tail -f /opt/quantshift/logs/equity-bot-error.log`
3. Verify Redis connection: `redis-cli -a "Cloudy_92!" ping`
4. Check heartbeat: `redis-cli -a "Cloudy_92!" get "bot:equity-bot:heartbeat"`

### Platform Not Loading
1. Check PM2 status: `pm2 status`
2. Check platform logs: `pm2 logs quantshift-platform`
3. Verify Redis connection from platform
4. Check if port 3001 is accessible

### No Data Showing
1. Verify bot is writing to Redis
2. Check Redis connection from platform
3. Verify database connection
4. Check API endpoints directly: `curl http://localhost:3001/api/bots`

### API Errors
1. Check platform logs for error details
2. Verify environment variables in `.env.local`
3. Check database connectivity
4. Verify Redis connectivity

## Environment Variables

### Platform (.env.local)
```bash
DATABASE_URL=postgresql://quantshift_bot:Cloudy_92!@10.92.3.21:5432/quantshift
REDIS_URL=redis://:Cloudy_92!@10.92.3.27:6379/0
NODE_ENV=production
```

### Bot (systemd service)
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=Cloudy_92!
APCA_API_KEY_ID=<your_key>
APCA_API_SECRET_KEY=<your_secret>
APCA_API_BASE_URL=https://paper-api.alpaca.markets
DATABASE_URL=postgresql://quantshift_bot:Cloudy_92!@10.92.3.21:5432/quantshift
```

## Development Workflow

1. **Make changes locally** in `/Users/cory/Documents/Cloudy-Work/applications/quantshift`
2. **Commit and push** to GitHub
3. **Deploy to platform**:
   ```bash
   ssh quantshift-platform
   cd /opt/quantshift
   git pull origin main
   cd apps/dashboard
   npm run build
   pm2 restart quantshift-platform
   ```
4. **Deploy bot updates**:
   ```bash
   ssh quantshift-primary
   cd /opt/quantshift
   git pull origin main
   systemctl restart quantshift-equity.service
   ```

## Monitoring

### Real-Time Monitoring
- Platform automatically polls APIs every 5 seconds
- Bot sends heartbeat every 30 seconds
- Bot updates state every 60 seconds

### Health Checks
- Bot is considered alive if heartbeat is less than 2 minutes old
- Redis keys have TTL (Time To Live):
  - State: 1 hour
  - Positions: 24 hours
  - Heartbeat: 60 seconds

## Future Enhancements

1. **Crypto Bot Deployment**
   - Deploy crypto trading bot
   - Add crypto-specific strategies

2. **Advanced Analytics**
   - Performance charts
   - Risk metrics
   - Drawdown analysis

3. **Settings & Configuration**
   - Bot parameter tuning
   - Risk limit configuration
   - Alert preferences

4. **Strategy Management**
   - Real-time strategy performance
   - Strategy allocation
   - Backtest results

5. **Notifications**
   - Email alerts for trades
   - Slack/Discord integration
   - SMS notifications for critical events

## Support

For issues or questions:
- Check logs first (bot and platform)
- Verify all services are running
- Check Redis and database connectivity
- Review this guide for troubleshooting steps
