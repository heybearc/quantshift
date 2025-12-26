# Equity Bot - Admin Platform Integration

## Overview

This guide shows how to integrate the equity bot with the QuantShift Admin Platform for real-time monitoring.

## Database Writer

The `database_writer.py` module handles all database writes to PostgreSQL for the admin platform.

### Connection

```python
from database_writer import DatabaseWriter

db_writer = DatabaseWriter(bot_name='equity-bot')
db_writer.connect()
```

### Integration Points

#### 1. Bot Status (Every Minute)

Add to your main loop:

```python
# In run_bot.py main loop
account_info = self.get_account_info()
positions = self.get_positions()

db_writer.update_status(
    account_info=account_info,
    positions=positions,
    trades_count=total_trades
)
```

#### 2. Trade Entry

When entering a trade:

```python
trade_id = db_writer.record_trade_entry(
    symbol='AAPL',
    side='BUY',
    quantity=10,
    entry_price=150.00,
    stop_loss=148.00,
    take_profit=155.00,
    strategy='MA_CROSSOVER',
    signal_type='LONG',
    entry_reason='5/20 MA crossover bullish'
)

# Store trade_id for later exit
```

#### 3. Trade Exit

When exiting a trade:

```python
db_writer.record_trade_exit(
    trade_id=stored_trade_id,
    exit_price=153.00,
    exit_reason='Take profit hit'
)
```

#### 4. Position Updates

Update positions in real-time:

```python
positions = self.get_positions()
db_writer.update_positions(positions)
```

#### 5. Daily Performance

At end of day:

```python
daily_trades = get_today_trades()
account_info = self.get_account_info()

db_writer.record_daily_performance(
    daily_trades=daily_trades,
    account_equity=account_info['equity']
)
```

## Modified run_bot.py Integration

Add to the `QuantShiftEquityBot` class:

```python
from database_writer import DatabaseWriter

class QuantShiftEquityBot:
    def __init__(self):
        # ... existing code ...
        
        # Add database writer
        self.db_writer = DatabaseWriter(bot_name=self.bot_name)
        self.db_writer.connect()
        
    def run(self):
        """Main bot loop with admin platform integration"""
        logger.info(f"Starting {self.bot_name}...")
        
        while self.running:
            try:
                # Update state (existing)
                self.update_state()
                
                # Sync trades (existing)
                self.sync_trades_to_database()
                
                # NEW: Update admin platform
                account_info = self.get_account_info()
                positions = self.get_positions()
                
                if account_info:
                    # Update bot status for admin dashboard
                    self.db_writer.update_status(
                        account_info=account_info,
                        positions=positions,
                        trades_count=self.get_total_trades_count()
                    )
                    
                    # Update positions
                    self.db_writer.update_positions(positions)
                
                # Sleep for 60 seconds
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)
                
        # Cleanup
        self.db_writer.disconnect()
```

## Testing

### 1. Test Database Connection

```python
from database_writer import DatabaseWriter

db = DatabaseWriter(bot_name='equity-bot')
db.connect()
print("Connection successful!")
db.disconnect()
```

### 2. Test Status Update

```python
db = DatabaseWriter(bot_name='equity-bot')
db.connect()

db.update_status(
    account_info={'equity': 10000, 'balance': 5000, 'buying_power': 8000, 'portfolio_value': 10000},
    positions=[],
    trades_count=0
)

db.disconnect()
```

### 3. Verify in Admin Platform

1. Start admin platform: `cd apps/admin-web && npm run dev`
2. Open http://localhost:3001
3. Login and check dashboard
4. Verify bot status appears

## Deployment

### Local Testing

```bash
# Terminal 1: Admin platform
cd apps/admin-web
npm run dev

# Terminal 2: Equity bot
cd apps/bots/equity
python run_bot.py
```

### Production Deployment

The bot will deploy to LXC 100 & 101 (hot-standby) and connect to PostgreSQL on LXC 131 (10.92.3.21).

Database URL is configured in `database_writer.py`:
```python
db_url = "postgresql://quantshift:Cloudy_92!@10.92.3.21:5432/quantshift"
```

## Troubleshooting

### Connection Issues

```python
# Check PostgreSQL is accessible
psql -h 10.92.3.21 -U quantshift -d quantshift

# Test from Python
import psycopg2
conn = psycopg2.connect("postgresql://quantshift:Cloudy_92!@10.92.3.21:5432/quantshift")
print("Connected!")
```

### Missing Data

- Check bot logs for database errors
- Verify tables exist in PostgreSQL
- Check admin platform API endpoints return data

## Next Steps

1. Add database writer to run_bot.py
2. Test locally with admin platform
3. Deploy to LXC 100/101
4. Monitor in production
