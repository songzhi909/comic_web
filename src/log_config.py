import os
import sys
import logging
import io
from logging.handlers import RotatingFileHandler

# Import our configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def setup_logging():
    """
    Setup logging configuration
    """
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        logs_dir = os.path.join(os.path.dirname(sys.executable), 'logs')
    else:
        # Running in development
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Configure logging
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with UTF-8 encoding if enabled
    if Config.LOG_ENABLE_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        # Ensure UTF-8 encoding for console output to prevent UnicodeEncodeError on Windows
        if isinstance(console_handler.stream, io.TextIOWrapper):
            console_handler.stream.reconfigure(encoding='utf-8')
        root_logger.addHandler(console_handler)
    
    # Create file handler with rotation if enabled
    if Config.LOG_ENABLE_FILE:
        log_file = os.path.join(logs_dir, 'comic_web.log')
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=Config.LOG_FILE_MAX_BYTES,
            backupCount=Config.LOG_FILE_BACKUP_COUNT,
            encoding='utf-8'  # Explicitly set UTF-8 encoding to handle Unicode characters
        )
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
    
    # Set the level for werkzeug logger specifically to match our configuration
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    return root_logger