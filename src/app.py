"""
Main application file for Comic Web
"""

import sys
import os
import threading
import time
import webbrowser

# Add the src directory to the path so we can import from our packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comics_app.routes import create_app
from comics_app.database import init_db
from log_config import setup_logging

# Setup logging
logger = setup_logging()

# Initialize database
init_db()

# Create the Flask application
app = create_app()

def open_browser():
    """Open the web browser after a short delay to ensure server is running"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    logger.info("Starting Comic Web application")
    
    # Only open browser when running as standalone executable
    if getattr(sys, 'frozen', False):
        # Start browser opening in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    # Run the Flask app
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)