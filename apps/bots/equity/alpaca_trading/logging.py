"""Central logging configuration for Alpaca Trading Bot.

Call ``configure_logging()`` once, ideally at application startup (import-time
inside :pymod:`alpaca_trading.__init__` so that every script that simply imports
``alpaca_trading`` gets sensible logging without extra code).

Features
--------
* Console + rotating-file handler (30 days of 5 MB logs)
* Log-level driven by ``LOG_LEVEL`` env var (default INFO)
* Unified format key=value to ease parsing
"""
from __future__ import annotations

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

_DEFAULT_FORMAT = (
    "%(asctime)s level=%(levelname)s name=%(name)s "
    "msg=\"%(message)s\" func=%(funcName)s lineno=%(lineno)d"
)

_LOG_FILE = os.getenv("LOG_FILE", "trading_bot.log")
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def configure_logging(level: str | int = _LOG_LEVEL, log_file: str | Path = _LOG_FILE) -> None:
    """Idempotent logging initialisation.

    Multiple calls are harmless – subsequent invocations do nothing.
    """
    if logging.getLogger().handlers:
        # Already configured – do not duplicate handlers.
        return

    # Root logger setup
    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
    root.addHandler(console)

    # Rotating file handler (daily rotation, keep 30 backups)
    _ensure_dir(Path(log_file))
    file_handler: TimedRotatingFileHandler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
    root.addHandler(file_handler)

    root.debug("Logging configured – level=%s file=%s", level, log_file)
