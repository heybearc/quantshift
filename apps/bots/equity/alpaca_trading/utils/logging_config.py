"""
Centralized logging configuration for the Alpaca Trading Bot.

This module provides standardized logging setup for all components of the application.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from alpaca_trading.core.config import config

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

def setup_logger(name, log_file=None, level=None):
    """
    Set up a logger with standardized formatting and handlers.
    
    Args:
        name (str): Logger name, typically __name__ from the calling module
        log_file (str, optional): Log file path. If None, uses the name parameter with .log extension
        level (str, optional): Logging level. If None, uses the level from config
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # If logger already has handlers, assume it's configured
    if logger.handlers:
        return logger
    
    # Set level from config if not specified
    if level is None:
        level = getattr(logging, config.log_level.upper(), logging.INFO)
    else:
        level = getattr(logging, level.upper(), logging.INFO)
    
    logger.setLevel(level)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    # Create formatter
    formatter = logging.Formatter(config.log_format)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified or can be derived
    if log_file is None:
        # Use name as basis for log file, but make it safe for filesystem
        safe_name = name.replace(".", "_").lower()
        if safe_name == "__main__":
            # For scripts run as main, use the script filename
            if hasattr(sys, 'argv') and len(sys.argv) > 0:
                script_name = os.path.basename(sys.argv[0])
                safe_name = os.path.splitext(script_name)[0]
        
        # Use the logs directory
        log_file = os.path.join("logs", f"{safe_name}.log")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    
    # Add timestamp to log file for daily rotation
    today = datetime.now().strftime("%Y-%m-%d")
    log_file_with_date = os.path.splitext(log_file)[0] + f"_{today}.log"
    
    file_handler = logging.FileHandler(log_file_with_date)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Root logger configuration
def configure_root_logger():
    """Configure the root logger with standard settings."""
    root_logger = logging.getLogger()
    
    # If root logger already has handlers, don't reconfigure
    if root_logger.handlers:
        return
    
    # Set level from config
    level = getattr(logging, config.log_level.upper(), logging.INFO)
    root_logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(config.log_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(f"logs/alpaca_trading_{today}.log")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

def configure_logging(level=None, log_file=None):
    """
    Configure logging for the application.
    
    This is the main entry point for setting up logging across the application.
    It's imported and used by the package __init__ file.
    
    Args:
        level (str, optional): Logging level. If None, uses the level from config
        log_file (str, optional): Log file path. If None, uses default path
    """
    # Configure root logger
    configure_root_logger()
    
    # Return the root logger
    return logging.getLogger()

# Configure root logger when module is imported
configure_root_logger()
