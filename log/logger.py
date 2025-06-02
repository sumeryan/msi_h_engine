"""
Powered by Renoir
Created by igor.goncalves@renoirgroup.com

This module provides logging functionality for the hierarchical filtering engine.
It sets up a configurable logger that can be used across the application for
consistent logging with various verbosity levels.

The logger is configured to:
- Write to both console and file
- Support multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include timestamp, log level, and module information in log messages
- Provide a rotation policy for log files

Configuration is done through environment variables in .env file:
- LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- LOG_TO_CONSOLE: Whether to log to console (true/false)
- LOG_TO_FILE: Whether to log to file (true/false)
- LOG_DIR: Directory to store log files
- LOG_FILE: Name of the log file
- LOG_FILE_MAX_SIZE_BYTES: Maximum size of the log file before rotation
- LOG_FILE_BACKUP_COUNT: Number of backup files to keep

Usage:
    from log.logger import get_logger
    
    # Get the logger
    logger = get_logger()
    
    # Log at different levels
    logger.debug("Detailed debugging information")
    logger.info("General information")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical error message")
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AlignedFormatter(logging.Formatter):
    """Custom formatter that handles message alignment."""
    
    # Column width for aligning colons
    COLON_COLUMN = 25
    
    def format(self, record):
        # Get the original formatted message
        original = super().format(record)
        
        # Split into timestamp/level and message parts
        parts = original.split(" - ", 2)
        if len(parts) == 3:
            timestamp_level = " - ".join(parts[:2])
            message = parts[2]
            
            # Remove original indentation
            clean_message = message.lstrip()
            
            # Check if the message contains a colon for alignment
            if ':' in clean_message and not clean_message.startswith(('=', '-', '.', '>', '<', '✓', '✗', '⚠')):
                # Split on the first colon
                colon_pos = clean_message.find(':')
                before_colon = clean_message[:colon_pos].strip()
                after_colon = clean_message[colon_pos + 1:].strip()
                
                # Calculate padding to align the colon
                padding = max(0, self.COLON_COLUMN - len(before_colon))
                aligned_message = f"{before_colon}{' ' * padding}: {after_colon}"
                
                return f"{timestamp_level} - {aligned_message}"
            else:
                # For messages without colons or special headers, keep original formatting
                # but still apply some indentation based on content
                indent_count = len(message) - len(message.lstrip())
                indent = " " * (indent_count * 2)
                
                return f"{timestamp_level} - {indent}{clean_message}"
        
        return original

# Mapping of string log levels to their numeric values
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Get configuration from environment variables
def get_env_var(name, default=None, type_cast=None):
    """
    Get an environment variable with optional type casting.
    
    Args:
        name: Name of the environment variable
        default: Default value if the environment variable is not set
        type_cast: Function to cast the value to a specific type
        
    Returns:
        The value of the environment variable, or the default if not set
    """
    value = os.getenv(name, default)
    if value is not None and type_cast is not None:
        try:
            value = type_cast(value)
        except (ValueError, TypeError):
            # If casting fails, return the default
            value = default
    return value

# Get boolean value from environment variable
def get_env_bool(name, default=False):
    """
    Get a boolean value from an environment variable.
    
    Args:
        name: Name of the environment variable
        default: Default value if the environment variable is not set
        
    Returns:
        True if the value is 'true', 'yes', 'y', 'on', or '1' (case-insensitive)
        False otherwise
    """
    value = os.getenv(name, str(default)).lower()
    return value in ('true', 'yes', 'y', 'on', '1')

# Constants with environment variable fallbacks
DEFAULT_LOG_LEVEL = get_env_var("LOG_LEVEL", "DEBUG", lambda x: LOG_LEVEL_MAP.get(x.upper(), logging.DEBUG))
DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)-8s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_DIR = get_env_var("LOG_DIR", "logs")
DEFAULT_LOG_FILE = get_env_var("LOG_FILE", "filter_engine.log")
MAX_LOG_FILE_SIZE = get_env_var("LOG_FILE_MAX_SIZE_BYTES", 1048576, int)  # Default 1MB
MAX_LOG_FILE_BACKUPS = get_env_var("LOG_FILE_BACKUP_COUNT", 3, int)

# Global logger instance
_logger = None

def setup_logger(
    name: str = "filters",
    level: int = None,
    log_format: str = DEFAULT_LOG_FORMAT,
    log_to_console: bool = None,
    log_to_file: bool = None,
    log_dir: str = None,
    log_file: str = None
) -> logging.Logger:
    """
    Configure and return a logger instance with the specified settings.
    Settings are read from parameters or environment variables if not specified.
    
    Args:
        name: Name of the logger (default: "filters")
        level: Logging level (default: from LOG_LEVEL env var or DEBUG)
        log_format: Format string for log messages
        log_to_console: Whether to log to console (default: from LOG_TO_CONSOLE env var or True)
        log_to_file: Whether to log to file (default: from LOG_TO_FILE env var or True)
        log_dir: Directory for log files (default: from LOG_DIR env var or "logs")
        log_file: Name of the log file (default: from LOG_FILE env var or "filter_engine.log")
        
    Returns:
        Configured logger instance
    """
    # Apply defaults from environment variables if not specified
    if level is None:
        level = DEFAULT_LOG_LEVEL
    
    if log_to_console is None:
        log_to_console = get_env_bool("LOG_TO_CONSOLE", True)
    
    if log_to_file is None:
        log_to_file = get_env_bool("LOG_TO_FILE", True)
    
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    
    if log_file is None:
        log_file = DEFAULT_LOG_FILE
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter using our custom AlignedFormatter
    formatter = AlignedFormatter(log_format, DEFAULT_DATE_FORMAT)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Create log directory if it doesn't exist
        full_log_dir = os.path.abspath(log_dir)
        os.makedirs(full_log_dir, exist_ok=True)
        
        # Set up rotating file handler
        log_path = os.path.join(full_log_dir, log_file)
        
        # Use the size limit from environment variable 
        max_bytes = MAX_LOG_FILE_SIZE
        backup_count = MAX_LOG_FILE_BACKUPS
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Log file configuration
        logger.debug(f"Log file configuration: {log_path}, max size: {max_bytes/1024:.1f}KB, backups: {backup_count}")
    
    # Log initial message
    logger.debug(f"Logger '{name}' initialized with level {logging.getLevelName(level)}")
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the configured logger instance. If no logger has been set up yet,
    this function will initialize one with default settings.
    
    Args:
        name: Optional name for the logger. If not provided, uses the main
              logger instance. If provided, returns a child logger of the
              main logger with the specified name.
    
    Returns:
        Configured logger instance
    """
    global _logger
    
    # Initialize the main logger if not yet initialized
    if _logger is None:
        _logger = setup_logger()
    
    # If name is provided, return a child logger
    if name:
        return logging.getLogger(f"filters.{name}")
    
    return _logger

# Initialize the logger when module is imported
_logger = setup_logger()