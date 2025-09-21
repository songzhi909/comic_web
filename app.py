import os
import sys
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS

# Determine if we're running in a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    # Comics directory should always be alongside the executable
    exe_dir = os.path.dirname(sys.executable)
    comics_dir = os.path.join(exe_dir, 'comics')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    # Running in development (Python interpreter)
    app = Flask(__name__)
    # Comics directory is alongside the script file
    comics_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comics')

CORS(app)

# Configuration
COMICS_DIR = comics_dir
IMAGES_PER_LOAD = 20

def get_comic_images(comic_name):
    """
    Get all image files from a comic directory
    """
    comic_path = os.path.join(COMICS_DIR, comic_name)
    if not os.path.exists(comic_path):
        return []
    
    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
    images = []
    
    for filename in sorted(os.listdir(comic_path)):
        if filename.lower().endswith(image_extensions):
            images.append(filename)
    
    return images

def get_comic_cover(comic_name):
    """
    Get the cover image for a comic (first image in the directory)
    """
    images = get_comic_images(comic_name)
    if images:
        return images[0]
    return None

@app.route('/')
def index():
    """
    Main page showing list of comics with cover images
    """
    # Ensure the comics directory exists. This will create it on first run
    # if it doesn't already exist.
    if not os.path.exists(COMICS_DIR):
        os.makedirs(COMICS_DIR)
    
    comics = []
    if os.path.exists(COMICS_DIR):
        for d in os.listdir(COMICS_DIR):
            if os.path.isdir(os.path.join(COMICS_DIR, d)):
                cover_image = get_comic_cover(d)
                comics.append({
                    'name': d,
                    'cover': cover_image
                })
    
    return render_template('index.html', comics=comics)

@app.route('/comic/<comic_name>')
def view_comic(comic_name):
    """
    View a specific comic
    """
    # Sanitize comic name to prevent directory traversal
    if '..' in comic_name or comic_name.startswith('/'):
        return "Invalid comic name", 400
    
    images = get_comic_images(comic_name)
    if not images:
        return "No images found for this comic", 404
    
    return render_template('comic.html', comic_name=comic_name, total_images=len(images))

@app.route('/api/comic/<comic_name>/images')
def api_comic_images(comic_name):
    """
    API endpoint to get comic images with pagination
    """
    # Sanitize comic name to prevent directory traversal
    if '..' in comic_name or comic_name.startswith('/'):
        return jsonify({'error': 'Invalid comic name'}), 400
    
    page = int(request.args.get('page', 1))
    images = get_comic_images(comic_name)
    
    if not images:
        return jsonify({'error': 'No images found'}), 404
    
    start_index = (page - 1) * IMAGES_PER_LOAD
    end_index = start_index + IMAGES_PER_LOAD
    
    # Slice images for current page
    images_slice = images[start_index:end_index]
    
    # Prepare image URLs
    image_urls = [f'/comic/{comic_name}/image/{img}' for img in images_slice]
    
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
    # Sanitize inputs to prevent directory traversal
    if '..' in comic_name or '..' in filename or comic_name.startswith('/') or filename.startswith('/'):
        return "Invalid path", 400
    
    comic_path = os.path.join(COMICS_DIR, comic_name)
    return send_from_directory(comic_path, filename)

# New route to serve comic cover images
@app.route('/comic/<comic_name>/cover')
def serve_comic_cover(comic_name):
    """
    Serve the cover image for a comic (first image in directory)
    """
    # Sanitize inputs to prevent directory traversal
    if '..' in comic_name or comic_name.startswith('/'):
        return "Invalid path", 400
    
    cover_image = get_comic_cover(comic_name)
    if not cover_image:
        # Return a default "no cover" image or 404
        return "No cover image found", 404
    
    comic_path = os.path.join(COMICS_DIR, comic_name)
    return send_from_directory(comic_path, cover_image)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)