"""
Routes for the Comic Web application
"""

import os
import json
import logging
import sys
from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for
from werkzeug.utils import secure_filename

# Add the src directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from comics_app.models import Comic, ComicImage
from comics_app.utils import get_comic_images, get_comic_cover, is_path_safe

logger = logging.getLogger(__name__)

# Metadata file name
METADATA_FILE = "metadata.json"
BOOKMARKS_FILE = "bookmarks.json"

def load_comic_metadata(comic_name):
    """Load metadata for a specific comic"""
    metadata_path = os.path.join(Config.COMICS_DIR, comic_name, METADATA_FILE)
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata for {comic_name}: {str(e)}")
    return {}

def save_comic_metadata(comic_name, metadata):
    """Save metadata for a specific comic"""
    metadata_path = os.path.join(Config.COMICS_DIR, comic_name, METADATA_FILE)
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving metadata for {comic_name}: {str(e)}")
        return False

def load_bookmarks():
    """Load bookmarks from file"""
    bookmarks_path = os.path.join(Config.COMICS_DIR, BOOKMARKS_FILE)
    if os.path.exists(bookmarks_path):
        try:
            with open(bookmarks_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading bookmarks: {str(e)}")
    return {}

def save_bookmarks(bookmarks):
    """Save bookmarks to file"""
    bookmarks_path = os.path.join(Config.COMICS_DIR, BOOKMARKS_FILE)
    try:
        with open(bookmarks_path, 'w', encoding='utf-8') as f:
            json.dump(bookmarks, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving bookmarks: {str(e)}")
        return False

def get_all_comics():
    """Get all comics with their metadata"""
    comics = []
    if not os.path.exists(Config.COMICS_DIR):
        logger.warning("Comics directory does not exist")
        return comics
    
    try:
        for item in sorted(os.listdir(Config.COMICS_DIR)):
            item_path = os.path.join(Config.COMICS_DIR, item)
            if os.path.isdir(item_path):
                # Load metadata for the comic
                metadata = load_comic_metadata(item)
                
                # Get cover image
                cover = get_comic_cover(Config.COMICS_DIR, item)
                
                comic = Comic(
                    name=item,
                    cover_image=cover,
                    metadata=metadata
                )
                comics.append(comic)
    except Exception as e:
        logger.error(f"Error scanning comics directory: {str(e)}")
        
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
    
    @app.route('/')
    def index():
        """Main page showing all comics"""
        search_query = request.args.get('search', '').lower()
        comics = get_all_comics()
        
        # Apply search filter if provided
        if search_query:
            comics = [comic for comic in comics 
                     if search_query in comic.name.lower() or 
                        (comic.metadata and (
                            search_query in comic.metadata.get('title', '').lower() or
                            search_query in comic.metadata.get('author', '').lower() or
                            search_query in comic.metadata.get('tags', '').lower()
                        ))]
        
        return render_template('index.html', comics=comics, search_query=search_query)
    
    @app.route('/comic/<name>')
    def comic(name):
        """Page for viewing a specific comic"""
        if not is_path_safe(name):
            logger.warning(f"Unsafe path attempt: {name}")
            return "Invalid comic name", 400
            
        comic_path = os.path.join(Config.COMICS_DIR, name)
        if not os.path.exists(comic_path):
            logger.warning(f"Comic not found: {name}")
            return "Comic not found", 404
            
        # Load metadata
        metadata = load_comic_metadata(name)
        comic_title = metadata.get('title', name)
            
        # Get first batch of images
        all_images = get_comic_images(Config.COMICS_DIR, name)
        initial_images = all_images[:Config.IMAGES_PER_LOAD]
        
        return render_template('comic.html', 
                             comic_name=name,
                             comic_title=comic_title,
                             images=initial_images,
                             total_images=len(all_images))
    
    @app.route('/api/comic/<name>/images')
    def api_comic_images(name):
        """API endpoint for getting comic images with pagination"""
        if not is_path_safe(name):
            return jsonify({"error": "Invalid comic name"}), 400
            
        page = int(request.args.get('page', 1))
        all_images = get_comic_images(Config.COMICS_DIR, name)
        
        start_idx = (page - 1) * Config.IMAGES_PER_LOAD
        end_idx = start_idx + Config.IMAGES_PER_LOAD
        
        images_batch = all_images[start_idx:end_idx]
        
        return jsonify({
            "images": images_batch,
            "has_more": end_idx < len(all_images),
            "total": len(all_images)
        })
    
    @app.route('/comic/<name>/image/<filename>')
    def comic_image(name, filename):
        """Serve a specific comic image"""
        if not is_path_safe(name) or not is_path_safe(filename):
            logger.warning(f"Unsafe path attempt: {name}/{filename}")
            return "Invalid path", 400
            
        comic_path = os.path.join(Config.COMICS_DIR, name)
        return send_from_directory(comic_path, filename)
    
    @app.route('/comic/<name>/cover')
    def comic_cover(name):
        """Serve the cover image for a comic"""
        if not is_path_safe(name):
            logger.warning(f"Unsafe path attempt: {name}")
            return "Invalid comic name", 400
            
        cover = get_comic_cover(Config.COMICS_DIR, name)
        if not cover:
            return "Cover not found", 404
            
        comic_path = os.path.join(Config.COMICS_DIR, name)
        return send_from_directory(comic_path, cover)
    
    @app.route('/api/comic/<name>/metadata', methods=['GET', 'POST'])
    def comic_metadata(name):
        """API endpoint for getting or updating comic metadata"""
        if not is_path_safe(name):
            return jsonify({"error": "Invalid comic name"}), 400
            
        if request.method == 'GET':
            metadata = load_comic_metadata(name)
            return jsonify(metadata)
        elif request.method == 'POST':
            metadata = request.get_json()
            if save_comic_metadata(name, metadata):
                return jsonify({"success": True})
            else:
                return jsonify({"error": "Failed to save metadata"}), 500
    
    @app.route('/api/bookmarks', methods=['GET', 'POST'])
    def bookmarks():
        """API endpoint for getting or updating bookmarks"""
        if request.method == 'GET':
            bookmarks_data = load_bookmarks()
            return jsonify(bookmarks_data)
        elif request.method == 'POST':
            bookmarks_data = request.get_json()
            if save_bookmarks(bookmarks_data):
                return jsonify({"success": True})
            else:
                return jsonify({"error": "Failed to save bookmarks"}), 500
    
    return app