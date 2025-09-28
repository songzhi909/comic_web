"""
Main application file for Comic Web
"""

import sys
import os

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

if __name__ == '__main__':
    logger.info("Starting Comic Web application")
    app.run(debug=True, host='0.0.0.0', port=5000)