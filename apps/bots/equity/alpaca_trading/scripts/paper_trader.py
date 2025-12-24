import time
import schedule
from datetime import datetime, timedelta
from alpaca_trading.core.strategy import TradingBot
from alpaca_trading.core.config import config
from alpaca_trading.core.notifier import send_notification
from alpaca_trading.utils.logging_config import setup_logger
from alpaca_trading.utils.error_handler import error_handler, api_error_handler, safe_execute
from alpaca_trading.core.exceptions import TradingError, APIConnectionError, MarketClosedError

# Set up logger
logger = setup_logger(__name__, log_file="logs/paper_trading.log")

class PaperTrader:
    def __init__(self, symbols=None, paper=True, universe_limit: int = 200):
        """Initialize the paper trader.
        
        Args:
            symbols (list): List of stock symbols to trade
            paper (bool): Whether to use paper trading (default: True)
        """
        # Determine trading universe
        if symbols:
            self.symbols = symbols
        else:
            self.symbols = self._fetch_tradable_universe()

        self.paper = paper
        
        # Set paper trading URL in config if needed
        if paper:
            # No need to set environment variable as we're using config object
            pass
            
        self.bot = TradingBot()

        logger.info(f"Trading universe size: {len(self.symbols)} symbols")
        self.universe_limit = universe_limit  # cap to avoid rate limits
        self.check_interval = 60  # minutes between strategy checks
        
        # Trading hours (in Eastern Time)
        self.market_open = config.market_open
        self.market_close = config.market_close
        
        
        logger.info(f"Paper trading mode: {self.paper}")
    
    @error_handler(context="Strategy execution", notify=True)
    @api_error_handler
    def run_strategy(self, symbol, short_window=5, long_window=20):
        """Run the trading strategy for a single symbol.
        
        Args:
            symbol (str): The stock symbol to trade
            short_window (int): Short moving average window
            long_window (int): Long moving average window
            
        Returns:
            dict: Strategy execution result or None if there was an error
            
        Raises:
            TradingError: If there's an error in the trading logic
            APIConnectionError: If there's an error connecting to the Alpaca API
        """
        logger.info(f"\n{'='*50}")
        logger.info(f"Running strategy for {symbol} with MA({short_window}, {long_window})")
        
        # Run the strategy
        result = self.bot.run_strategy(
            symbol=symbol,
            short_window=short_window,
            long_window=long_window
        )
        
        # Log the result
        logger.info(f"\nStrategy Result:")
        for key, value in result.items():
            logger.info(f"{key}: {value}")
            
        return result
    
    @error_handler(context="Batch strategy execution", notify=True, reraise=False)
    def run_all_symbols(self):
        """Run the strategy for all symbols."""
        if not self.is_market_open():
            logger.info("Market is closed. Not running strategy.")
            return
            
        for symbol in self.symbols[: self.universe_limit]:
            # Use safe_execute to continue processing even if one symbol fails
            safe_execute(
                self.run_strategy,
                symbol,
                context=f"Strategy execution for {symbol}",
                notify=True,
                log_level="error"
            )
            time.sleep(1)  # Small delay between symbols to avoid rate limiting
    
    @error_handler(context="Market status check", notify=False, reraise=False)
    def is_market_open(self):
        """Check if the market is currently open.
        
        Returns:
            bool: True if the market is open, False otherwise
        """
        try:
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            
            # Check if today is a weekend
            if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
                logger.info("Market is closed (weekend)")
                return False
                
            # Check if current time is within market hours
            market_open = datetime.strptime(f"{today} {self.market_open}", "%Y-%m-%d %H:%M")
            market_close = datetime.strptime(f"{today} {self.market_close}", "%Y-%m-%d %H:%M")
            
            is_open = market_open <= now <= market_close
            logger.info(f"Market is {'open' if is_open else 'closed'} (current time: {now.strftime('%H:%M')})")
            return is_open
        except Exception as e:
            logger.error(f"Error checking market status: {str(e)}")
            return False  # Default to closed on error
    
    def schedule_tasks(self):
        """Schedule the trading tasks."""
        # Run at market open
        schedule.every().day.at(self.market_open).do(
            lambda: logger.info("Market open - Starting trading session")
        )
        
        # Run the strategy every X minutes during market hours
        schedule.every(self.check_interval).minutes.do(
            self.run_all_symbols
        )
        
        # Run at market close
        schedule.every().day.at(self.market_close).do(
            lambda: logger.info("Market close - Ending trading session")
        )
        
        logger.info(f"Scheduled tasks: Strategy will run every {self.check_interval} minutes during market hours")
    
    @error_handler(context="Paper trading bot main loop", notify=True)
    def start(self):
        """Start the paper trading bot."""
        logger.info("Starting paper trading bot...")
        self.schedule_tasks()
        
        # Initial run
        self.run_all_symbols()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time_until_next = schedule.idle_seconds()
                if time_until_next is not None:
                    # Sleep until the next scheduled run or 60 seconds, whichever is smaller
                    sleep_time = min(60, max(1, time_until_next))
                    time.sleep(sleep_time)
                else:
                    time.sleep(60)
                    
        except KeyboardInterrupt:
            logger.info("\nShutting down paper trading bot...")

    @error_handler(context="Fetch tradable universe", notify=False, reraise=False)
    @api_error_handler
    def _fetch_tradable_universe(self):
        """Fetch a list of active, tradable US equities from Alpaca.
        
        Returns:
            list: List of tradable stock symbols
            
        Note:
            Falls back to a default list of large-cap tech stocks on error
        """
        import alpaca_trade_api as tradeapi
        api = tradeapi.REST(
            config.api_key,
            config.api_secret,
            base_url=config.base_url,
            api_version=config.api_version
        )
        assets = api.list_assets(status="active", asset_class="us_equity")
        symbols = [a.symbol for a in assets if a.tradable]
        symbols.sort()
        logger.info(f"Fetched {len(symbols)} tradable symbols from Alpaca")
        return symbols
        
    # This is called if the decorated method raises an exception
    def _fetch_tradable_universe_error_handler(self, exc):
        logger.warning(f"Could not fetch asset universe: {exc}. Falling back to large-cap tech list.")
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]


def main():
    """Entry point for the paper trader script."""
    # Create and start the paper trader
    trader = PaperTrader(
        symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
        paper=True
    )
    trader.start()

if __name__ == "__main__":
    main()
