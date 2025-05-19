"""
Tests that the logging configuration from environment variables works correctly.
"""

import os
from log import get_logger

def main():
    """Main test function"""
    
    # Get the logger with default configuration
    logger = get_logger("test_env_config")
    
    # Log some test messages
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # Print environment variables for reference
    log_level = os.getenv("LOG_LEVEL", "Not set")
    log_max_size = os.getenv("LOG_FILE_MAX_SIZE_BYTES", "Not set")
    log_backups = os.getenv("LOG_FILE_BACKUP_COUNT", "Not set")
    
    print("\nEnvironment variables:")
    print(f"LOG_LEVEL = {log_level}")
    print(f"LOG_FILE_MAX_SIZE_BYTES = {log_max_size}")
    print(f"LOG_FILE_BACKUP_COUNT = {log_backups}")
    
    # Force a few log files to test rotation
    for i in range(1, 1001):
        logger.info(f"Test message {i} to fill log file: " + "X" * 1000)
    
    print("\nCheck your logs directory for rotated log files")

if __name__ == "__main__":
    main()