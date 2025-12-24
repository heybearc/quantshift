"""
Error handling utilities for the Alpaca Trading Bot.

This module provides standardized error handling functions to be used across the application.
"""
import sys
import traceback
from functools import wraps
from typing import Callable, Any, Optional, Type, Dict, List, Union

from alpaca_trading.utils.logging_config import setup_logger
from alpaca_trading.core.exceptions import TradingError, APIConnectionError, APIError
from alpaca_trading.core.notifier import notifier

# For backward compatibility
send_notification = notifier.send_email

# Set up logger
logger = setup_logger(__name__)

def handle_error(
    error: Exception,
    context: str = None,
    notify: bool = True,
    log_level: str = "error",
    reraise: bool = True
) -> None:
    """
    Standardized error handling function.
    
    Args:
        error: The exception that was raised
        context: Additional context about where the error occurred
        notify: Whether to send a notification about the error
        log_level: The logging level to use (debug, info, warning, error, critical)
        reraise: Whether to re-raise the exception after handling
    
    Raises:
        The original exception if reraise is True
    """
    # Get the error details
    error_type = type(error).__name__
    error_message = str(error)
    error_traceback = traceback.format_exc()
    
    # Format the error message
    if context:
        log_message = f"{context}: {error_type} - {error_message}"
    else:
        log_message = f"{error_type} - {error_message}"
    
    # Log the error
    log_func = getattr(logger, log_level.lower(), logger.error)
    log_func(log_message, exc_info=True)
    
    # Send notification if requested
    if notify:
        subject = f"Alpaca Trading Bot Error: {error_type}"
        message = f"""
Error occurred in the Alpaca Trading Bot:

Context: {context or 'Not specified'}
Error Type: {error_type}
Error Message: {error_message}

Traceback:
{error_traceback}
"""
        try:
            send_notification(subject=subject, message=message)
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {str(notify_error)}")
    
    # Re-raise the exception if requested
    if reraise:
        raise error


def error_handler(
    context: str = None,
    notify: bool = True,
    log_level: str = "error",
    reraise: bool = True,
    handle_exceptions: List[Type[Exception]] = None
):
    """
    Decorator for standardized error handling.
    
    Args:
        context: Additional context about where the error occurred
        notify: Whether to send a notification about the error
        log_level: The logging level to use (debug, info, warning, error, critical)
        reraise: Whether to re-raise the exception after handling
        handle_exceptions: List of exception types to handle. If None, handles all exceptions.
    
    Returns:
        Decorated function with standardized error handling
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if we should handle this exception type
                if handle_exceptions is not None and not any(isinstance(e, exc_type) for exc_type in handle_exceptions):
                    raise e
                
                # Use function name as context if not provided
                ctx = context or f"{func.__module__}.{func.__name__}"
                handle_error(e, ctx, notify, log_level, reraise)
                
                # Return None if we're not re-raising
                if not reraise:
                    return None
        return wrapper
    return decorator


def api_error_handler(func):
    """
    Decorator specifically for handling Alpaca API errors.
    
    This decorator will catch API-specific errors and convert them to our custom exceptions.
    
    Args:
        func: The function to decorate
    
    Returns:
        Decorated function with API error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Handle Alpaca API specific errors
            error_message = str(e).lower()
            
            # Check for specific error types
            if "connection" in error_message or "timeout" in error_message:
                raise APIConnectionError(f"API Connection Error: {str(e)}") from e
            elif "rate limit" in error_message:
                raise APIError(f"API Rate Limit Exceeded: {str(e)}", 429) from e
            elif "403" in error_message or "unauthorized" in error_message:
                raise APIError(f"API Authentication Error: {str(e)}", 403) from e
            elif "404" in error_message or "not found" in error_message:
                raise APIError(f"API Resource Not Found: {str(e)}", 404) from e
            else:
                # Re-raise as a general API error
                raise APIError(f"API Error: {str(e)}") from e
    
    return wrapper


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    context: str = None,
    notify: bool = True,
    log_level: str = "error",
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: The function to execute
        *args: Positional arguments to pass to the function
        default_return: Value to return if the function raises an exception
        context: Additional context about where the error occurred
        notify: Whether to send a notification about the error
        log_level: The logging level to use (debug, info, warning, error, critical)
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        The function's return value or the default_return if an exception occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Use function name as context if not provided
        ctx = context or f"{func.__module__}.{func.__name__}"
        handle_error(e, ctx, notify, log_level, reraise=False)
        return default_return
