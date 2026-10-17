# QuantShift Equity Bot

Alpaca equity trading bot with advanced technical analysis and risk management.

## 🎯 Features

- Moving Average Crossover strategy
- Advanced stock screening
- Risk management with stop-loss/take-profit
- Real-time position monitoring
- Streamlit dashboard
- Paper and live trading support

## 📦 Installation

```bash
# From monorepo root
pip install -e apps/bots/equity
```

## 🚀 Usage

```bash
# Run the bot
quantshift-equity

# Or with Python
python -m alpaca_trading.scripts.run_paper_trader
```

## 🔧 Configuration

Create `.env` file in monorepo root:

```env
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
DATABASE_URL=postgresql://quantshift_bot:password@10.92.3.23:5432/quantshift
```

## 📁 Structure

```
equity/
├── alpaca_trading/
│   ├── core/           # Core trading logic
│   ├── strategies/     # Trading strategies
│   ├── screeners/      # Stock screening
│   ├── scripts/        # Entry points
│   └── gui/            # Streamlit dashboards
├── pyproject.toml
└── README.md
```

## 🔗 Dependencies

- Alpaca Trade API
- Pandas, NumPy
- Technical Analysis library (ta)
- Streamlit for dashboards
- PostgreSQL for state management

## 📝 License

MIT
