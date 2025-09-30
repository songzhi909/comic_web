import os
import sys
import logging
import io
from logging.handlers import RotatingFileHandler

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
    
    # Create console handler with UTF-8 encoding
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    # Ensure UTF-8 encoding for console output to prevent UnicodeEncodeError on Windows
    if isinstance(console_handler.stream, io.TextIOWrapper):
        console_handler.stream.reconfigure(encoding='utf-8')
    
    # Create file handler with rotation
    log_file = os.path.join(logs_dir, 'comic_web.log')
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # Explicitly set UTF-8 encoding to handle Unicode characters
    )
    file_handler.setFormatter(log_formatter)
    
    # Get root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger