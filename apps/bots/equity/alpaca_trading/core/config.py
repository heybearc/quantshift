"""
Configuration settings for the Alpaca Trading Bot.

This module centralizes all configuration settings including environment variables,
API credentials, and trading parameters.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

@dataclass
class TradingConfig:
    """Trading configuration parameters."""
    # Alpaca API credentials
    api_key: str = os.getenv('APCA_API_KEY_ID', '').split('#')[0].strip()
    api_secret: str = os.getenv('APCA_API_SECRET_KEY', '').split('#')[0].strip()
    base_url: str = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets').split('#')[0].strip()
    api_version: str = 'v2'
    
    # Email configuration (for Brevo SMTP)
    email_host: str = os.getenv('EMAIL_HOST', 'smtp-relay.brevo.com').split('#')[0].strip()
    email_port: int = int(os.getenv('EMAIL_PORT', '587').split('#')[0].strip())
    email_user: str = os.getenv('EMAIL_USER', '').split('#')[0].strip()
    email_pass: str = os.getenv('EMAIL_PASS', '').split('#')[0].strip()
    email_from: str = os.getenv('EMAIL_FROM', '').split('#')[0].strip()
    email_to: str = os.getenv('EMAIL_TO', '').split('#')[0].strip()  # Can be comma-separated list
    
    # Trading parameters
    default_symbol: str = 'AAPL'
    short_window: int = 5
    long_window: int = 20
    quantity: int = 1
    risk_per_trade: float = 0.01  # 1% of portfolio per trade
    
    # Daily automation parameters
    max_positions: int = int(os.getenv('MAX_POSITIONS', '5').split('#')[0].strip())
    position_size: float = float(os.getenv('POSITION_SIZE', '1000').split('#')[0].strip())
    stop_loss_pct: float = float(os.getenv('STOP_LOSS_PCT', '0.02').split('#')[0].strip())
    
    # Advanced Scaling Strategy Parameters
    scale_out_first_pct: float = float(os.getenv('SCALE_OUT_FIRST_PCT', '0.5').split('#')[0].strip())  # 50% at +1 ATR
    scale_out_resistance_pct: float = float(os.getenv('SCALE_OUT_RESISTANCE_PCT', '0.33').split('#')[0].strip())  # 33% at resistance
    trailing_stop_atr_mult: float = float(os.getenv('TRAILING_STOP_ATR_MULT', '1.5').split('#')[0].strip())  # 1.5x ATR trailing
    min_shares_for_scaling: int = int(os.getenv('MIN_SHARES_FOR_SCALING', '2').split('#')[0].strip())  # Minimum shares for scaling
    
    # Schedule settings
    check_interval: int = 15  # minutes
    market_open: str = '09:30'
    market_close: str = '16:00'
    
    # Logging configuration
    log_level: str = 'INFO'
    log_file: str = 'trading_bot.log'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def validate(self) -> None:
        """Validate configuration settings."""
        required_vars = {
            'APCA_API_KEY_ID': self.api_key,
            'APCA_API_SECRET_KEY': self.api_secret,
            'EMAIL_HOST': self.email_host,
            'EMAIL_USER': self.email_user,
            'EMAIL_PASS': self.email_pass,
            'EMAIL_FROM': self.email_from,
            'EMAIL_TO': self.email_to
        }
        
        missing = [name for name, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        if not all([self.email_host, self.email_user, self.email_pass, self.email_from, self.email_to]):
            logging.warning("Email configuration is incomplete. Email alerts will be disabled.")
            logging.warning("Required email settings: EMAIL_HOST, EMAIL_USER, EMAIL_PASS, EMAIL_FROM, EMAIL_TO")

# Create a singleton instance of the configuration
config = TradingConfig()

# Validate configuration when module is imported
try:
    config.validate()
except ValueError as e:
    logging.error(f"Configuration error: {e}")
    raise
