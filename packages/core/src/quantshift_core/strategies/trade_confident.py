"""One setup for crypto and Kraken, taken from the owner's Trade Confident chart tools.

Daily money flow sets the zone. A finished lower-timeframe bar must reverse at a
pivot, the daily trend lights must agree, and volume must not contradict price.
The stop sits beyond the pivot. The next pivot must be at least twice as far.
"""

from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from .base_strategy import Account, BaseStrategy, Position, Signal, SignalType


def _columns(frame: pd.DataFrame) -> Optional[pd.DataFrame]:
    if frame is None or len(frame) == 0:
        return None
    renamed = frame.rename(columns={col: str(col).lower() for col in frame.columns})
    needed = {"open", "high", "low", "close", "volume"}
    if not needed.issubset(renamed.columns):
        return None
    return renamed


def _is_daily(frame: pd.DataFrame) -> bool:
    if len(frame.index) < 3:
        return False
    gaps = pd.Series(frame.index).diff().dt.total_seconds().dropna()
    if gaps.empty:
        return False
    return float(gaps.median()) >= 20 * 3600


def trades_in_favor(frame: pd.DataFrame) -> Optional[float]:
    """0-100 money-flow reading. Under 20 is the long zone. Over 80 is the short zone."""
    data = _columns(frame)
    if data is None or len(data) < 21:
        return None
    high = data["high"].astype(float)
    low = data["low"].astype(float)
    close = data["close"].astype(float)
    volume = data["volume"].astype(float).clip(lower=0)
    span = (high - low).replace(0, np.nan)
    location = ((2 * close - low - high) / span) * volume
    location = location.fillna(0.0)
    ohlc4 = (data["open"].astype(float) + high + low + close) / 4.0
    change_ohlc = ohlc4.diff()
    up_ohlc = np.where(change_ohlc > 0, ohlc4, 0.0)
    down_ohlc = np.where(change_ohlc < 0, ohlc4, 0.0)
    top = pd.Series(up_ohlc, index=data.index).mul(volume).rolling(8).sum()
    lower = pd.Series(down_ohlc, index=data.index).mul(volume).rolling(8).sum()
    change_close = close.diff()
    up_close = np.where(change_close > 0, close, 0.0)
    down_close = np.where(change_close < 0, close, 0.0)
    top2 = pd.Series(up_close, index=data.index).mul(volume).rolling(20).sum()
    lower2 = pd.Series(down_close, index=data.index).mul(volume).rolling(20).sum()

    def _ratio(upper: pd.Series, lower_side: pd.Series) -> pd.Series:
        ratio = pd.Series(np.nan, index=upper.index)
        ratio = ratio.mask(lower_side == 0, 100.0)
        ratio = ratio.mask(upper == 0, 0.0)
        both = (upper > 0) & (lower_side > 0)
        ratio = ratio.mask(both, 100.0 - (100.0 / (1.0 + upper / lower_side)))
        return ratio

    trend = _ratio(top, lower)
    trend2 = _ratio(top2, lower2)
    strength = location / volume.replace(0, np.nan)
    strength = strength.fillna(0.0)
    line2 = trend2.replace(0, np.nan)
    stretched = (strength / line2).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    reading = trend + stretched + strength
    value = reading.iloc[-1]
    if pd.isna(value):
        return None
    return float(value)


def average_true_range(frame: pd.DataFrame, period: int = 21) -> Optional[float]:
    data = _columns(frame)
    if data is None or len(data) < period + 1:
        return None
    high = data["high"].astype(float)
    low = data["low"].astype(float)
    close = data["close"].astype(float)
    previous = close.shift(1)
    true_range = pd.concat([(high - low), (high - previous).abs(), (low - previous).abs()], axis=1).max(axis=1)
    value = true_range.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    if pd.isna(value) or float(value) <= 0:
        return None
    return float(value)


def last_pivots(frame: pd.DataFrame, length: int = 12) -> Tuple[Optional[float], Optional[float]]:
    """Last confirmed swing low and swing high. A pivot needs `length` bars on each side."""
    data = _columns(frame)
    if data is None or len(data) < (length * 2 + 1):
        return None, None
    high = data["high"].astype(float).to_numpy()
    low = data["low"].astype(float).to_numpy()
    support = None
    resistance = None
    for index in range(length, len(data) - length):
        high_window = high[index - length:index + length + 1]
        low_window = low[index - length:index + length + 1]
        if high[index] == high_window.max():
            resistance = float(high[index])
        if low[index] == low_window.min():
            support = float(low[index])
    return support, resistance


