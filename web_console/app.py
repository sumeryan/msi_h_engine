"""
Web Console for Hierarchical Engine Logs

This module provides a web interface for viewing and filtering logs 
from the engine_eval module in a console-style display.

Features:
- Real-time log viewing
- Filtering by log level
- Highlighting for different log levels
- Search functionality
- Formula evaluation visualization

Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com
"""
import os
import json
import re
import time
import threading
from datetime import datetime
from collections import deque
from flask import Flask, render_template, jsonify, request, Response
import log
from log.logger import setup_logger

# Setup logging for the web console itself
logger = log.get_logger("Web Console")

# Flask application
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Configuration
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
DEFAULT_LOG_FILE = "engine.log"
MAX_LOGS = 1000  # Maximum number of log entries to keep in memory
POLL_INTERVAL = 1.0  # Seconds between log file checks

# In-memory log storage for quick access
log_buffer = deque(maxlen=MAX_LOGS)
last_read_position = 0
buffer_lock = threading.Lock()

# Regular expression to parse log entries
LOG_PATTERN = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - ([^-]+) - (.+)'

# Define log levels and their corresponding colors
LOG_LEVELS = {
    "DEBUG": "gray",
    "INFO": "green",
    "WARNING": "orange",
    "ERROR": "red",
    "CRITICAL": "purple"
}

def parse_log_line(line):
    """
    Parse a log line into its components.
    
    Args:
        line (str): A log line to parse
        
    Returns:
        dict: Parsed log entry or None if it's not a valid log line
    """
    match = re.match(LOG_PATTERN, line)
    if match:
        timestamp, level, module, message = match.groups()
        return {
            "timestamp": timestamp,
            "level": level,
            "module": module.strip(),
            "message": message.strip(),
            "color": LOG_LEVELS.get(level, "black")
        }
    return None

def read_log_file(path=None, max_lines=None, filter_module=None, filter_level=None, search=None):
    """
    Read and parse log file.
    
    Args:
        path (str): Path to log file, default is logs/engine.log
        max_lines (int): Maximum number of lines to read
        filter_module (str): Only include logs from this module
        filter_level (str): Minimum log level to include
        search (str): Text to search for in log messages
        
    Returns:
        list: List of parsed log entries
    """
    global last_read_position
    
    if path is None:
        path = os.path.join(DEFAULT_LOG_DIR, DEFAULT_LOG_FILE)
    
    logger.debug(f"Reading log file: {path}")
    
    # Log level precedence for filtering
    level_order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    min_level_idx = level_order.index(filter_level) if filter_level in level_order else 0
    
    try:
        # Check file size and open file
        if not os.path.exists(path):
            logger.warning(f"Log file does not exist: {path}")
            return []
            
        file_size = os.path.getsize(path)
        new_logs = []
        
        with open(path, 'r', encoding='utf-8') as f:
            # If file has been rotated (size smaller than last position), start from beginning
            if file_size < last_read_position:
                last_read_position = 0
            
            # Position at the last read point
            if last_read_position > 0:
                f.seek(last_read_position)
            
            # Read and parse new lines
            for line in f:
                log_entry = parse_log_line(line)
                if log_entry:
                    # Apply filters
                    if (filter_module is None or filter_module in log_entry["module"]) and \
                       (filter_level is None or level_order.index(log_entry["level"]) >= min_level_idx) and \
                       (search is None or search.lower() in line.lower()):
                        new_logs.append(log_entry)
                
            # Update the last read position
            last_read_position = f.tell()
        
        # Add new logs to the buffer
        with buffer_lock:
            for log_entry in new_logs:
                log_buffer.append(log_entry)
            
            # Apply filters to the buffer for returning
            filtered_logs = list(log_buffer)
            if filter_module or filter_level or search:
                filtered_logs = [
                    log for log in filtered_logs
                    if (filter_module is None or filter_module in log["module"]) and
                       (filter_level is None or level_order.index(log["level"]) >= min_level_idx) and
                       (search is None or search.lower() in json.dumps(log).lower())
                ]
                
            # Limit the number of logs if max_lines is provided
            if max_lines and len(filtered_logs) > max_lines:
                filtered_logs = filtered_logs[-max_lines:]
                
            logger.debug(f"Read {len(new_logs)} new log entries, returning {len(filtered_logs)} filtered entries")
            return filtered_logs
        
    except Exception as e:
        logger.error(f"Error reading log file: {str(e)}", exc_info=True)
        return [{"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "level": "ERROR", 
                "module": "Web Console", 
                "message": f"Error reading log file: {str(e)}",
                "color": "red"}]

