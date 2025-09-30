"""
Routes for the Comic Web application
"""

import os
import json
import logging
import sys

# Add the src directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for, abort
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException

from config import Config
from comics_app.models import Comic, ComicImage
from comics_app.utils import get_comic_images, get_comic_cover, is_path_safe, get_image_size
from comics_app.database import (
    init_db, 
    get_comic_metadata, 
    save_comic_metadata, 
    get_all_comics as db_get_all_comics,
    save_bookmark,
    remove_bookmark,
    get_bookmarks,
    sync_comics_with_db
)

logger = logging.getLogger(__name__)

def get_all_comics():
    """Get all comics with their metadata"""
    # Sync comics directory with database
    sync_comics_with_db()
    
    # Get comics from database
    db_comics = db_get_all_comics()
    comics = []
    
    for db_comic in db_comics:
        # Skip hidden comics (starting with dot)
        if db_comic['name'].startswith('.'):
            continue
            
        comic = Comic(
            name=db_comic['name'],
            cover_image=db_comic['cover_image'],
            metadata={
                'title': db_comic['title'],
                'author': db_comic['author'],
                'tags': db_comic['tags'],
                'description': db_comic['description']
            }
        )
        comics.append(comic)
        
    return comics

def create_app():
    """Create and configure the Flask application"""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Set template and static folders explicitly with absolute paths
    template_dir = os.path.join(project_root, '..', 'templates')
    static_dir = os.path.join(project_root, '..', 'static')
    
    app = Flask(__name__, 
                template_folder=os.path.abspath(template_dir),
                static_folder=os.path.abspath(static_dir))
    
    # Initialize database
    with app.app_context():
        init_db()
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        return render_template('error.html', 
                             title="Page Not Found",
                             message="The page you are looking for does not exist.",
                             error_code=404), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {error}")
        return render_template('error.html', 
                             title="Internal Server Error",
                             message="An unexpected error occurred. Please try again later.",
                             error_code=500), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all uncaught exceptions"""
        # Pass through HTTP errors
        if isinstance(e, HTTPException):
            return e
        
        # Log the error
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        
        # Return a generic error page for production
        return render_template('error.html',
                             title="Unexpected Error",
                             message="An unexpected error occurred.",
                             error_code=500), 500
    
    @app.route('/')
    def index():
        """Main page showing all comics"""
        try:
            search_query = request.args.get('search', '').lower()
            comics = get_all_comics()
            
            # Apply search filter if provided
            if search_query:
                comics = [comic for comic in comics 
                         if search_query in comic.name.lower() or 
                            (comic.metadata and (
                                search_query in (comic.metadata.get('title') or '').lower() or
                                search_query in (comic.metadata.get('author') or '').lower() or
                                search_query in (comic.metadata.get('tags') or '').lower()
                            ))]
            
            return render_template('index.html', comics=comics, search_query=search_query)
        except Exception as e:
            logger.error(f"Error in index route: {e}")
            abort(500)
    
    @app.route('/comic/<name>')
    def comic(name):
        """Page for viewing a specific comic"""
        try:
            if not is_path_safe(name):
                logger.warning(f"Unsafe path attempt: {name}")
                abort(400)
                
            comic_path = os.path.join(Config.COMICS_DIR, name)
            if not os.path.exists(comic_path):
                logger.warning(f"Comic not found: {name}")
                abort(404)
                
            # Load metadata
            metadata = get_comic_metadata(name)
            comic_title = metadata.get('title', name)
                
            # Get first batch of images
            all_images = get_comic_images(Config.COMICS_DIR, name)
            initial_images = all_images[:Config.IMAGES_PER_LOAD]
            
            return render_template('comic.html', 
                                 comic_name=name,
                                 comic_title=comic_title,
                                 images=initial_images,
                                 total_images=len(all_images))
        except Exception as e:
            logger.error(f"Error in comic route for {name}: {e}")
            abort(500)
    
    @app.route('/api/comic/<name>/images')
    def api_comic_images(name):
        """API endpoint for getting comic images with pagination"""
        try:
            if not is_path_safe(name):
                return jsonify({"error": "Invalid comic name"}), 400
                
            page = int(request.args.get('page', 1))
            all_images = get_comic_images(Config.COMICS_DIR, name)
            
            start_idx = (page - 1) * Config.IMAGES_PER_LOAD
            end_idx = start_idx + Config.IMAGES_PER_LOAD
            
            images_batch = all_images[start_idx:end_idx]
            
            # Add image size information for better rendering performance
            images_with_info = []
            for image in images_batch:
                width, height = get_image_size(Config.COMICS_DIR, name, image)
                images_with_info.append({
                    'filename': image,
                    'width': width,
                    'height': height
                })
            
            return jsonify({
                "images": images_with_info,
                "has_more": end_idx < len(all_images),
                "total": len(all_images)
            })
        except Exception as e:
            logger.error(f"Error in api_comic_images for {name}: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/comic/<name>/image/<filename>')
    def comic_image(name, filename):
        """Serve a specific comic image"""
        try:
            if not is_path_safe(name) or not is_path_safe(filename):
                logger.warning(f"Unsafe path attempt: {name}/{filename}")
                abort(400)
                
            comic_path = os.path.join(Config.COMICS_DIR, name)
            return send_from_directory(comic_path, filename)
        except FileNotFoundError:
            logger.warning(f"Image not found: {name}/{filename}")
            abort(404)
        except Exception as e:
            logger.error(f"Error serving image {name}/{filename}: {e}")
            abort(500)
    
    @app.route('/comic/<name>/cover')
    def comic_cover(name):
        """Serve the cover image for a comic"""
        try:
            if not is_path_safe(name):
                logger.warning(f"Unsafe path attempt: {name}")
                abort(400)
                
            logger.debug(f"Attempting to get cover for comic: {name}")
            cover = get_comic_cover(Config.COMICS_DIR, name)
            if not cover:
                logger.info(f"No cover found for comic: {name}")
                abort(404)
                
            logger.debug(f"Found cover image: {cover} for comic: {name}")
            comic_path = os.path.join(Config.COMICS_DIR, name)
            logger.debug(f"Comic path: {comic_path}")
            return send_from_directory(comic_path, cover)
        except FileNotFoundError as e:
            logger.warning(f"Cover file not found for {name}: {e}")
            abort(404)
        except Exception as e:
            logger.error(f"Error serving cover for {name}: {e}", exc_info=True)
            abort(500)
    
    @app.route('/api/comic/<name>/metadata', methods=['GET', 'POST'])
    def comic_metadata(name):
        """API endpoint for getting or updating comic metadata"""
        try:
            if not is_path_safe(name):
                return jsonify({"error": "Invalid comic name"}), 400
                
            if request.method == 'GET':
                metadata = get_comic_metadata(name)
                return jsonify(metadata)
            elif request.method == 'POST':
                metadata = request.get_json()
                # Ensure we don't accidentally overwrite the cover_image with null
                # If cover_image is not in the metadata, explicitly set it to None
                # so the save function knows to keep the existing one
                if 'cover_image' not in metadata:
                    metadata['cover_image'] = None
                    
                if save_comic_metadata(name, metadata):
                    return jsonify({"success": True})
                else:
                    return jsonify({"error": "Failed to save metadata"}), 500
        except Exception as e:
            logger.error(f"Error in comic_metadata for {name}: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/api/bookmarks', methods=['GET', 'POST'])
    def bookmarks():
        """API endpoint for getting or updating bookmarks"""
        try:
            if request.method == 'GET':
                bookmarks_data = get_bookmarks()
                return jsonify(bookmarks_data)
            elif request.method == 'POST':
                data = request.get_json()
                if isinstance(data, dict):
                    # For backward compatibility, handle both old format and new format
                    if 'comic_name' in data and 'action' in data:
                        # New format with action
                        comic_name = data['comic_name']
                        comic_title = data.get('comic_title', comic_name)
                        action = data['action']
                        
                        if action == 'add':
                            if save_bookmark(comic_name, comic_title):
                                return jsonify({"success": True})
                            else:
                                return jsonify({"error": "Failed to save bookmark"}), 500
                        elif action == 'remove':
                            if remove_bookmark(comic_name):
                                return jsonify({"success": True})
                            else:
                                return jsonify({"error": "Failed to remove bookmark"}), 500
                    else:
                        # Old format - replace all bookmarks
                        # In this case, we'll just return success since we're not using this approach anymore
                        return jsonify({"success": True})
                else:
                    return jsonify({"error": "Invalid data format"}), 400
        except Exception as e:
            logger.error(f"Error in bookmarks API: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    return app