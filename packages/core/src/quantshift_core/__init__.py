"""QuantShift Core - Shared libraries for trading system."""

__version__ = "0.1.0"

from quantshift_core.config import Settings, get_settings
from quantshift_core.database import DatabaseManager, get_db
from quantshift_core.models import Trade, Position, BotHealth
from quantshift_core.state_manager import StateManager
from quantshift_core.backtesting import BacktestEngine, WalkForwardOptimizer
from quantshift_core.position_sizing import PositionSizer, RiskManager
from quantshift_core.indicators import TechnicalIndicators, MultiTimeframeAnalyzer
from quantshift_core.strategies import (
    BaseStrategy,
    Signal,
    SignalType,
    MACrossoverStrategy
)
from quantshift_core.strategy_manager import StrategyManager

__all__ = [
    "Settings",
    "get_settings",
    "DatabaseManager",
    "get_db",
    "Trade",
    "Position",
    "BotHealth",
    "StateManager",
    "BacktestEngine",
    "WalkForwardOptimizer",
    "PositionSizer",
    "RiskManager",
    "TechnicalIndicators",
    "MultiTimeframeAnalyzer",
    "BaseStrategy",
    "Signal",
    "SignalType",
    "MACrossoverStrategy",
    "StrategyManager",
]
