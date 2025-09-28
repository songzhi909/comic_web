"""
Image caching module for the Comic Web application
"""

import os
import time
import logging
import hashlib
from functools import lru_cache
from config import Config

logger = logging.getLogger(__name__)

class ImageCache:
    """Simple image caching mechanism to improve performance"""
    
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
        self.cache_dir = os.path.join(Config.COMICS_DIR, '.cache')
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
        except Exception as e:
            logger.warning(f"Could not create cache directory: {e}")
    
    def _get_cache_key(self, comic_name, filename):
        """Generate a cache key for a comic image"""
        return f"{comic_name}:{filename}"
    
    def _get_file_hash(self, filepath):
        """Get file hash for cache validation"""
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Could not generate hash for {filepath}: {e}")
            return None
    
    def get_image_info(self, comic_name, filename):
        """Get cached image information if available"""
        cache_key = self._get_cache_key(comic_name, filename)
        
        # Check memory cache first
        if cache_key in self.cache:
            self.access_times[cache_key] = time.time()
            return self.cache[cache_key]
        
        # Check file-based cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.info")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    import json
                    info = json.load(f)
                    
                    # Validate file hasn't changed
                    image_path = os.path.join(Config.COMICS_DIR, comic_name, filename)
                    if os.path.exists(image_path):
                        current_hash = self._get_file_hash(image_path)
                        if current_hash == info.get('hash'):
                            # Update access time
                            self.access_times[cache_key] = time.time()
                            self.cache[cache_key] = info
                            return info
            except Exception as e:
                logger.warning(f"Error reading cache file {cache_file}: {e}")
        
        return None
    
    def store_image_info(self, comic_name, filename, info):
        """Store image information in cache"""
        cache_key = self._get_cache_key(comic_name, filename)
        
        # Store in memory cache
        self.cache[cache_key] = info
        self.access_times[cache_key] = time.time()
        
        # Store in file cache
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.info")
            # Add file hash for validation
            image_path = os.path.join(Config.COMICS_DIR, comic_name, filename)
            if os.path.exists(image_path):
                info['hash'] = self._get_file_hash(image_path)
            
            with open(cache_file, 'w') as f:
                import json
                json.dump(info, f)
        except Exception as e:
            logger.warning(f"Could not store cache for {comic_name}/{filename}: {e}")
        
        # Clean up cache if it's too large
        self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove old cache entries if cache is too large"""
        if len(self.cache) > self.max_size:
            # Sort by access time and remove oldest entries
            sorted_items = sorted(self.access_times.items(), key=lambda x: x[1])
            items_to_remove = len(self.cache) - self.max_size // 2  # Remove half
            
            for i in range(items_to_remove):
                if sorted_items:
                    cache_key, _ = sorted_items.pop(0)
                    self.cache.pop(cache_key, None)
                    self.access_times.pop(cache_key, None)
                    
                    # Remove file cache
                    cache_file = os.path.join(self.cache_dir, f"{cache_key}.info")
                    if os.path.exists(cache_file):
                        try:
                            os.remove(cache_file)
                        except Exception as e:
                            logger.warning(f"Could not remove cache file {cache_file}: {e}")

# Global image cache instance
image_cache = ImageCache()

def get_cached_image_size(comic_name, filename):
    """Get cached image size information"""
    info = image_cache.get_image_info(comic_name, filename)
    if info and 'width' in info and 'height' in info:
        return info['width'], info['height']
    return None, None

def cache_image_size(comic_name, filename, width, height):
    """Cache image size information"""
    info = {
        'width': width,
        'height': height,
        'cached_at': time.time()
    }
    image_cache.store_image_info(comic_name, filename, info)