# QuantShift Architecture Documentation

## Broker-Agnostic Strategy Framework

### Design Philosophy

**Separation of Concerns:**
- **Strategies** = Pure trading logic (no broker dependencies)
- **Executors** = Broker-specific implementation (API calls, order management)
- **Backtesting** = Uses same strategy code as live trading
- **Scalability** = Add new brokers/assets without rewriting strategies

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Trading Bot Application                   │
│                     (run_bot_v2.py)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─── Configuration (YAML)
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Broker-Specific Executor                   │
│                    (alpaca_executor.py)                      │
│                                                              │
│  • Fetch market data from broker                            │
│  • Convert broker data to standard format                   │
│  • Execute orders via broker API                            │
│  • Handle broker-specific quirks                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Broker-Agnostic Strategy                    │
│              (strategies/ma_crossover.py)                    │
│                                                              │
│  • Pure trading logic                                        │
│  • No broker dependencies                                   │
│  • Receives: market data, account, positions                │
│  • Returns: trading signals                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Base Strategy                           │
│                 (strategies/base_strategy.py)                │
│                                                              │
│  • Abstract interface                                        │
│  • Common risk management                                   │
│  • Signal validation                                        │
│  • Position sizing helpers                                  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Bot starts → Load configuration
                ↓
2. Initialize Strategy (broker-agnostic)
                ↓
3. Initialize Executor (broker-specific)
                ↓
4. Main Loop:
   ├─ Executor fetches market data from Alpaca
   ├─ Executor converts to standard DataFrame format
   ├─ Executor gets account & positions
   ├─ Executor passes data to Strategy
   ├─ Strategy generates signals (BUY/SELL/HOLD)
   ├─ Executor validates signals
   ├─ Executor executes via Alpaca API
   └─ Bot syncs trades to database
```

## Core Components

### 1. Base Strategy (`base_strategy.py`)

**Purpose:** Abstract base class defining strategy interface

**Key Classes:**
- `BaseStrategy` - Abstract strategy interface
- `Signal` - Trading signal (BUY/SELL/HOLD)
- `Account` - Broker-agnostic account data
- `Position` - Broker-agnostic position data
- `SignalType` - Enum for signal types

**Key Methods:**
```python
@abstractmethod
def generate_signals(market_data, account, positions) -> List[Signal]:
    """Core strategy logic - must be implemented by subclasses"""
    
@abstractmethod
def calculate_position_size(signal, account, atr) -> int:
    """Risk-based position sizing"""
    
def calculate_stop_loss(signal, atr) -> float:
    """ATR-based stop loss calculation"""
    
def calculate_take_profit(signal, stop_loss) -> float:
    """Risk-reward based take profit"""
    
def validate_signal(signal, account, positions) -> bool:
    """Risk management validation"""
```

### 2. MA Crossover Strategy (`ma_crossover.py`)

**Purpose:** Concrete implementation of Moving Average Crossover

**Features:**
- Golden cross detection (short MA > long MA)
- Death cross detection (short MA < long MA)
- ATR-based position sizing
- Volume confirmation filter
- Weekly trend confirmation filter
- Support/resistance proximity filter

**Configuration:**
```python
config = {
    'short_window': 20,
    'long_window': 50,
    'atr_period': 14,
    'risk_per_trade': 0.02,
    'volume_confirmation': True,
    'trend_confirmation': True,
    'support_resistance_filter': True
}
```

### 3. Alpaca Executor (`alpaca_executor.py`)

**Purpose:** Alpaca-specific strategy execution

**Responsibilities:**
1. Fetch market data from Alpaca API
2. Convert Alpaca data to standard format
3. Execute signals via Alpaca orders
4. Handle stop loss and take profit orders
5. Manage Alpaca-specific quirks

**Key Methods:**
```python
def get_account() -> Account:
    """Fetch and normalize account data"""
    
def get_positions() -> List[Position]:
    """Fetch and normalize positions"""
    
def get_market_data(symbol, days) -> DataFrame:
    """Fetch historical OHLCV data"""
    
def execute_signal(signal) -> Dict:
    """Execute trading signal via Alpaca"""
    
def run_strategy_cycle() -> Dict:
    """Complete strategy execution cycle"""
```

### 4. Trading Bot (`run_bot_v2.py`)

**Purpose:** Main application orchestrating everything

**Responsibilities:**
1. Load configuration from YAML
2. Initialize strategy and executor
3. Manage bot lifecycle (start/stop/signals)
4. Update state to Redis
5. Sync trades to PostgreSQL
6. Run strategy on schedule

## Configuration System

### Configuration File (`config/equity_strategy.yaml`)

**Structure:**
```yaml
strategy:
  name: "MA Crossover"
  parameters:
    short_window: 20
    long_window: 50
  symbols:
    - SPY
    - QQQ

risk_management:
  risk_per_trade: 0.02
  max_positions: 5
  max_portfolio_heat: 0.10

