"""Configuration using Pydantic BaseSettings.

This supersedes the previous *config.py* dataclass while keeping the same field
names so that existing code continues to work once it switches import path to
``from alpaca_trading import config``.

The class automatically loads variables from environment and a ``.env`` file
(compatible with *python-dotenv* if present). You can also instantiate it with
explicit keyword arguments for tests.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

try:
    from pydantic_settings import BaseSettings  # Pydantic v2
except ModuleNotFoundError:  # pragma: no cover
    from pydantic.v1 import BaseSettings  # type: ignore

from pydantic import Field, validator
from dotenv import load_dotenv

# Ensure .env is loaded before Settings evaluates env vars.
load_dotenv()
logger = logging.getLogger(__name__)


def _default_log_file() -> str:
    return "trading_bot.log"


class Settings(BaseSettings):
    # Alpaca
    api_key: str = Field("", env="APCA_API_KEY_ID")
    api_secret: str = Field("", env="APCA_API_SECRET_KEY")
    base_url: str = Field("https://paper-api.alpaca.markets", env="APCA_API_BASE_URL")
    api_version: str = "v2"

    # Email / SMTP (Brevo)
    email_host: str = Field("smtp-relay.brevo.com", env="EMAIL_HOST")
    email_port: int = Field(587, env="EMAIL_PORT")
    email_user: str = Field("", env="EMAIL_USER")
    email_pass: str = Field("", env="EMAIL_PASS")
    email_from: str = Field("", env="EMAIL_FROM")
    email_to: str = Field("", env="EMAIL_TO")

    # Trading params
    default_symbol: str = "AAPL"
    short_window: int = 5
    long_window: int = 20
    quantity: int = 1
    risk_per_trade: float = 0.01  # 1%

    # Schedule
    check_interval: int = 15
    market_open: str = "09:30"
    market_close: str = "16:00"

    # Logging
    log_level: str = "INFO"
    log_file: str = Field(default_factory=_default_log_file)

    @validator("api_key", "api_secret", "email_host", "email_user", "email_pass", "email_from", "email_to")
    def _not_empty(cls, v: str) -> str:
        if not v:
            logger.warning("Environment variable is missing")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


# Singleton – module import creates one settings instance.
settings = Settings()

# Legacy alias so that other modules can ``from alpaca_trading import config``
config = settings  # type: ignore  # re-export same object
