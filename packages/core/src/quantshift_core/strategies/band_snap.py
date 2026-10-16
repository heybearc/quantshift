"""Fifteen-minute mean reversion for the crypto books.

A finished 15-minute bar must tag the outer Bollinger band and close back
inside. The target is the middle of the band. The stop sits just beyond the
tag. A position still open after three hours is closed. Shorts follow
enable_shorts. Names already held by any setup are left alone.
"""

from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from ..candles import attached_frame
from .base_strategy import Account, BaseStrategy, Position, Signal, SignalType


def _columns(frame: pd.DataFrame) -> Optional[pd.DataFrame]:
    if frame is None or len(frame) == 0:
        return None
    renamed = frame.rename(columns={col: str(col).lower() for col in frame.columns})
    needed = {"open", "high", "low", "close"}
    if not needed.issubset(renamed.columns):
        return None
    return renamed


def _opened(value) -> Optional[datetime]:
    if isinstance(value, datetime):
        parsed = value
    elif not value:
        return None
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", ""))
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.replace(tzinfo=None)
    return parsed


class BandSnapSetup(BaseStrategy):
    """Fade a closed 15-minute stretch back to the middle of the band."""

    def generate_signals(
        self,
        market_data: pd.DataFrame,
        account: Account,
        positions: List[Position],
    ) -> List[Signal]:
        symbol = getattr(market_data, "symbol", None)
        if not symbol:
            return []
        held = self.held_position(positions, symbol)
        if held is not None:
            return self._time_stop(symbol, held, market_data)
        noise = _columns(attached_frame(market_data, "noise"))
        if noise is None:
            return []
        period = 20
        if len(noise) < period:
            return []
        close = noise["close"].astype(float)
        mid = close.rolling(period).mean().iloc[-1]
        width = close.rolling(period).std().iloc[-1]
        if pd.isna(mid) or pd.isna(width) or float(width) <= 0:
            return []
        middle = float(mid)
        lower = middle - (2.0 * float(width))
        upper = middle + (2.0 * float(width))
        price = float(close.iloc[-1])
        low = float(noise["low"].astype(float).iloc[-1])
        high = float(noise["high"].astype(float).iloc[-1])
        if price <= 0:
            return []
        if low <= lower and lower < price < middle:
            return self._entry(symbol, SignalType.BUY, price, low, lower, middle, account, "long")
        if (
            self.shorts_enabled()
            and high >= upper
            and middle < price < upper
        ):
            return self._entry(symbol, SignalType.SELL, price, high, upper, middle, account, "short")
        return []

    def calculate_position_size(self, signal: Signal, account: Account, atr: Optional[float] = None) -> float:
        if signal.stop_loss is None or signal.price <= 0:
            return 0
        risk = abs(float(signal.price) - float(signal.stop_loss))
        if risk <= 0:
            return 0
        budget = float(account.equity) * float(self.config.get("risk_per_trade", 0.0025))
        return budget / risk

    def _time_stop(self, symbol: str, held: Position, market_data: pd.DataFrame) -> List[Signal]:
        meta = held.metadata or {}
        if meta.get("strategy") != self.name:
            return []
        opened = _opened(meta.get("opened_at"))
        if opened is None:
            return []
        limit = float(self.config.get("max_hold_minutes", 180))
        if datetime.utcnow() - opened < timedelta(minutes=limit):
            return []
        price = self._mark(market_data)
        if price is None:
            price = float(held.current_price or 0)
        if price <= 0:
            return []
        side = SignalType.SELL if str(held.side).lower() != "short" else SignalType.BUY
        return [Signal(
            signal_type=side,
            symbol=symbol,
            timestamp=datetime.utcnow(),
            price=price,
            position_size=abs(float(held.quantity or 0)),
            reason="band snap time stop",
            metadata={"strategy": self.name, "side": "exit"},
        )]

    def _mark(self, market_data: pd.DataFrame) -> Optional[float]:
        noise = attached_frame(market_data, "noise")
        if noise is None:
            return None
        mark = getattr(noise, "attrs", {}).get("mark_price")
        if mark and float(mark) > 0:
            return float(mark)
        data = _columns(noise)
        if data is None:
            return None
        price = float(data["close"].iloc[-1])
        return price if price > 0 else None

    def _entry(
        self,
        symbol: str,
        side: SignalType,
        price: float,
        wick: float,
        band: float,
        middle: float,
        account: Account,
        name: str,
    ) -> List[Signal]:
        reward = abs(middle - price) / price
        if reward < float(self.config.get("min_reward_pct", 0.006)):
            return []
        buffer = float(self.config.get("stop_buffer", 0.001))
        if name == "long":
            stop = min(wick, band) * (1.0 - buffer)
            if stop >= price or middle <= price:
                return []
            target = middle
        else:
            stop = max(wick, band) * (1.0 + buffer)
            if stop <= price or middle >= price:
                return []
            target = middle
        risk = abs(price - stop)
        if risk <= 0:
            return []
        budget = float(account.equity) * float(self.config.get("risk_per_trade", 0.0025))
        quantity = budget / risk
        notional_cap = float(account.equity) * float(self.config.get("max_notional", 0.20))
        if quantity * price > notional_cap:
            quantity = notional_cap / price
        if quantity <= 0:
            return []
        return [Signal(
            signal_type=side,
            symbol=symbol,
            timestamp=datetime.utcnow(),
            price=price,
            stop_loss=stop,
            take_profit=target,
            position_size=quantity,
            reason=f"band snap {name}",
            metadata={"strategy": self.name, "side": name},
        )]
