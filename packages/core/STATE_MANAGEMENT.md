# State Management for Hot-Standby Failover

## Overview

The `StateManager` class provides state persistence and recovery for hot-standby failover between primary and standby bot containers.

## Features

### 1. Redis Replication
- **Primary (LXC 100):** Redis master
- **Standby (LXC 101):** Redis replica
- Automatic state synchronization
- 256MB memory limit with LRU eviction

### 2. Graceful Shutdown
- SIGTERM/SIGINT signal handlers
- Save state before shutdown
- Run custom shutdown handlers
- Close positions safely

### 3. Position Recovery
- Save positions to Redis
- Load positions on startup
- Sync with broker API
- Handle partial fills

### 4. Heartbeat Monitoring
- 60-second heartbeat interval
- Primary lock mechanism
- Automatic failover detection

## Usage

```python
from quantshift_core import StateManager

# Initialize state manager
state = StateManager(bot_name="equity-bot")

# Register shutdown handler
def close_positions():
    # Your cleanup code
    pass

state.register_shutdown_handler(close_positions)

# Save bot state
state.save_state({
    "strategy": "moving_average",
    "last_trade": "2025-12-24T22:00:00",
    "daily_pnl": 150.50
})

# Load state on startup
previous_state = state.load_state()
if previous_state:
    print(f"Recovered state from: {previous_state['last_update']}")

# Save position
state.save_position("AAPL", {
    "quantity": 10,
    "entry_price": 150.00,
    "stop_loss": 145.00,
    "take_profit": 160.00
})

# Load all positions
positions = state.load_positions()
for symbol, data in positions.items():
    print(f"{symbol}: {data['quantity']} shares @ ${data['entry_price']}")

# Send heartbeat (call every 30 seconds)
state.heartbeat()

# Check if primary
if state.is_primary():
    print("This instance is primary")
else:
    print("This instance is standby")
```

## Redis Configuration

### Primary (10.92.3.27)
```conf
bind 0.0.0.0
requirepass Cloudy_92!
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### Standby (10.92.3.28)
```conf
bind 0.0.0.0
requirepass Cloudy_92!
replicaof 10.92.3.27 6379
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## State Keys

- `bot:{bot_name}:state` - General bot state (1 hour TTL)
- `bot:{bot_name}:position:{symbol}` - Position data (24 hour TTL)
- `bot:{bot_name}:heartbeat` - Heartbeat timestamp (60 second TTL)
- `bot:{bot_name}:primary_lock` - Primary instance lock (30 second TTL)

## Failover Process

1. **Primary Failure:**
   - Primary stops sending heartbeat
   - Standby detects missing heartbeat
   - Standby acquires primary lock
   - Standby loads state from Redis
   - Standby resumes trading

2. **Primary Recovery:**
   - Primary starts up
   - Attempts to acquire primary lock
   - Fails (standby holds lock)
   - Operates as standby
   - Waits for standby to release lock

## Testing

```bash
# Test graceful shutdown
ssh quantshift-primary 'systemctl stop quantshift-equity'

# Check state persisted
ssh quantshift-primary 'redis-cli -a Cloudy_92! GET "bot:equity-bot:state"'

# Restart and verify recovery
ssh quantshift-primary 'systemctl start quantshift-equity'
ssh quantshift-primary 'tail -f /opt/quantshift/logs/equity-bot.log'
```

## Dependencies

- `redis>=5.0.1` - Redis client
- `structlog>=23.2.0` - Structured logging
- `sqlalchemy>=2.0.23` - Database ORM

## Notes

- State is saved to Redis for fast recovery
- PostgreSQL is used for permanent trade history
- Redis replication ensures state is available on standby
- Graceful shutdown prevents data loss
- Primary lock prevents split-brain scenarios
