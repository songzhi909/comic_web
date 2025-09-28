"""
Unit tests for the Comic Web application
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from comics_app.utils import is_path_safe, get_comic_images, get_comic_cover
from comics_app.cache import ImageCache

class TestUtils(unittest.TestCase):
    """Test utility functions"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.comics_dir = os.path.join(self.test_dir, 'comics')
        os.makedirs(self.comics_dir)
        
        # Create a test comic directory
        self.test_comic = os.path.join(self.comics_dir, 'test_comic')
        os.makedirs(self.test_comic)
        
        # Create some test images
        self.test_images = ['001.jpg', '002.png', '003.gif']
        for image in self.test_images:
            with open(os.path.join(self.test_comic, image), 'w') as f:
                f.write('fake image data')
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        shutil.rmtree(self.test_dir)
    
    def test_is_path_safe_valid(self):
        """Test is_path_safe with valid paths"""
        self.assertTrue(is_path_safe('test_comic'))
        self.assertTrue(is_path_safe('comic_with_underscore'))
        self.assertTrue(is_path_safe('comic-with-dash'))
    
    def test_is_path_safe_invalid(self):
        """Test is_path_safe with invalid paths"""
        self.assertFalse(is_path_safe('../test_comic'))
        self.assertFalse(is_path_safe('/test_comic'))
        self.assertFalse(is_path_safe('test:comic'))
        self.assertFalse(is_path_safe('test\\comic'))
    
    def test_get_comic_images(self):
        """Test get_comic_images function"""
        images = get_comic_images(self.comics_dir, 'test_comic')
        self.assertEqual(len(images), 3)
        self.assertIn('001.jpg', images)
        self.assertIn('002.png', images)
        self.assertIn('003.gif', images)
    
    def test_get_comic_cover(self):
        """Test get_comic_cover function"""
        cover = get_comic_cover(self.comics_dir, 'test_comic')
        self.assertEqual(cover, '001.jpg')  # Should be the first image alphabetically
    
    def test_get_comic_images_nonexistent(self):
        """Test get_comic_images with nonexistent comic"""
        images = get_comic_images(self.comics_dir, 'nonexistent_comic')
        self.assertEqual(images, [])

class TestImageCache(unittest.TestCase):
    """Test image caching functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.comics_dir = os.path.join(self.test_dir, 'comics')
        os.makedirs(self.comics_dir)
        
        # Create a test comic directory
        self.test_comic = os.path.join(self.comics_dir, 'test_comic')
        os.makedirs(self.test_comic)
        
        # Create a test image
        self.test_image = '001.jpg'
        with open(os.path.join(self.test_comic, self.test_image), 'w') as f:
            f.write('fake image data')
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        shutil.rmtree(self.test_dir)
    
    def test_image_cache_creation(self):
        """Test ImageCache creation"""
        cache = ImageCache()
        self.assertIsNotNone(cache)
        self.assertEqual(cache.max_size, 1000)
    
    def test_cache_image_info(self):
        """Test caching image information"""
        cache = ImageCache()
        info = {'width': 800, 'height': 600}
        cache.store_image_info('test_comic', self.test_image, info)
        
        # Retrieve cached info
        cached_info = cache.get_image_info('test_comic', self.test_image)
        self.assertEqual(cached_info['width'], 800)
        self.assertEqual(cached_info['height'], 600)
    
    def test_cache_cleanup(self):
        """Test cache cleanup when exceeding max size"""
        cache = ImageCache(max_size=2)
        
        # Add more items than cache can hold
        for i in range(5):
            info = {'width': 800 + i, 'height': 600 + i}
            cache.store_image_info('test_comic', f'image_{i}.jpg', info)
        
        # Cache should have been cleaned up
        self.assertLessEqual(len(cache.cache), 2)

if __name__ == '__main__':
    unittest.main()