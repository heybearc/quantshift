"""Main entry point for crypto bot."""

import os
import sys
import json
import logging
from dotenv import load_dotenv

from quantshift_crypto.bot import CryptoBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_credentials():
    """
    Load Coinbase API credentials.
    Supports two formats:
      1. CDP JSON key file: COINBASE_KEY_FILE=/path/to/cdp_api_key.json
         File contains {"name": "...", "privateKey": "..."}
      2. Environment variables: COINBASE_API_KEY + COINBASE_API_SECRET
    """
    key_file = os.getenv("COINBASE_KEY_FILE")
    if key_file and os.path.exists(key_file):
        with open(key_file, "r") as f:
            data = json.load(f)
        api_key = data.get("name")
        api_secret = data.get("privateKey")
        logger.info(f"Loaded credentials from CDP key file: {key_file}")
        return api_key, api_secret

    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")
    return api_key, api_secret


def main() -> None:
    """Main function."""
    api_key, api_secret = load_credentials()

    if not api_key or not api_secret:
        logger.error(
            "Missing Coinbase credentials. Set COINBASE_KEY_FILE or "
            "COINBASE_API_KEY + COINBASE_API_SECRET environment variables."
        )
        sys.exit(1)

    try:
        bot = CryptoBot(api_key=api_key, api_secret=api_secret)
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
