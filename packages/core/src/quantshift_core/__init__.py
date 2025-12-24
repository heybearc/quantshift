"""QuantShift Core - Shared libraries for trading system."""

__version__ = "0.1.0"

from quantshift_core.config import Settings, get_settings
from quantshift_core.database import DatabaseManager, get_db
from quantshift_core.models import Trade, Position, BotHealth

__all__ = [
    "Settings",
    "get_settings",
    "DatabaseManager",
    "get_db",
    "Trade",
    "Position",
    "BotHealth",
]