def reversal_bar(frame: pd.DataFrame, qual: int = 2, length: int = 10) -> int:
    """1 when the last closed bar reverses up at a low. -1 when it reverses down at a high."""
    data = _columns(frame)
    if data is None or len(data) < max(length, 5):
        return 0
    open_ = data["open"].astype(float).to_numpy()
    high = data["high"].astype(float).to_numpy()
    low = data["low"].astype(float).to_numpy()
    close = data["close"].astype(float).to_numpy()
    down_count = 0.0
    up_count = 0.0
    signal = 0
    for index in range(len(data)):
        signal = 0
        if index >= 4 and close[index] > close[index - 4]:
            up_count += 1
        if index >= 4 and close[index] < close[index - 4]:
            down_count += 1
        start = max(0, index - length + 1)
        if up_count > qual and close[index] < open_[index] and high[index] >= high[start:index + 1].max():
            up_count = 0
            signal = -1
        if down_count > qual and close[index] > open_[index] and low[index] <= low[start:index + 1].min():
            down_count = 0
            signal = 1
    return signal


def _rsi(close: pd.Series, period: int) -> pd.Series:
    change = close.diff()
    gains = change.clip(lower=0)
    losses = -change.clip(upper=0)
    average_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
    average_loss = losses.ewm(alpha=1 / period, adjust=False).mean()
    relative = average_gain / average_loss.replace(0, np.nan)
    return 100 - (100 / (1 + relative))


def trend_agrees(frame: pd.DataFrame, side: str) -> bool:
    """Every daily trend light points the same way: RSI, stochastic, MACD, and three averages."""
    data = _columns(frame)
    if data is None or len(data) < 200:
        return False
    close = data["close"].astype(float)
    high = data["high"].astype(float)
    low = data["low"].astype(float)
    rsi = _rsi(close, 14).iloc[-1]
    lowest = low.rolling(14).min()
    highest = high.rolling(14).max()
    raw_k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
    k_value = raw_k.rolling(3).mean().iloc[-1]
    d_value = raw_k.rolling(3).mean().rolling(3).mean().iloc[-1]
    fast = close.ewm(span=12, adjust=False).mean()
    slow = close.ewm(span=25, adjust=False).mean()
    macd = fast - slow
    signal = macd.ewm(span=9, adjust=False).mean()
    price = float(close.iloc[-1])
    lights = [
        float(rsi) > 50,
        float(k_value) > float(d_value),
        float(macd.iloc[-1]) > float(signal.iloc[-1]),
        price > float(close.rolling(50).mean().iloc[-1]),
        price > float(close.rolling(100).mean().iloc[-1]),
        price > float(close.rolling(200).mean().iloc[-1]),
    ]
    if any(pd.isna(item) if not isinstance(item, (bool, np.bool_)) else False for item in [rsi, k_value, d_value]):
        return False
    if side == "long":
        return all(lights)
    return not any(lights)


def whale_contradicts(frame: pd.DataFrame, side: str) -> bool:
    """True when price and volume money are on opposite sides of neutral."""
    data = _columns(frame)
    if data is None or len(data) < 20:
        return False
    close = data["close"].astype(float)
    high = data["high"].astype(float)
    low = data["low"].astype(float)
    volume = data["volume"].astype(float).clip(lower=0)
    span = (high - low).replace(0, np.nan)
    location = (((2 * close - low - high) / span) * volume).fillna(0.0)
    whale = (location.rolling(10).sum() / volume.rolling(10).sum().replace(0, np.nan)).iloc[-1]
    change = close.diff()
    up = np.where(change > 0, close, 0.0)
    down = np.where(change < 0, close, 0.0)
    upper = pd.Series(up, index=data.index).mul(volume).rolling(14).sum().iloc[-1]
    lower = pd.Series(down, index=data.index).mul(volume).rolling(14).sum().iloc[-1]
    if lower == 0:
        money = 100.0
    elif upper == 0:
        money = 0.0
    else:
        money = 100.0 - (100.0 / (1.0 + float(upper) / float(lower)))
    composite = float(money) + (0.0 if pd.isna(whale) else float(whale))
    gains = change.clip(lower=0).ewm(alpha=1 / 12, adjust=False).mean().iloc[-1]
    losses = (-change.clip(upper=0)).ewm(alpha=1 / 12, adjust=False).mean().iloc[-1]
    if losses == 0:
        price = 100.0
    elif gains == 0:
        price = 0.0
    else:
        price = 100.0 - (100.0 / (1.0 + float(gains) / float(losses)))
    if side == "long":
        return price > 50 and composite < 50
    return price < 50 and composite > 50