execution:
  order_type: "market"
  costs:
    slippage_bps: 5

filters:
  volume_confirmation: true
  trend_confirmation: true
```

## Adding New Strategies

### Step 1: Create Strategy Class

```python
from quantshift_core.strategies import BaseStrategy, Signal, SignalType

class MyNewStrategy(BaseStrategy):
    def __init__(self, config=None):
        super().__init__(config)
        # Initialize strategy parameters
        
    def generate_signals(self, market_data, account, positions):
        # Implement your strategy logic
        signals = []
        
        # Analyze market_data
        # Generate BUY/SELL signals
        
        return signals
    
    def calculate_position_size(self, signal, account, atr):
        # Implement position sizing logic
        return size
```

### Step 2: Register Strategy

```python
# In strategies/__init__.py
from .my_new_strategy import MyNewStrategy

__all__ = [
    'BaseStrategy',
    'MACrossoverStrategy',
    'MyNewStrategy'  # Add here
]
```

### Step 3: Use in Bot

```python
from quantshift_core.strategies import MyNewStrategy

strategy = MyNewStrategy(config=strategy_config)
executor = AlpacaExecutor(
    strategy=strategy,
    alpaca_client=alpaca_client,
    symbols=['SPY', 'QQQ']
)
```

## Adding New Brokers

### Step 1: Create Broker Executor

```python
class CoinbaseExecutor:
    def __init__(self, strategy, coinbase_client, symbols):
        self.strategy = strategy
        self.client = coinbase_client
        self.symbols = symbols
    
    def get_account(self) -> Account:
        # Fetch from Coinbase, convert to Account
        pass
    
    def get_positions(self) -> List[Position]:
        # Fetch from Coinbase, convert to Position
        pass
    
    def get_market_data(self, symbol) -> DataFrame:
        # Fetch from Coinbase, return standard DataFrame
        pass
    
    def execute_signal(self, signal) -> Dict:
        # Execute via Coinbase API
        pass
```

### Step 2: Use Same Strategy

```python
# Same strategy works with different brokers!
strategy = MACrossoverStrategy(config=config)

# Use with Alpaca
alpaca_executor = AlpacaExecutor(strategy, alpaca_client, ['SPY'])

# Use with Coinbase
coinbase_executor = CoinbaseExecutor(strategy, coinbase_client, ['BTC-USD'])
```

## Backtesting Integration

### Using Strategy with Backtest Engine

```python
from quantshift_core.backtesting import BacktestEngine
from quantshift_core.strategies import MACrossoverStrategy

# Initialize
engine = BacktestEngine(initial_capital=10000)
strategy = MACrossoverStrategy(config={'short_window': 20, 'long_window': 50})

# Load historical data
historical_data = load_historical_data('SPY', start='2022-01-01', end='2024-12-31')

# Run backtest
for timestamp, bar in historical_data.iterrows():
    # Get current market data up to this point
    market_data = historical_data.loc[:timestamp]
    
    # Generate signals using same strategy
    signals = strategy.generate_signals(
        market_data=market_data,
        account=engine.get_account(),
        positions=engine.get_positions()
    )
    
    # Execute in backtest
    for signal in signals:
        engine.execute_trade(signal)

# Get results
metrics = engine.get_metrics()
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
```

## Benefits of This Architecture

### 1. **Reusability**
- Write strategy once, use everywhere (Alpaca, Coinbase, backtesting)
- No code duplication between brokers

### 2. **Testability**
- Strategies are pure functions (easy to unit test)
- Backtesting uses same code as live trading
- Mock executors for integration testing

### 3. **Maintainability**
- Clear separation of concerns
- Changes to broker APIs don't affect strategy logic
- Easy to add new strategies or brokers

### 4. **Scalability**
- Run multiple strategies simultaneously
- Support multiple brokers with same codebase
- Easy to add new asset classes

### 5. **Professional**
- Industry-standard architecture
- Clean, maintainable code
- Easy for other developers to understand

## Migration Path

### From Old Architecture:
```python
# Old: Broker-specific strategy
from alpaca_trading.core.strategy import TradingBot
bot = TradingBot()
result = bot.run_strategy(symbol='SPY')
```

### To New Architecture:
```python
# New: Broker-agnostic strategy
from quantshift_core.strategies import MACrossoverStrategy
from alpaca_executor import AlpacaExecutor

strategy = MACrossoverStrategy(config=config)
executor = AlpacaExecutor(strategy, alpaca_client, symbols=['SPY'])
results = executor.run_strategy_cycle()
```

## Next Steps

1. **Phase 1:** Backtest MA Crossover strategy
2. **Phase 2:** Deploy V2 bot to paper trading
3. **Phase 3:** Add more strategies (RSI, Breakout, etc.)
4. **Phase 4:** Add Coinbase executor for crypto
5. **Phase 5:** Multi-strategy portfolio management
