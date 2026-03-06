"""
Trailing Stop Manager

Monitors open positions and adjusts stop-loss orders as price moves favorably.
Implements high water mark tracking and ATR-based trailing stops.
"""

import time
from typing import Dict, Optional, Any
from datetime import datetime
import structlog

from .position_tracker import PositionTracker

logger = structlog.get_logger()


class TrailingStopManager:
    """
    Manages trailing stop-loss orders for all open positions.
    
    Responsibilities:
    - Track high water marks for each position
    - Calculate trailing stop prices based on ATR
    - Update stop orders with broker when stops improve
    - Persist state to database for recovery
    """
    
    def __init__(
        self,
        executor,
        db_writer,
        config: Dict[str, Any]
    ):
        """
        Initialize trailing stop manager.
        
        Args:
            executor: Broker executor (AlpacaExecutor, CoinbaseExecutor, etc.)
            db_writer: Database writer for persistence
            config: Trailing stop configuration dict
        """
        self.executor = executor
        self.db_writer = db_writer
        self.config = config
        
        # Configuration parameters
        self.enabled = config.get('enabled', True)
        self.activation_threshold_pct = config.get('activation_threshold_pct', 0.01)
        self.trail_distance_atr_mult = config.get('trail_distance_atr_mult', 1.5)
        self.min_trail_distance_pct = config.get('min_trail_distance_pct', 0.005)
        self.update_frequency_seconds = config.get('update_frequency_seconds', 30)
        self.only_improve_stop = config.get('only_improve_stop', True)
        
        # Position trackers: symbol -> PositionTracker
        self.position_trackers: Dict[str, PositionTracker] = {}
        
        # Last update timestamp
        self.last_update = None
        
        logger.info(
            "trailing_stop_manager_initialized",
            enabled=self.enabled,
            activation_threshold=f"{self.activation_threshold_pct * 100:.1f}%",
            trail_distance=f"{self.trail_distance_atr_mult}×ATR",
            update_frequency=f"{self.update_frequency_seconds}s"
        )
    
    def add_position(
        self,
        symbol: str,
        bot_name: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        stop_order_id: Optional[str] = None,
        take_profit_order_id: Optional[str] = None,
        strategy: str = "UNKNOWN"
    ) -> PositionTracker:
        """
        Add a new position to track.
        
        Args:
            symbol: Trading symbol
            bot_name: Bot name
            entry_price: Entry price
            quantity: Position size
            stop_loss: Initial stop-loss price
            stop_order_id: Broker stop order ID
            take_profit_order_id: Broker take profit order ID
            strategy: Strategy name
            
        Returns:
            PositionTracker instance
        """
        tracker = PositionTracker(
            symbol=symbol,
            bot_name=bot_name,
            entry_price=entry_price,
            current_price=entry_price,
            quantity=quantity,
            original_stop_loss=stop_loss,
            current_stop_loss=stop_loss,
            high_water_mark=entry_price,
            trailing_stop_active=False,
            stop_order_id=stop_order_id,
            take_profit_order_id=take_profit_order_id,
            strategy=strategy,
            entered_at=datetime.utcnow()
        )
        
        self.position_trackers[symbol] = tracker
        
        logger.info(
            "position_added_to_trailing_stop_manager",
            symbol=symbol,
            entry_price=f"${entry_price:.2f}",
            stop_loss=f"${stop_loss:.2f}",
            quantity=quantity
        )
        
        return tracker
    
    def remove_position(self, symbol: str) -> None:
        """
        Remove a position from tracking (when closed).
        
        Args:
            symbol: Trading symbol
        """
        if symbol in self.position_trackers:
            del self.position_trackers[symbol]
            logger.info("position_removed_from_trailing_stop_manager", symbol=symbol)
    
    def update_positions(self, current_prices: Dict[str, float], atr_values: Dict[str, float]) -> None:
        """
        Update all position trackers with current prices and adjust stops if needed.
        
        Args:
            current_prices: Dict of symbol -> current price
            atr_values: Dict of symbol -> current ATR
        """
        if not self.enabled:
            return
        
        # Check if enough time has passed since last update
        if self.last_update:
            elapsed = (datetime.utcnow() - self.last_update).total_seconds()
            if elapsed < self.update_frequency_seconds:
                return
        
        self.last_update = datetime.utcnow()
        
        for symbol, tracker in list(self.position_trackers.items()):
            if symbol not in current_prices:
                logger.warning("no_price_data_for_position", symbol=symbol)
                continue
            
            if symbol not in atr_values:
                logger.warning("no_atr_data_for_position", symbol=symbol)
                continue
            
            current_price = current_prices[symbol]
            atr = atr_values[symbol]
            
            # Update price and high water mark
            hwm_updated = tracker.update_price(current_price)
            
            # Check if trailing stop should activate
            if not tracker.trailing_stop_active:
                if tracker.should_activate_trailing_stop(self.activation_threshold_pct):
                    tracker.activate_trailing_stop()
            
            # If trailing stop is active, calculate new stop price
            if tracker.trailing_stop_active:
                new_stop_price = tracker.calculate_trailing_stop_price(
                    trail_distance_atr_mult=self.trail_distance_atr_mult,
                    atr=atr,
                    min_trail_distance_pct=self.min_trail_distance_pct
                )
                
                # Check if stop should be updated
                if tracker.should_update_stop(new_stop_price, self.only_improve_stop):
                    # Update stop order with broker
                    success = self._update_broker_stop_order(tracker, new_stop_price)
                    
                    if success:
                        # Update tracker state
                        tracker.update_stop_loss(new_stop_price)
                        
                        # Persist to database
                        self._persist_tracker_state(tracker)
    
    def _update_broker_stop_order(
        self,
        tracker: PositionTracker,
        new_stop_price: float
    ) -> bool:
        """
        Update stop order with broker (cancel old, place new).
        
        Args:
            tracker: Position tracker
            new_stop_price: New stop price
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Cancel existing stop order if it exists
            if tracker.stop_order_id:
                try:
                    self.executor.cancel_order(tracker.stop_order_id)
                    logger.info(
                        "stop_order_cancelled",
                        symbol=tracker.symbol,
                        order_id=tracker.stop_order_id
                    )
                except Exception as e:
                    logger.warning(
                        "failed_to_cancel_stop_order",
                        symbol=tracker.symbol,
                        order_id=tracker.stop_order_id,
                        error=str(e)
                    )
            
            # Place new stop order
            new_order_id = self.executor.place_stop_order(
                symbol=tracker.symbol,
                quantity=tracker.quantity,
                stop_price=new_stop_price
            )
            
            if new_order_id:
                tracker.stop_order_id = new_order_id
                logger.info(
                    "trailing_stop_order_placed",
                    symbol=tracker.symbol,
                    stop_price=f"${new_stop_price:.2f}",
                    order_id=new_order_id
                )
                return True
            else:
                logger.error(
                    "failed_to_place_trailing_stop_order",
                    symbol=tracker.symbol,
                    stop_price=f"${new_stop_price:.2f}"
                )
                return False
                
        except Exception as e:
            logger.error(
                "error_updating_broker_stop_order",
                symbol=tracker.symbol,
                error=str(e)
            )
            return False
    
    def _persist_tracker_state(self, tracker: PositionTracker) -> None:
        """
        Persist tracker state to database.
        
        Args:
            tracker: Position tracker to persist
        """
        if not self.db_writer:
            return
        
        try:
            self.db_writer.update_position_trailing_stop(
                symbol=tracker.symbol,
                high_water_mark=tracker.high_water_mark,
                current_stop_loss=tracker.current_stop_loss,
                trailing_stop_active=tracker.trailing_stop_active,
                stop_order_id=tracker.stop_order_id
            )
        except Exception as e:
            logger.error(
                "failed_to_persist_tracker_state",
                symbol=tracker.symbol,
                error=str(e)
            )
    
    def load_from_database(self) -> None:
        """
        Load position trackers from database (for recovery after restart).
        """
        if not self.db_writer:
            return
        
        try:
            positions = self.db_writer.get_open_positions_with_trailing_stops()
            
            for pos in positions:
                tracker = PositionTracker(
                    symbol=pos['symbol'],
                    bot_name=pos['bot_name'],
                    entry_price=pos['entry_price'],
                    current_price=pos['current_price'],
                    quantity=pos['quantity'],
                    original_stop_loss=pos.get('stop_loss', pos['entry_price'] * 0.95),
                    current_stop_loss=pos.get('current_stop_loss', pos.get('stop_loss', pos['entry_price'] * 0.95)),
                    high_water_mark=pos.get('high_water_mark', pos['entry_price']),
                    trailing_stop_active=pos.get('trailing_stop_active', False),
                    stop_order_id=pos.get('stop_order_id'),
                    take_profit_order_id=pos.get('take_profit_order_id'),
                    strategy=pos.get('strategy', 'UNKNOWN'),
                    entered_at=pos.get('entered_at', datetime.utcnow())
                )
                
                self.position_trackers[pos['symbol']] = tracker
                
            logger.info(
                "position_trackers_loaded_from_database",
                count=len(self.position_trackers)
            )
            
        except Exception as e:
            logger.error("failed_to_load_trackers_from_database", error=str(e))
    
    def get_tracker(self, symbol: str) -> Optional[PositionTracker]:
        """
        Get position tracker for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            PositionTracker or None if not found
        """
        return self.position_trackers.get(symbol)
    
    def get_all_trackers(self) -> Dict[str, PositionTracker]:
        """Get all position trackers."""
        return self.position_trackers.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get trailing stop manager statistics.
        
        Returns:
            Dict with stats
        """
        total_positions = len(self.position_trackers)
        active_trailing = sum(1 for t in self.position_trackers.values() if t.trailing_stop_active)
        
        total_locked_profit = sum(
            (t.current_stop_loss - t.entry_price) * t.quantity
            for t in self.position_trackers.values()
            if t.current_stop_loss > t.entry_price
        )
        
        return {
            'enabled': self.enabled,
            'total_positions': total_positions,
            'active_trailing_stops': active_trailing,
            'inactive_trailing_stops': total_positions - active_trailing,
            'total_locked_profit': total_locked_profit,
            'last_update': self.last_update
        }
