"""
Routes for the Comic Web application
"""

import os
import sys
import logging
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from comics_app.utils import get_comic_images, get_comic_cover, is_path_safe
from comics_app.models import Comic
from config import Config

logger = logging.getLogger(__name__)

def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Flask: Configured Flask application
    """
    # Create Flask app with appropriate template and static folders
    if Config.TEMPLATE_FOLDER and Config.STATIC_FOLDER:
        app = Flask(__name__, 
                   template_folder=Config.TEMPLATE_FOLDER, 
                   static_folder=Config.STATIC_FOLDER)
    else:
        app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Register routes
    register_routes(app)
    
    return app

def register_routes(app):
    """
    Register all routes with the Flask application
    
    Args:
        app (Flask): Flask application instance
    """
    
    @app.route('/')
    def index():
        """
        Main page showing list of comics with cover images
        """
        logger.info("Accessing main page")
        
        # Ensure the comics directory exists. This will create it on first run
        # if it doesn't already exist.
        if not os.path.exists(Config.COMICS_DIR):
            os.makedirs(Config.COMICS_DIR)
            logger.info(f"Created comics directory: {Config.COMICS_DIR}")
        
        comics = []
        if os.path.exists(Config.COMICS_DIR):
            for d in os.listdir(Config.COMICS_DIR):
                if os.path.isdir(os.path.join(Config.COMICS_DIR, d)):
                    cover_image = get_comic_cover(Config.COMICS_DIR, d)
                    comics.append({
                        'name': d,
                        'cover': cover_image
                    })
            logger.info(f"Found {len(comics)} comics in directory")
        else:
            logger.warning(f"Comics directory does not exist: {Config.COMICS_DIR}")
        
        return render_template('index.html', comics=comics)
    
    @app.route('/comic/<comic_name>')
    def view_comic(comic_name):
        """
        View a specific comic
        """
        logger.info(f"Accessing comic: {comic_name}")
        
        # Sanitize comic name to prevent directory traversal
        if not is_path_safe(comic_name):
            logger.warning(f"Invalid comic name attempted: {comic_name}")
            return "Invalid comic name", 400
        
        images = get_comic_images(Config.COMICS_DIR, comic_name)
        if not images:
            logger.warning(f"No images found for comic: {comic_name}")
            return "No images found for this comic", 404
        
        logger.info(f"Displaying comic {comic_name} with {len(images)} images")
        return render_template('comic.html', comic_name=comic_name, total_images=len(images))
    
    @app.route('/api/comic/<comic_name>/images')
    def api_comic_images(comic_name):
        """
        API endpoint to get comic images with pagination
        """
        logger.info(f"API request for images of comic: {comic_name}")
        
        # Sanitize comic name to prevent directory traversal
        if not is_path_safe(comic_name):
            logger.warning(f"Invalid comic name in API request: {comic_name}")
            return jsonify({'error': 'Invalid comic name'}), 400
        
        page = int(request.args.get('page', 1))
        logger.info(f"Loading page {page} for comic: {comic_name}")
        
        images = get_comic_images(Config.COMICS_DIR, comic_name)
        
        if not images:
            logger.warning(f"No images found for comic in API: {comic_name}")
            return jsonify({'error': 'No images found'}), 404
        
        start_index = (page - 1) * Config.IMAGES_PER_LOAD
        end_index = start_index + Config.IMAGES_PER_LOAD
        
        # Slice images for current page
        images_slice = images[start_index:end_index]
        
        # Prepare image URLs
        image_urls = [f'/comic/{comic_name}/image/{img}' for img in images_slice]
        
        logger.info(f"Returning {len(image_urls)} images for page {page} of {comic_name}")
        
        return jsonify({
            'images': image_urls,
            'has_more': end_index < len(images),
            'total': len(images)
        })
    
    @app.route('/comic/<comic_name>/image/<path:filename>')
    def serve_comic_image(comic_name, filename):
        """
        Serve a specific comic image
        """
        logger.info(f"Serving image: {filename} from comic: {comic_name}")
        
        # Sanitize inputs to prevent directory traversal
        if not is_path_safe(comic_name) or not is_path_safe(filename):
            logger.warning(f"Invalid path attempted - comic: {comic_name}, file: {filename}")
            return "Invalid path", 400
        
        comic_path = os.path.join(Config.COMICS_DIR, comic_name)
        logger.info(f"Serving image from path: {comic_path}")
        return send_from_directory(comic_path, filename)
    
    # New route to serve comic cover images
    @app.route('/comic/<comic_name>/cover')
    def serve_comic_cover(comic_name):
        """
        Serve the cover image for a comic (first image in directory)
        """
        logger.info(f"Serving cover for comic: {comic_name}")
        
        # Sanitize inputs to prevent directory traversal
        if not is_path_safe(comic_name):
            logger.warning(f"Invalid comic name for cover request: {comic_name}")
            return "Invalid path", 400
        
        cover_image = get_comic_cover(Config.COMICS_DIR, comic_name)
        if not cover_image:
            # Return a default "no cover" image or 404
            logger.warning(f"No cover image found for comic: {comic_name}")
            return "No cover image found", 404
        
        comic_path = os.path.join(Config.COMICS_DIR, comic_name)
        logger.info(f"Serving cover image from path: {comic_path}")
        return send_from_directory(comic_path, cover_image)