"""
Run Web Console

This script starts the web console for viewing engine_eval logs.

Usage:
    python run_web_console.py [--port PORT] [--host HOST] [--debug]

Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com
"""

import argparse
from web_console.app import start_web_console

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start the Engine Eval Web Console')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the web server on')
    parser.add_argument('--host', type=str, default="127.0.0.1", help='Host to bind the web server to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting Engine Eval Web Console on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    start_web_console(host=args.host, port=args.port, debug=args.debug)