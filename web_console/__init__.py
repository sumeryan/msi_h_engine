"""
Web Console Module for Hierarchical Engine Logs

This module provides a web-based console for viewing real-time logs from
the engine_eval module and other components of the hierarchical engine.

Usage:
    from web_console.app import start_web_console
    
    # Start the web console
    start_web_console(host="0.0.0.0", port=5000, debug=False)

Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com
"""

from .app import start_web_console

__all__ = ['start_web_console']