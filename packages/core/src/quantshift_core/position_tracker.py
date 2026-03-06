"""
Position Tracker for Trailing Stop-Loss Management

Tracks position state including high water marks and trailing stop prices.
Persists to database for recovery after bot restarts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()


@dataclass
class PositionTracker:
    """
    Tracks a single position with trailing stop-loss state.
    
    Attributes:
        symbol: Trading symbol (e.g., 'AAPL', 'BTC-USD')
        bot_name: Name of the bot managing this position
        entry_price: Original entry price
        current_price: Latest market price
        quantity: Position size (shares/units)
        original_stop_loss: Initial stop-loss price (never changes)
        current_stop_loss: Current stop-loss price (adjusts with trailing)
        high_water_mark: Highest price reached since entry
        trailing_stop_active: Whether trailing stop has activated
        stop_order_id: Alpaca/broker stop order ID
        take_profit_order_id: Alpaca/broker take profit order ID
        strategy: Strategy that opened this position
        entered_at: Timestamp when position was opened
        last_stop_update: Timestamp of last stop adjustment
    """
    symbol: str
    bot_name: str
    entry_price: float
    current_price: float
    quantity: float
    original_stop_loss: float
    current_stop_loss: float
    high_water_mark: float
    trailing_stop_active: bool = False
    stop_order_id: Optional[str] = None
    take_profit_order_id: Optional[str] = None
    strategy: str = "UNKNOWN"
    entered_at: datetime = field(default_factory=datetime.utcnow)
    last_stop_update: Optional[datetime] = None
    
    def update_price(self, new_price: float) -> bool:
        """
        Update current price and high water mark.
        
        Args:
            new_price: Latest market price
            
        Returns:
            True if high water mark was updated, False otherwise
        """
        self.current_price = new_price
        
        if new_price > self.high_water_mark:
            old_hwm = self.high_water_mark
            self.high_water_mark = new_price
            logger.info(
                "high_water_mark_updated",
                symbol=self.symbol,
                old_hwm=f"${old_hwm:.2f}",
                new_hwm=f"${new_price:.2f}",
                gain_from_entry=f"{((new_price - self.entry_price) / self.entry_price * 100):.2f}%"
            )
            return True
        
        return False
    
    def should_activate_trailing_stop(self, activation_threshold_pct: float) -> bool:
        """
        Check if trailing stop should activate based on gain threshold.
        
        Args:
            activation_threshold_pct: Minimum gain % to activate (e.g., 0.01 = 1%)
            
        Returns:
            True if trailing stop should activate
        """
        if self.trailing_stop_active:
            return False
        
        gain_pct = (self.high_water_mark - self.entry_price) / self.entry_price
        return gain_pct >= activation_threshold_pct
    
    def calculate_trailing_stop_price(
        self,
        trail_distance_atr_mult: float,
        atr: float,
        min_trail_distance_pct: float = 0.005
    ) -> float:
        """
        Calculate new trailing stop price.
        
        Args:
            trail_distance_atr_mult: ATR multiplier for trail distance
            atr: Current Average True Range
            min_trail_distance_pct: Minimum trail distance as % (default 0.5%)
            
        Returns:
            New trailing stop price
        """
        # Calculate ATR-based trail distance
        atr_distance = trail_distance_atr_mult * atr
        
        # Calculate minimum percentage-based distance
        pct_distance = self.high_water_mark * min_trail_distance_pct
        
        # Use the larger of the two
        trail_distance = max(atr_distance, pct_distance)
        
        # Trailing stop is trail_distance below high water mark
        new_stop = self.high_water_mark - trail_distance
        
        return new_stop
    
    def should_update_stop(
        self,
        new_stop_price: float,
        only_improve: bool = True
    ) -> bool:
        """
        Check if stop-loss should be updated to new price.
        
        Args:
            new_stop_price: Proposed new stop price
            only_improve: Only update if new stop is better (higher for longs)
            
        Returns:
            True if stop should be updated
        """
        if only_improve:
            # For long positions, new stop must be higher than current
            return new_stop_price > self.current_stop_loss
        else:
            return new_stop_price != self.current_stop_loss
    
    def update_stop_loss(self, new_stop_price: float) -> None:
        """
        Update current stop-loss price and timestamp.
        
        Args:
            new_stop_price: New stop-loss price
        """
        old_stop = self.current_stop_loss
        self.current_stop_loss = new_stop_price
        self.last_stop_update = datetime.utcnow()
        
        locked_profit = (new_stop_price - self.entry_price) * self.quantity
        
        logger.info(
            "stop_loss_updated",
            symbol=self.symbol,
            old_stop=f"${old_stop:.2f}",
            new_stop=f"${new_stop_price:.2f}",
            high_water_mark=f"${self.high_water_mark:.2f}",
            locked_profit=f"${locked_profit:.2f}",
            locked_profit_pct=f"{((new_stop_price - self.entry_price) / self.entry_price * 100):.2f}%"
        )
    
    def activate_trailing_stop(self) -> None:
        """Mark trailing stop as activated."""
        self.trailing_stop_active = True
        logger.info(
            "trailing_stop_activated",
            symbol=self.symbol,
            entry_price=f"${self.entry_price:.2f}",
            high_water_mark=f"${self.high_water_mark:.2f}",
            gain=f"{((self.high_water_mark - self.entry_price) / self.entry_price * 100):.2f}%"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'symbol': self.symbol,
            'bot_name': self.bot_name,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'quantity': self.quantity,
            'original_stop_loss': self.original_stop_loss,
            'current_stop_loss': self.current_stop_loss,
            'high_water_mark': self.high_water_mark,
            'trailing_stop_active': self.trailing_stop_active,
            'stop_order_id': self.stop_order_id,
            'take_profit_order_id': self.take_profit_order_id,
            'strategy': self.strategy,
            'entered_at': self.entered_at,
            'last_stop_update': self.last_stop_update
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PositionTracker':
        """Create PositionTracker from dictionary."""
        return cls(**data)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        gain_pct = ((self.current_price - self.entry_price) / self.entry_price * 100)
        return (
            f"PositionTracker({self.symbol}: "
            f"Entry=${self.entry_price:.2f}, "
            f"Current=${self.current_price:.2f} ({gain_pct:+.2f}%), "
            f"HWM=${self.high_water_mark:.2f}, "
            f"Stop=${self.current_stop_loss:.2f}, "
            f"Trailing={'ACTIVE' if self.trailing_stop_active else 'INACTIVE'})"
        )
