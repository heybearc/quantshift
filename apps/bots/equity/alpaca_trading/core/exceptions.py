"""
Custom exceptions for the Alpaca Trading Bot.

This module defines custom exceptions for different types of errors that can occur
in the trading bot, making error handling more specific and informative.
"""

class TradingError(Exception):
    """Base exception for trading-related errors."""
    pass


class ConfigurationError(TradingError):
    """Raised when there is a configuration error."""
    pass


class APIConnectionError(TradingError):
    """Raised when there is an error connecting to the Alpaca API."""
    pass


class APIError(TradingError):
    """Raised when the Alpaca API returns an error response."""
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(f"Status {status_code}: {message}" if status_code else message)


class OrderExecutionError(TradingError):
    """Raised when there is an error executing an order."""
    pass


class InsufficientFundsError(OrderExecutionError):
    """Raised when there are insufficient funds to execute an order."""
    pass


class PositionNotFoundError(OrderExecutionError):
    """Raised when trying to close a non-existent position."""
    pass


class MarketClosedError(TradingError):
    """Raised when attempting to trade when the market is closed."""
    pass


class DataError(TradingError):
    """Raised when there is an error with market data."""
    pass


class StrategyError(TradingError):
    """Raised when there is an error in the trading strategy."""
    pass
