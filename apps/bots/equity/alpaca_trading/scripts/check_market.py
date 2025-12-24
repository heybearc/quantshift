from datetime import timezone
from zoneinfo import ZoneInfo
import alpaca_trade_api as tradeapi
from alpaca_trading.core.config import config
from alpaca_trading.utils.logging_config import setup_logger
from alpaca_trading.utils.error_handler import error_handler, api_error_handler
from alpaca_trading.core.exceptions import MarketClosedError, APIConnectionError

# Set up logger
logger = setup_logger(__name__, log_file="logs/market_check.log")

@error_handler(context="Market status check", notify=False)
@api_error_handler
def is_market_open():
    """Check if the market is currently open.
    
    Returns:
        bool: True if the market is open, False otherwise
        
    Raises:
        APIConnectionError: If there's an error connecting to the Alpaca API
    """
    api = tradeapi.REST(
        config.api_key,
        config.api_secret,
        base_url=config.base_url,
        api_version=config.api_version
    )
    
    try:
        clock = api.get_clock()
        eastern = ZoneInfo("America/New_York")

        # Log market information
        current_time = clock.timestamp.astimezone(eastern).strftime('%Y-%m-%d %H:%M:%S %Z')
        next_open = clock.next_open.astimezone(eastern).strftime('%Y-%m-%d %H:%M:%S %Z')
        next_close = clock.next_close.astimezone(eastern).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        logger.info(f"Current time: {current_time}")
        logger.info(f"Market is {'OPEN' if clock.is_open else 'CLOSED'}")
        logger.info(f"Next market open: {next_open}")
        logger.info(f"Next market close: {next_close}")
        
        # Also print to stdout for shell script integration
        print(f"Current time: {current_time}")
        print(f"Market is {'OPEN' if clock.is_open else 'CLOSED'}")
        print(f"Next market open: {next_open}")
        print(f"Next market close: {next_close}")
        
        return clock.is_open
    except Exception as e:
        logger.error(f"Error checking market status: {str(e)}")
        raise APIConnectionError(f"Failed to check market status: {str(e)}") from e

def main():
    """Entry point for the market check script."""
    import sys
    if is_market_open():
        sys.exit(0)  # Exit code 0 means success (market is open)
    else:
        sys.exit(1)  # Exit code 1 means market is closed

if __name__ == "__main__":
    main()