class TradeConfidentSetup(BaseStrategy):
    """Long at support in the daily pump zone. Short at resistance only when shorts are enabled."""

    def shorts_enabled(self) -> bool:
        return bool(self.config.get("enable_shorts", False))

    def held_position(self, positions: List[Position], symbol: str) -> Optional[Position]:
        for position in positions or []:
            if position.symbol == symbol and abs(float(position.quantity or 0)) > 0:
                return position
        return None

    def generate_signals(self, market_data: pd.DataFrame, account: Account, positions: List[Position]) -> List[Signal]:
        symbol = getattr(market_data, "symbol", None)
        if not symbol:
            return []
        held = self.held_position(positions, symbol)
        if held is not None:
            return []
        daily, entry = self._frames(market_data)
        if daily is None or entry is None:
            return []
        zone = trades_in_favor(daily)
        if zone is None:
            return []
        bar = reversal_bar(entry)
        support, resistance = last_pivots(entry)
        room = average_true_range(entry)
        if room is None:
            return []
        price = float(_columns(entry)["close"].iloc[-1])
        low = float(_columns(entry)["low"].iloc[-1])
        high = float(_columns(entry)["high"].iloc[-1])
        if zone < 20 and bar == 1 and support is not None and self._touched(low, high, support, room):
            if trend_agrees(daily, "long") and not whale_contradicts(daily, "long"):
                return self._order(symbol, SignalType.BUY, price, support, resistance, room, account, "long")
        if (
            self.shorts_enabled()
            and zone > 80
            and bar == -1
            and resistance is not None
            and self._touched(low, high, resistance, room)
            and trend_agrees(daily, "short")
            and not whale_contradicts(daily, "short")
        ):
            return self._order(symbol, SignalType.SELL, price, resistance, support, room, account, "short")
        return []

    def calculate_position_size(self, signal: Signal, account: Account, atr: Optional[float] = None) -> int:
        if signal.stop_loss is None or signal.price <= 0:
            return 0
        risk = abs(float(signal.price) - float(signal.stop_loss))
        if risk <= 0:
            return 0
        budget = float(account.equity) * float(self.config.get("risk_per_trade", 0.01))
        return budget / risk

    def _frames(self, market_data: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        daily = market_data.attrs.get("daily")
        entry = market_data.attrs.get("entry")
        if daily is None and _is_daily(market_data):
            daily = market_data
        if entry is None and not _is_daily(market_data):
            entry = market_data
        return daily, entry

    def _touched(self, low: float, high: float, level: float, room: float) -> bool:
        return low <= level + room and high >= level - room

    def _order(
        self,
        symbol: str,
        side: SignalType,
        price: float,
        pivot: float,
        opposite: Optional[float],
        room: float,
        account: Account,
        name: str,
    ) -> List[Signal]:
        if name == "long":
            stop = pivot - (0.25 * room)
            if stop >= price or opposite is None or opposite <= price:
                return []
            target = opposite
            risk = price - stop
            if target - price < risk * 2:
                return []
        else:
            stop = pivot + (0.25 * room)
            if stop <= price or opposite is None or opposite >= price:
                return []
            target = opposite
            risk = stop - price
            if price - target < risk * 2:
                return []
        budget = float(account.equity) * float(self.config.get("risk_per_trade", 0.01))
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
            reason=f"trade confident {name}",
            metadata={"strategy": self.name, "side": name, "pivot": pivot},
        )]
