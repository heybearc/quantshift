"""
Configuration for the Stock Screener
"""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ScreenerConfig:
    # API Configuration
    API_KEY: str = os.getenv('APCA_API_KEY_ID', '')
    API_SECRET: str = os.getenv('APCA_API_SECRET_KEY', '')
    BASE_URL: str = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')
    
    # Stock Filters
    MIN_PRICE: float = 5.0  # Minimum stock price to consider
    MAX_PRICE: float = 1000.0  # Maximum stock price to consider
    MIN_VOLUME: int = 100000  # Minimum average daily volume
    MIN_MARKET_CAP: float = 1e9  # $1B minimum market cap
    
    # Strategy Parameters
    SHORT_WINDOW: int = 5  # Short moving average window
    LONG_WINDOW: int = 20  # Long moving average window
    
    # Position Sizing
    MAX_POSITIONS: int = 20  # Maximum number of positions to hold
    RISK_PER_TRADE: float = 0.05  # 5% of portfolio per trade
    
    # Trading Hours (Eastern Time)
    MARKET_OPEN: str = "09:30"
    MARKET_CLOSE: str = "16:00"
    
    # Screener Settings
    MAX_STOCKS_TO_SCAN: int = 200  # Maximum number of stocks to scan per run
    SCAN_INTERVAL_MINUTES: int = 60  # Minutes between scans during market hours
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "screener.log"

# Create config instance
config = ScreenerConfig()
