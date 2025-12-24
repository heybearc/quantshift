"""Main entry point for crypto bot."""

import os
import sys
from dotenv import load_dotenv
import structlog

from quantshift_crypto.bot import CryptoBot

# Load environment variables
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


def main() -> None:
    """Main function."""
    # Get API credentials from environment
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")
    
    if not api_key or not api_secret:
        logger.error("missing_credentials", message="COINBASE_API_KEY and COINBASE_API_SECRET required")
        sys.exit(1)
    
    # Initialize and run bot
    try:
        bot = CryptoBot(api_key=api_key, api_secret=api_secret)
        bot.run()
    except KeyboardInterrupt:
        logger.info("bot_stopped_by_user")
    except Exception as e:
        logger.error("bot_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
