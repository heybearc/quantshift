"""Fifteen-minute break for the Kraken sprint book.

A finished 15-minute bar must close beyond the high or low of the prior
lookback bars. The stop sits just outside that bar. The target is twice the
stop distance, and the order is skipped when that target is under the minimum
reward. A position still open after the hold limit is closed. Shorts follow
enable_shorts. A name already held is left alone.
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


class SprintBreakSetup(BaseStrategy):
    """Take a 15-minute close through the prior range when the target clears cost."""

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
        lookback = int(self.config.get("lookback", 8))
        if noise is None or len(noise) < lookback + 1:
            return []
        prior = noise.iloc[-(lookback + 1):-1]
        bar = noise.iloc[-1]
        price = float(bar["close"])
        if price <= 0:
            return []
        prior_high = float(prior["high"].astype(float).max())
        prior_low = float(prior["low"].astype(float).min())
        if price > prior_high:
            return self._entry(symbol, SignalType.BUY, price, float(bar["low"]), account, "long")
        if self.shorts_enabled() and price < prior_low:
            return self._entry(symbol, SignalType.SELL, price, float(bar["high"]), account, "short")
        return []

    def calculate_position_size(self, signal: Signal, account: Account, atr: Optional[float] = None) -> float:
        if signal.stop_loss is None or signal.price <= 0:
            return 0
        risk = abs(float(signal.price) - float(signal.stop_loss))
        if risk <= 0:
            return 0
        budget = float(account.equity) * float(self.config.get("risk_per_trade", 0.005))
        return budget / risk

    def _time_stop(self, symbol: str, held: Position, market_data: pd.DataFrame) -> List[Signal]:
        meta = held.metadata or {}
        if meta.get("strategy") != self.name:
            return []
        opened = _opened(meta.get("opened_at"))
        if opened is None:
            return []
        limit = float(self.config.get("max_hold_minutes", 90))
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
            reason="sprint break time stop",
            metadata={"strategy": self.name, "side": "exit"},
        )]

    def _mark(self, market_data: pd.DataFrame) -> Optional[float]:
        noise = attached_frame(market_data, "noise")
        if noise is None:
            return None
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
        account: Account,
        name: str,
    ) -> List[Signal]:
        buffer = float(self.config.get("stop_buffer", 0.001))
        multiple = float(self.config.get("reward_multiple", 2.0))
        if name == "long":
            stop = float(wick) * (1.0 - buffer)
            if stop >= price:
                return []
            risk = price - stop
            target = price + (multiple * risk)
        else:
            stop = float(wick) * (1.0 + buffer)
            if stop <= price:
                return []
            risk = stop - price
            target = price - (multiple * risk)
        if risk <= 0 or target <= 0:
            return []
        reward = (multiple * risk) / price
        if reward < float(self.config.get("min_reward_pct", 0.01)):
            return []
        budget = float(account.equity) * float(self.config.get("risk_per_trade", 0.005))
        quantity = budget / risk
        notional_cap = float(account.equity) * float(self.config.get("max_notional", 0.12))
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
            reason=f"sprint break {name}",
            metadata={"strategy": self.name, "side": name},
        )]
