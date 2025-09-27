"""
Utility functions for the Comic Web application
"""

import os
import logging

# Supported image extensions
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')

logger = logging.getLogger(__name__)

def get_comic_images(comics_dir, comic_name):
    """
    Get all image files from a comic directory
    
    Args:
        comics_dir (str): Path to the comics directory
        comic_name (str): Name of the comic
        
    Returns:
        list: List of image filenames
    """
    comic_path = os.path.join(comics_dir, comic_name)
    if not os.path.exists(comic_path):
        logger.warning(f"Comic path does not exist: {comic_path}")
        return []
    
    images = []
    
    try:
        for filename in sorted(os.listdir(comic_path)):
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                images.append(filename)
        logger.info(f"Found {len(images)} images in comic: {comic_name}")
    except Exception as e:
        logger.error(f"Error reading comic directory {comic_name}: {str(e)}")
        return []
    
    return images

def get_comic_cover(comics_dir, comic_name):
    """
    Get the cover image for a comic (first image in the directory)
    
    Args:
        comics_dir (str): Path to the comics directory
        comic_name (str): Name of the comic
        
    Returns:
        str or None: Filename of the cover image or None if not found
    """
    images = get_comic_images(comics_dir, comic_name)
    if images:
        logger.info(f"Cover image for {comic_name}: {images[0]}")
        return images[0]
    logger.warning(f"No cover image found for comic: {comic_name}")
    return None

def is_path_safe(path_segment):
    """
    Check if a path segment is safe (no directory traversal attempts)
    
    Args:
        path_segment (str): Path segment to check
        
    Returns:
        bool: True if path is safe, False otherwise
    """
    return '..' not in path_segment and not path_segment.startswith('/')