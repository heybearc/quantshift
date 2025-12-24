"""
Automated Trading Bot Scheduler

This module handles the scheduling and execution of the trading strategy
at regular intervals during market hours.
"""
import time
import logging
import schedule
from datetime import datetime, time as dt_time
from typing import Dict, Any, Optional

from config import config
from exceptions import TradingError, MarketClosedError
from notifier import notifier
from strategy import TradingBot

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format=config.log_format,
    handlers=[
        logging.FileHandler(config.log_file),
        logging.StreamHandler()
    ]
)

# Get logger for this module
logger = logging.getLogger(__name__)

class TradingScheduler:
    """Handles scheduling and execution of trading jobs."""
    
    def __init__(self):
        """Initialize the trading scheduler with a trading bot instance."""
        self.bot = TradingBot()
        self._running = False
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.
        
        Returns:
            bool: True if market is open, False otherwise
        """
        now = datetime.now()
        
        # Check if it's a weekend
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Parse market hours from config
        try:
            market_open_time = datetime.strptime(config.market_open, '%H:%M').time()
            market_close_time = datetime.strptime(config.market_close, '%H:%M').time()
        except ValueError as e:
            logger.error(f"Invalid market hours format in config: {e}")
            raise MarketClosedError("Invalid market hours configuration")
        
        current_time = now.time()
        return market_open_time <= current_time <= market_close_time
    
    def run_trading_job(self) -> Dict[str, Any]:
        """
        Execute the trading strategy with proper error handling.
        
        Returns:
            Dict containing the result of the trading strategy execution
        """
        if not self.is_market_open():
            logger.info("Market is closed. Skipping this run.")
            return {'status': 'skipped', 'reason': 'market_closed'}
        
        try:
            logger.info("Starting trading strategy execution...")
            result = self.bot.run_strategy()
            
            # Log the result
            logger.info(
                "Strategy execution completed: %s - %s",
                result.get('status', 'unknown'),
                result.get('message', 'No message')
            )
            
            # Send notification for important events
            if result.get('status') in ['buy', 'sell']:
                notifier.send_email(
                    f"Trade Executed - {result['status'].title()}",
                    result['message']
                )
                
            return result
            
        except Exception as e:
            error_msg = f"Error in trading job: {str(e)}"
            logger.error(error_msg, exc_info=True)
            notifier.send_email("Trading Bot Error", error_msg)
            return {'status': 'error', 'message': error_msg}
    
    def start(self, run_immediately: bool = True) -> None:
        """
        Start the trading scheduler.
        
        Args:
            run_immediately: If True, run the job immediately on start
        """
        if self._running:
            logger.warning("Scheduler is already running")
            return
            
        self._running = True
        
        # Schedule the job
        schedule.every(config.check_interval).minutes.do(self.run_trading_job)
        
        # Initial run if requested
        if run_immediately:
            self.run_trading_job()
        
        logger.info("Trading scheduler started")
        
        # Main loop
        try:
            while self._running:
                schedule.run_pending()
                time.sleep(1)  # Check every second
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Stopping scheduler...")
        except Exception as e:
            error_msg = f"Fatal error in scheduler: {str(e)}"
            logger.critical(error_msg, exc_info=True)
            notifier.send_email("Trading Bot Fatal Error", error_msg)
            raise
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the trading scheduler."""
        if not self._running:
            return
            
        self._running = False
        schedule.clear()
        logger.info("Trading scheduler stopped")

def main() -> None:
    """Main entry point for the automated trading bot."""
    try:
        logger.info("Starting Alpaca Trading Bot...")
        
        # Create and start the scheduler
        scheduler = TradingScheduler()
        scheduler.start()
        
    except Exception as e:
        error_msg = f"Failed to start trading bot: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        notifier.send_email("Trading Bot Startup Error", error_msg)
        raise

if __name__ == "__main__":
    main()