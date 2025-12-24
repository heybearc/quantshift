# QuantShift Core

Shared core libraries and utilities for the QuantShift trading system.

## 📦 Installation

```bash
# From monorepo root
pip install -e packages/core
```

## 🎯 Features

- **Configuration Management**: Environment-based config with Pydantic
- **Database Layer**: SQLAlchemy connection management for PostgreSQL
- **Data Models**: Shared Pydantic models (Trade, Position, BotHealth)
- **Type Safety**: Full type hints with mypy strict mode

## 🔧 Usage

```python
from quantshift_core import get_settings, get_db, Trade, Position

# Get settings
settings = get_settings()
print(settings.database_url)

# Use database
db = get_db()
with db.session() as session:
    # Your database operations
    pass

# Use models
trade = Trade(
    bot_name="equity-bot",
    symbol="AAPL",
    direction="buy",
    quantity=10,
    entry_price=150.00,
    status="filled"
)
```

## 🔗 Used By

- `apps/bots/equity` - Alpaca equity trading
- `apps/bots/crypto` - Coinbase crypto trading
- `apps/dashboard` - Next.js dashboard

## 📝 License

MIT