def get_log_files():
    """
    Get a list of available log files.
    
    Returns:
        list: List of log files in the logs directory
    """
    log_files = []
    try:
        log_files = [f for f in os.listdir(DEFAULT_LOG_DIR) 
                    if os.path.isfile(os.path.join(DEFAULT_LOG_DIR, f)) 
                    and f.endswith('.log')]
        log_files.sort(key=lambda f: os.path.getmtime(os.path.join(DEFAULT_LOG_DIR, f)), reverse=True)
    except Exception as e:
        logger.error(f"Error reading log directory: {str(e)}", exc_info=True)
    
    return log_files

def background_log_reader():
    """Background thread to continuously read logs"""
    while True:
        try:
            read_log_file()  # Read logs without filters
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Error in background log reader: {str(e)}", exc_info=True)
            time.sleep(POLL_INTERVAL * 2)  # Wait longer after an error

# Start the background log reader thread
log_reader_thread = None

@app.route('/')
def index():
    """Render the main console page"""
    available_log_files = get_log_files()
    
    # Get unique modules from the log buffer
    with buffer_lock:
        log_modules = list(set(entry["module"] for entry in log_buffer if "module" in entry))
    
    return render_template('console.html', 
                          log_files=available_log_files, 
                          log_levels=list(LOG_LEVELS.keys()),
                          log_modules=sorted(log_modules))

@app.route('/api/logs')
def get_logs():
    """API endpoint to get logs with optional filtering"""
    log_file = request.args.get('file', DEFAULT_LOG_FILE)
    filter_level = request.args.get('level', None)
    filter_module = request.args.get('module', None)
    search_text = request.args.get('search', None)
    max_lines = request.args.get('max', None)
    
    if max_lines is not None:
        try:
            max_lines = int(max_lines)
        except ValueError:
            max_lines = None
    
    # For this endpoint, read directly from file to refresh
    logs = read_log_file(
        path=os.path.join(DEFAULT_LOG_DIR, log_file),
        max_lines=max_lines,
        filter_module=filter_module,
        filter_level=filter_level,
        search=search_text
    )
    
    return jsonify(logs)

@app.route('/api/logs/updates')
def log_updates():
    """
    API endpoint to poll for new logs
    This is a safer alternative to streaming for environments where SSE may not work
    """
    since = request.args.get('since', None)
    log_file = request.args.get('file', DEFAULT_LOG_FILE)
    filter_level = request.args.get('level', None)
    filter_module = request.args.get('module', None)
    search_text = request.args.get('search', None)
    
    # Parse since timestamp
    if since:
        try:
            since_time = datetime.strptime(since, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                since_time = datetime.strptime(since, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                since_time = None
    else:
        since_time = None
    
    # Get filtered logs
    with buffer_lock:
        all_logs = list(log_buffer)
        
        # Apply filters
        level_order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        min_level_idx = level_order.index(filter_level) if filter_level in level_order else 0
        
        filtered_logs = [
            log for log in all_logs
            if (filter_module is None or filter_module in log["module"]) and
               (filter_level is None or level_order.index(log["level"]) >= min_level_idx) and
               (search_text is None or search_text.lower() in json.dumps(log).lower())
        ]
        
        # Filter by timestamp if provided
        if since_time:
            filtered_logs = [
                log for log in filtered_logs 
                if datetime.strptime(log["timestamp"], "%Y-%m-%d %H:%M:%S") > since_time
            ]
    
    # Get current timestamp for the next poll
    current_time = datetime.now()
    
    return jsonify({
        "logs": filtered_logs,
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    })

@app.route('/api/log_files')
def api_log_files():
    """API endpoint to get available log files"""
    log_files = get_log_files()
    return jsonify(log_files)

@app.route('/api/log_modules')
def api_log_modules():
    """API endpoint to get all log modules found in logs"""
    with buffer_lock:
        log_modules = list(set(entry["module"] for entry in log_buffer if "module" in entry))
    return jsonify(sorted(log_modules))

def start_web_console(host="0.0.0.0", port=5000, debug=False):
    """
    Start the web console application.
    
    Args:
        host (str): Host address to bind to
        port (int): Port to listen on
        debug (bool): Whether to run in debug mode
    """
    global log_reader_thread
    
    logger.info(f"Starting web console on {host}:{port}")
    
    # Pre-load some logs to populate the buffer
    read_log_file()
    
    # Start background log reader if not already running
    if log_reader_thread is None:
        log_reader_thread = threading.Thread(target=background_log_reader, daemon=True)
        log_reader_thread.start()
        logger.info("Started background log reader thread")
    
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    start_web_console(debug=True)