"""Shared data models for trading system."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class TradeDirection(str, Enum):
    """Trade direction."""

    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, Enum):
    """Trade status."""

    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionStatus(str, Enum):
    """Position status."""

    OPEN = "open"
    CLOSED = "closed"


class Trade(BaseModel):
    """Trade model."""

    id: int | None = None
    bot_name: str
    symbol: str
    direction: TradeDirection
    quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    status: TradeStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    profit_loss: Decimal | None = None
    profit_loss_pct: Decimal | None = None
    notes: str | None = None


class Position(BaseModel):
    """Position model."""

    id: int | None = None
    bot_name: str
    symbol: str
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    status: PositionStatus
    entry_time: datetime
    exit_time: datetime | None = None
    unrealized_pl: Decimal | None = None
    unrealized_pl_pct: Decimal | None = None


class BotHealth(BaseModel):
    """Bot health status."""

    id: int | None = None
    bot_name: str
    status: str  # running, stopped, error
    last_heartbeat: datetime
    error_message: str | None = None
    trades_today: int = 0
    positions_open: int = 0
    daily_pnl: Decimal = Decimal("0")
