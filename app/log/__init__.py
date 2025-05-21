"""
Powered by Renoir
Created by igor.goncalves@renoirgroup.com

Logging module for the hierarchical filtering engine.
This package provides utilities for consistent logging across the application.

The main entry point is the get_logger function from the logger module.
"""

from .logger import get_logger, setup_logger

# Export the get_logger function so it can be imported directly from log module
__all__ = ['get_logger', 'setup_logger']