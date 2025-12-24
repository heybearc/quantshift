"""Alpaca Trading Bot package.

This package provides a modular structure for the Alpaca Trading Bot with
clear separation of concerns:

- alpaca_trading.core: Core trading functionality (strategy, config, etc.)
- alpaca_trading.scripts: Executable trading scripts
- alpaca_trading.utils: Utility modules and helpers
"""
from __future__ import annotations

# Import key modules that should be available at the package level
from .core import config, exceptions, notifier, strategy
from .utils import error_handler, logging_config, analytics

# Initialize shared logging & settings as part of package import
from .utils.logging_config import configure_logging
from .settings import settings

configure_logging(level=settings.log_level, log_file=settings.log_file)

# Define what gets imported with `from alpaca_trading import *`
__all__ = [
    # Core modules
    'config',
    'exceptions',
    'notifier',
    'strategy',
    # Utility modules
    'error_handler',
    'logging_config',
    'analytics',
]
