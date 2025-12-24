# QuantShift Crypto Bot

Cryptocurrency trading bot using Coinbase Advanced Trade API.

## Features

- **24/7 Trading:** Crypto markets never close
- **Multiple Strategies:** MA crossover, RSI, MACD, Bollinger Bands
- **ATR-Based Position Sizing:** Volatility-adjusted risk management
- **Hot-Standby Support:** Automatic failover with state management
- **Real-Time Monitoring:** Heartbeat and health checks

## Supported Cryptocurrencies

- BTC-USD (Bitcoin)
- ETH-USD (Ethereum)
- SOL-USD (Solana)
- AVAX-USD (Avalanche)
- MATIC-USD (Polygon)
- And many more...

## Installation

```bash
# From monorepo root
pip install -e apps/bots/crypto
```

## Configuration

Add to `.env` file:

```env
# Coinbase Advanced Trade API
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret

# Database and Redis (inherited from core)
DATABASE_URL=postgresql://quantshift_bot:password@10.92.3.21:5432/quantshift
REDIS_URL=redis://:Cloudy_92!@localhost:6379/0
```

## Usage

```bash
# Run the bot
quantshift-crypto

# Or with Python
python -m quantshift_crypto.main
```

## Strategies

### 1. Moving Average Crossover
- **Buy:** 20 SMA crosses above 50 SMA (Golden Cross)
- **Sell:** 20 SMA crosses below 50 SMA (Death Cross)
- **Filter:** RSI not overbought/oversold

### 2. RSI Strategy
- **Buy:** RSI crosses below 30 (Oversold)
- **Sell:** RSI crosses above 70 (Overbought)

### 3. MACD Strategy
- **Buy:** MACD crosses above signal line
- **Sell:** MACD crosses below signal line

## Risk Management

- **Position Sizing:** ATR-based (2% account risk per trade)
- **Stop Loss:** 2x ATR from entry
- **Maximum Positions:** Configurable (default: 10)
- **Portfolio Heat:** Total risk exposure monitoring

## Differences from Equity Bot

### Higher Volatility
- Wider stop losses (2-3x ATR vs 1.5x for equities)
- Smaller position sizes relative to account
- More frequent rebalancing

### 24/7 Market
- No market hours restrictions
- Weekend trading
- Different volume patterns

### Lower Fees
- Maker orders: 0.40% - 0.60%
- Taker orders: 0.60% - 0.80%
- Lower than equity commissions

## Systemd Service

Create `/etc/systemd/system/quantshift-crypto.service`:

```ini
[Unit]
Description=QuantShift Crypto Trading Bot
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/quantshift/apps/bots/crypto
Environment="PYTHONPATH=/opt/quantshift/apps/bots/crypto"
Environment="COINBASE_API_KEY=your_key"
Environment="COINBASE_API_SECRET=your_secret"
Environment="DATABASE_URL=postgresql://quantshift_bot:password@10.92.3.21:5432/quantshift"
ExecStart=/opt/quantshift/venv/bin/python -m quantshift_crypto.main
Restart=always
RestartSec=10
StandardOutput=append:/opt/quantshift/logs/crypto-bot.log
StandardError=append:/opt/quantshift/logs/crypto-bot-error.log

[Install]
WantedBy=multi-user.target
```

## Monitoring

```bash
# Check service status
systemctl status quantshift-crypto

# View logs
tail -f /opt/quantshift/logs/crypto-bot.log

# Check Redis state
redis-cli -a Cloudy_92! GET "bot:crypto-bot:heartbeat"
```

## Testing

```bash
# Run tests
pytest apps/bots/crypto/tests -v

# With coverage
pytest apps/bots/crypto/tests --cov=quantshift_crypto
```

## Future Enhancements

- [ ] WebSocket streaming data
- [ ] On-chain metrics integration
- [ ] Funding rate arbitrage
- [ ] Cross-exchange arbitrage
- [ ] DeFi integration
- [ ] NFT trading strategies

## License

MIT
