"""
Routes for the Comic Web application
"""

import os
import json
import logging
import sys

# Add the src directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for, abort, session
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
    sync_comics_with_db,
    get_user_by_username,
    create_user,
    verify_user_password
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
            
        # Handle tags - could be string, list, or None
        tags = db_comic['tags']
        if isinstance(tags, str):
            # Split string into list
            tags = tags.split(',') if tags else []
        elif tags is None:
            # If None, make it an empty list
            tags = []
        elif not isinstance(tags, list):
            # If it's something else, make it a list with one item
            tags = [str(tags)]
            
        comic = Comic(
            name=db_comic['name'],
            cover_image=db_comic['cover_image'],
            metadata={
                'title': db_comic['title'],
                'author': db_comic['author'],
                'tags': tags,
                'description': db_comic['description']
            }
        )
        comics.append(comic)
        
    return comics

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                template_folder=Config.TEMPLATE_FOLDER,
                static_folder=Config.STATIC_FOLDER)
    
    # Add secret key for session management
    app.secret_key = 'comic_web_secret_key_2025'
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login"""
        # If user is already logged in, redirect to main page
        if 'user' in session:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            # Verify user credentials
            if verify_user_password(username, password):
                # Store user in session
                session['user'] = username
                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('index'))
            else:
                logger.warning(f"Failed login attempt for user: {username}")
                return render_template('login.html', error='Invalid username or password')
        
        # GET request - show login page
        return render_template('login.html')
    
    @app.route('/register', methods=['POST'])
    def register():
        """Handle user registration"""
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        
        # Check if passwords match
        if password != confirm_password:
            return render_template('login.html', error='Passwords do not match')
        
        # Check if user already exists
        if get_user_by_username(username):
            return render_template('login.html', error='Username already exists')
        
        # Create new user
        if create_user(username, password):
            session['user'] = username
            logger.info(f"New user registered: {username}")
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Registration failed')
    
    @app.route('/logout')
    def logout():
        """Handle user logout"""
        session.pop('user', None)
        return redirect(url_for('login'))
    
    @app.route('/')
    def index():
        """Display the main page with all comics"""
        # Check if user is logged in
        if 'user' not in session:
            return redirect(url_for('login'))
            
        try:
            comics = get_all_comics()
            user = session['user']
            return render_template('index.html', comics=comics, user=user)
        except Exception as e:
            logger.error(f"Error loading comics: {e}")
            return render_template('error.html', error="Failed to load comics"), 500
    
    @app.route('/comic/<name>')
    def comic(name):
        """Display a specific comic"""
        # Check if user is logged in
        if 'user' not in session:
            return redirect(url_for('login'))
            
        # Security check - ensure the path is safe
        if not is_path_safe(name):
            logger.warning(f"Attempted access to unsafe path: {name}")
            abort(404)
            
        try:
            images = get_comic_images(Config.COMICS_DIR, name)
            cover_image = get_comic_cover(Config.COMICS_DIR, name)
            metadata = get_comic_metadata(name)
            
            # If no metadata found, create default
            if not metadata:
                metadata = {'title': name, 'author': 'Unknown', 'tags': [], 'description': ''}
                
            comic = Comic(name=name, cover_image=cover_image, metadata=metadata)
            return render_template('comic.html', 
                                 comic=comic, 
                                 images=images,
                                 comic_name=name,
                                 comic_title=metadata.get('title', name),
                                 total_images=len(images))
        except FileNotFoundError:
            logger.error(f"Comic not found: {name}")
            abort(404)
        except Exception as e:
            logger.error(f"Error loading comic {name}: {e}")
            return render_template('error.html', error=f"Failed to load comic: {name}"), 500

    @app.route('/comics/<name>/<path:filename>')
    def comic_image(name, filename):
        """Serve comic images"""
        # Check if user is logged in
        if 'user' not in session:
            abort(403)
            
        # Security check - ensure the path is safe
        if not is_path_safe(name) or not is_path_safe(filename):
            logger.warning(f"Attempted access to unsafe path: {name}/{filename}")
            abort(404)
            
        # Construct the full path to the comics directory
        comic_path = os.path.join(Config.COMICS_DIR, name)
        
        # Use Flask's send_from_directory to safely serve the file
        try:
            return send_from_directory(comic_path, filename)
        except FileNotFoundError:
            logger.error(f"File not found: {name}/{filename}")
            abort(404)
    
    @app.route('/comic/<name>/cover')
    def comic_cover(name):
        """Serve comic cover image"""
        # Check if user is logged in
        if 'user' not in session:
            abort(403)
            
        # Security check - ensure the path is safe
        if not is_path_safe(name):
            logger.warning(f"Attempted access to unsafe path: {name}")
            abort(404)
            
        # Get the cover image for this comic
        try:
            cover_image = get_comic_cover(Config.COMICS_DIR, name)
            if cover_image:
                # Construct the full path to the comics directory
                comic_path = os.path.join(Config.COMICS_DIR, name)
                cover_path = os.path.join(comic_path, cover_image)
                
                # Check if file exists
                if os.path.exists(cover_path):
                    return send_from_directory(comic_path, cover_image)
                else:
                    # If cover image file doesn't exist, return placeholder
                    return send_from_directory(app.static_folder, 'placeholder.png')
            else:
                # If no cover image found, return placeholder
                return send_from_directory(app.static_folder, 'placeholder.png')
        except Exception as e:
            logger.error(f"Error serving cover for {name}: {e}")
            # Return placeholder on any error
            return send_from_directory(app.static_folder, 'placeholder.png')
    
    @app.route('/api/comics')
    def api_comics():
        """API endpoint to get all comics as JSON"""
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
            
        try:
            comics = get_all_comics()
            comics_data = []
            for comic in comics:
                comics_data.append({
                    'name': comic.name,
                    'cover_image': comic.cover_image,
                    'metadata': comic.metadata
                })
            return jsonify(comics_data)
        except Exception as e:
            logger.error(f"Error in API comics endpoint: {e}")
            return jsonify({'error': 'Failed to load comics'}), 500
    
    @app.route('/api/comic/<name>/images')
    def api_comic_images(name):
        """API endpoint to get images for a specific comic"""
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
            
        # Security check
        if not is_path_safe(name):
            logger.warning(f"Attempted access to unsafe path in API: {name}")
            return jsonify({'error': 'Invalid comic name'}), 400
            
        try:
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
        except FileNotFoundError:
            logger.error(f"Comic not found in API: {name}")
            return jsonify({'error': 'Comic not found'}), 404
        except Exception as e:
            logger.error(f"Error in API comic images endpoint: {e}")
            return jsonify({'error': 'Failed to load images'}), 500
    
    @app.route('/api/bookmarks', methods=['GET', 'POST', 'DELETE'])
    def api_bookmarks():
        """API endpoint to manage bookmarks"""
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
            
        if request.method == 'GET':
            try:
                bookmarks = get_bookmarks()
                return jsonify(bookmarks)
            except Exception as e:
                logger.error(f"Error getting bookmarks: {e}")
                return jsonify({'error': 'Failed to get bookmarks'}), 500
                
        elif request.method == 'POST':
            try:
                data = request.get_json()
                # Check if data is in the new format (with comic_name and action)
                if isinstance(data, dict) and 'comic_name' in data and 'action' in data:
                    name = data.get('comic_name')
                    title = data.get('comic_title', name)
                    action = data.get('action')
                    
                    # Handle add/remove actions
                    if action == 'add':
                        if save_bookmark(name, title):
                            return jsonify({"success": True})
                        else:
                            return jsonify({"error": "Failed to save bookmark"}), 500
                    elif action == 'remove':
                        if remove_bookmark(name):
                            return jsonify({"success": True})
                        else:
                            return jsonify({"error": "Failed to remove bookmark"}), 500
                    else:
                        return jsonify({"error": "Invalid action"}), 400
                else:
                    # Old format (with name and title)
                    name = data.get('name')
                    title = data.get('title', name)
                
                if not name:
                    return jsonify({'error': 'Comic name is required'}), 400
                    
                if save_bookmark(name, title):
                    return jsonify({'message': 'Bookmark saved'}), 201
                else:
                    return jsonify({'error': 'Failed to save bookmark'}), 500
            except Exception as e:
                logger.error(f"Error saving bookmark: {e}")
                return jsonify({'error': 'Failed to save bookmark'}), 500
                
        elif request.method == 'DELETE':
            try:
                data = request.get_json()
                name = data.get('name')
                
                if not name:
                    return jsonify({'error': 'Comic name is required'}), 400
                    
                if remove_bookmark(name):
                    return jsonify({'message': 'Bookmark removed'})
                else:
                    return jsonify({'error': 'Failed to remove bookmark'}), 500
            except Exception as e:
                logger.error(f"Error removing bookmark: {e}")
                return jsonify({'error': 'Failed to remove bookmark'}), 500

    @app.route('/api/comic/<name>/metadata', methods=['GET', 'POST'])
    def api_comic_metadata(name):
        """API endpoint to get or update comic metadata"""
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
            
        # Security check
        if not is_path_safe(name):
            logger.warning(f"Attempted access to unsafe path in API: {name}")
            return jsonify({'error': 'Invalid comic name'}), 400
            
        if request.method == 'GET':
            try:
                # Get metadata from database
                metadata = get_comic_metadata(name)
                if not metadata:
                    # Return default metadata if none found
                    metadata = {
                        'title': name,
                        'author': 'Unknown',
                        'tags': [],
                        'description': ''
                    }
                return jsonify(metadata)
            except Exception as e:
                logger.error(f"Error getting metadata for {name}: {e}")
                return jsonify({'error': 'Failed to get metadata'}), 500
                
        elif request.method == 'POST':
            try:
                # Get the data from request
                data = request.get_json()
                
                # Get existing metadata
                metadata = get_comic_metadata(name)
                if not metadata:
                    metadata = {}
                
                # Update metadata fields
                if 'title' in data:
                    metadata['title'] = data['title']
                if 'author' in data:
                    metadata['author'] = data['author']
                if 'tags' in data:
                    # Handle tags - convert string to list if needed
                    if isinstance(data['tags'], str):
                        metadata['tags'] = [tag.strip() for tag in data['tags'].split(',') if tag.strip()]
                    else:
                        metadata['tags'] = data['tags']
                if 'description' in data:
                    metadata['description'] = data['description']
                
                # Save updated metadata to database
                if save_comic_metadata(name, metadata):
                    return jsonify({'success': True, 'message': 'Metadata updated successfully'})
                else:
                    return jsonify({'success': False, 'error': 'Failed to update metadata'}), 500
            except Exception as e:
                logger.error(f"Error updating metadata for {name}: {e}")
                return jsonify({'success': False, 'error': 'Failed to update metadata'}), 500

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        logger.error(f"Page not found: {error}")
        return render_template('error.html',
                             error="The page you are looking for does not exist."), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {error}")
        return render_template('error.html',
                             error="An unexpected error occurred. Please try again later."), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all uncaught exceptions"""
        # Pass through HTTP errors
        if isinstance(e, HTTPException):
            return e
        
        # Now you're handling non-HTTP exceptions only
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return render_template('error.html',
                               error="An unexpected error occurred. Please try again later."), 500

    # Add this route to enable shutdown via HTTP request (only in executable mode)
    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        """Shutdown the application (only available in executable mode)"""
        if not getattr(sys, 'frozen', False):
            # Only allow shutdown in executable mode for security
            abort(403)
        
        logger.info("Shutdown request received, shutting down server...")
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            # For non-werkzeug servers, just exit
            os._exit(0)
        else:
            func()
        return 'Server shutting down...'

    return app