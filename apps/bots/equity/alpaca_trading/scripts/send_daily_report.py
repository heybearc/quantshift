"""
Script to manually trigger the daily trading report.
"""
import sys
from datetime import datetime
from alpaca_trading.core.config import config
from alpaca_trading.utils.logging_config import setup_logger
from alpaca_trading.utils.error_handler import error_handler, api_error_handler
from alpaca_trading.core.exceptions import TradingError, APIError

# Set up logger
logger = setup_logger(__name__, log_file="logs/daily_report.log")

@error_handler(context="Daily report generation", notify=True)
@api_error_handler
def send_daily_report():
    """Generate and send the daily trading report.
    
    Returns:
        bool: True if the report was generated and sent successfully, False otherwise
        
    Raises:
        APIError: If there's an error with the Alpaca API
        TradingError: If there's an error in the trading logic
    """
    logger.info("Starting daily report generation...")
    
    # Import here to ensure logging is configured first
    import alpaca_trade_api as tradeapi
    from alpaca_trading.scripts.screener import StockScreener
    
    # Initialize the Alpaca API client
    api = tradeapi.REST(
        key_id=config.api_key,
        secret_key=config.api_secret,
        base_url=config.base_url,
        api_version=config.api_version
    )
    
    # Initialize the stock screener
    screener = StockScreener(api)
    
    # Generate and send the report
    logger.info("Generating daily trading report...")
    screener._generate_and_log_daily_report()
    logger.info("Daily report generation completed.")
    
    return True

def main():
    """Entry point for the daily report script."""
    print("Sending daily trading report...")
    if send_daily_report():
        print("✅ Daily report sent successfully!")
    else:
        print("❌ Failed to send daily report. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
