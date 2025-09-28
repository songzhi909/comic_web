"""
Utility functions for the Comic Web application
"""

import os
import logging
from PIL import Image

from config import Config
from comics_app.cache import get_cached_image_size, cache_image_size

logger = logging.getLogger(__name__)

def is_path_safe(path):
    """Check if a path is safe to use (no directory traversal)"""
    # Basic security check to prevent directory traversal
    if '..' in path or path.startswith('/'):
        return False
    
    # Allow colon only if it's part of a drive letter on Windows (e.g., C:)
    if ':' in path and not (len(path) > 1 and path[1] == ':' and path[0].isalpha() and len(path.split(':')) == 2):
        return False
    
    # Check for directory separators that could indicate traversal attempts
    if '\\' in path or '/' in path:
        return False
    
    # Use secure_filename as an additional check but be more permissive with Unicode
    from werkzeug.utils import secure_filename
    secured = secure_filename(path)
    
    # If secured filename is empty, it might be because of Unicode characters
    # In that case, we do a more manual check
    if not secured:
        # Check each character for potentially unsafe characters
        unsafe_chars = ['<', '>', '*', '?', '|', '"']
        for char in unsafe_chars:
            if char in path:
                return False
        return True
    
    # If secured version is very different, it might be over-cleaning Unicode names
    # Allow if the original path is not drastically reduced and doesn't contain unsafe patterns
    if len(secured) < len(path) // 2:
        # But still check for unsafe characters
        unsafe_chars = ['<', '>', '*', '?', '|', '"']
        for char in unsafe_chars:
            if char in path:
                return False
        return True
        
    return True

def get_comic_images(comics_dir, comic_name):
    """Get all image files from a comic directory"""
    try:
        comic_path = os.path.join(comics_dir, comic_name)
        logger.debug(f"Looking for comic at path: {comic_path}")
        if not os.path.exists(comic_path):
            logger.warning(f"Comic path does not exist: {comic_path}")
            return []
        
        # Supported image extensions
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
        images = []
        
        try:
            for filename in sorted(os.listdir(comic_path)):
                if filename.lower().endswith(image_extensions):
                    images.append(filename)
            logger.info(f"Found {len(images)} images in comic: {comic_name}")
        except Exception as e:
            logger.error(f"Error reading comic directory {comic_name}: {str(e)}")
            return []
        
        return images
    except Exception as e:
        logger.error(f"Error in get_comic_images for {comic_name}: {str(e)}", exc_info=True)
        return []

def get_comic_cover(comics_dir, comic_name):
    """Get the cover image for a comic (first image in the directory)"""
    try:
        images = get_comic_images(comics_dir, comic_name)
        if images:
            logger.info(f"Cover image for {comic_name}: {images[0]}")
            return images[0]
        logger.warning(f"No cover image found for comic: {comic_name}")
        return None
    except Exception as e:
        logger.error(f"Error getting cover image for {comic_name}: {e}", exc_info=True)
        return None

def get_image_size(comics_dir, comic_name, filename):
    """
    Get image dimensions with caching to improve performance
    """
    # Try to get from cache first
    width, height = get_cached_image_size(comic_name, filename)
    if width is not None and height is not None:
        return width, height
    
    # If not in cache, calculate and store
    try:
        image_path = os.path.join(comics_dir, comic_name, filename)
        with Image.open(image_path) as img:
            width, height = img.size
            # Cache the result
            cache_image_size(comic_name, filename, width, height)
            return width, height
    except Exception as e:
        logger.warning(f"Could not get image size for {comic_name}/{filename}: {e}")
        return None, None

def search_comics(comics_dir, query):
    """
    Search for comics by name or metadata
    
    Args:
        comics_dir (str): Path to the comics directory
        query (str): Search query
        
    Returns:
        list: List of comic names that match the query
    """
    # This function would be better placed in routes.py with access to metadata
    # For now, we'll implement basic name-based search
    matching_comics = []
    
    if not os.path.exists(comics_dir):
        return matching_comics
    
    try:
        for item in os.listdir(comics_dir):
            item_path = os.path.join(comics_dir, item)
            if os.path.isdir(item_path) and query.lower() in item.lower():
                matching_comics.append(item)
    except Exception as e:
        logger.error(f"Error searching comics: {str(e)}")
    
    return matching_comics
