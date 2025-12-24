#!/usr/bin/env python3
"""
Stock Screener Runner

This script runs the stock screener on a schedule to find and execute trades based on
moving average crossover signals.
"""
import os
import time
import schedule
import logging
from datetime import datetime, time as dt_time, timedelta
import alpaca_trade_api as tradeapi
from check_market import is_market_open
from screener import StockScreener, run_screener

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('screener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_screener_job():
    """Job to run the stock screener and execute trades."""
    try:
        logger.info("\n" + "="*50)
        logger.info("=== Starting stock screener job ===")
        logger.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if market is open
        if not is_market_open():
            logger.warning("Market is closed. Skipping screener run.")
            return False
        
        try:
            # Get account info
            account = tradeapi.REST(
                os.getenv('APCA_API_KEY_ID'),
                os.getenv('APCA_API_SECRET_KEY'),
                base_url=os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets'),
                api_version='v2'
            ).get_account()
            logger.info(f"Account status: {account.status}")
            logger.info(f"Buying power: ${float(account.buying_power):,.2f}")
            logger.info(f"Equity: ${float(account.equity):,.2f}")
            
            # Run the screener
            opportunities = run_screener()
            
            if not opportunities:
                logger.info("No trading opportunities found this run.")
                return True
                
            logger.info(f"\nFound {len(opportunities)} trading opportunities:")
            for i, opp in enumerate(opportunities, 1):
                logger.info(f"{i}. {opp['signal']} {opp['symbol']} at ${opp['price']:.2f} - {opp['reason']}")
            
            logger.info("\n=== Screener job completed successfully ===")
            return True
            
        except Exception as e:
            logger.error(f"Error in screener execution: {str(e)}", exc_info=True)
            return False
            
    except Exception as e:
        logger.critical(f"Critical error in screener job: {str(e)}", exc_info=True)
        return False

def schedule_screener():
    """Schedule the screener to run at regular intervals during market hours."""
    # Clear any existing jobs
    schedule.clear()
    
    # Schedule runs during market hours (9:30 AM - 4:00 PM ET)
    schedule.every().monday.at("09:35").do(run_screener_job)
    schedule.every().tuesday.at("09:35").do(run_screener_job)
    schedule.every().wednesday.at("09:35").do(run_screener_job)
    schedule.every().thursday.at("09:35").do(run_screener_job)
    schedule.every().friday.at("09:35").do(run_screener_job)
    
    # Schedule hourly checks during market hours (10:30 AM - 3:30 PM ET)
    for hour in [10, 11, 12, 13, 14, 15]:
        schedule.every().monday.at(f"{hour}:30").do(run_screener_job)
        schedule.every().tuesday.at(f"{hour}:30").do(run_screener_job)
        schedule.every().wednesday.at(f"{hour}:30").do(run_screener_job)
        schedule.every().thursday.at(f"{hour}:30").do(run_screener_job)
        schedule.every().friday.at(f"{hour}:30").do(run_screener_job)
    
    logger.info("\n=== Scheduled Jobs ===")
    for job in schedule.jobs:
        logger.info(f"- {job}")
    
    # Run immediately on start if market is open
    if is_market_open():
        logger.info("\n=== Running initial scan ===")
        run_screener_job()
    else:
        logger.info("\nMarket is closed. Waiting for next scheduled run...")
    
    # Main loop
    logger.info("\n=== Screener is running. Press Ctrl+C to stop ===")
    error_count = 0
    max_errors = 5
    
    while error_count < max_errors:
        try:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
            error_count = 0  # Reset error count on successful cycle
            
        except KeyboardInterrupt:
            logger.info("\n=== Received shutdown signal. Stopping screener... ===")
            break
            
        except Exception as e:
            error_count += 1
            wait_time = min(300, 60 * error_count)  # Exponential backoff up to 5 minutes
            logger.error(f"Error in scheduler (attempt {error_count}/{max_errors}): {e}")
            logger.error(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
    
    if error_count >= max_errors:
        logger.critical("Maximum error count reached. Exiting...")
    
    logger.info("=== Screener stopped ===")

if __name__ == "__main__":
    try:
        # Initialize API
        api = tradeapi.REST(
            os.getenv('APCA_API_KEY_ID'),
            os.getenv('APCA_API_SECRET_KEY'),
            base_url=os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets'),
            api_version='v2'
        )
        
        # Check connection
        account = api.get_account()
        logger.info(f"Connected to Alpaca account: {account.account_number}")
        logger.info(f"Buying power: ${float(account.buying_power):,.2f}")
        
        # Start the scheduler
        schedule_screener()
        
    except Exception as e:
        logger.error(f"Failed to start screener: {e}", exc_info=True)
