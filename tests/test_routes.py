"""
Unit tests for the Comic Web application routes
"""

import unittest
import os
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from comics_app.routes import create_app

class TestRoutes(unittest.TestCase):
    """Test Flask routes"""
    
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
        
        # Create app with test configuration
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['COMICS_DIR'] = self.comics_dir
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        shutil.rmtree(self.test_dir)
    
    def test_index_route(self):
        """Test the index route"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test_comic', response.data)
    
    def test_comic_route(self):
        """Test the comic route"""
        response = self.client.get('/comic/test_comic')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test_comic', response.data)
    
    def test_comic_route_nonexistent(self):
        """Test the comic route with nonexistent comic"""
        response = self.client.get('/comic/nonexistent_comic')
        self.assertEqual(response.status_code, 404)
    
    def test_comic_route_unsafe_path(self):
        """Test the comic route with unsafe path"""
        response = self.client.get('/comic/../etc/passwd')
        self.assertEqual(response.status_code, 400)
    
    def test_comic_images_api(self):
        """Test the comic images API"""
        response = self.client.get('/api/comic/test_comic/images')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('images', data)
        self.assertIn('has_more', data)
        self.assertIn('total', data)
        
        # Check that we got the expected images
        filenames = [img['filename'] for img in data['images']]
        self.assertIn('001.jpg', filenames)
        self.assertIn('002.png', filenames)
        self.assertIn('003.gif', filenames)
    
    def test_comic_image_route(self):
        """Test the comic image route"""
        response = self.client.get('/comic/test_comic/image/001.jpg')
        self.assertEqual(response.status_code, 200)
    
    def test_comic_image_route_nonexistent(self):
        """Test the comic image route with nonexistent image"""
        response = self.client.get('/comic/test_comic/image/nonexistent.jpg')
        self.assertEqual(response.status_code, 404)
    
    def test_error_handlers(self):
        """Test error handlers"""
        # Test 404 error handler
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        # Test 500 error handler
        with patch('comics_app.routes.get_all_comics') as mock_get_all_comics:
            mock_get_all_comics.side_effect = Exception('Test error')
            response = self.client.get('/')
            self.assertEqual(response.status_code, 500)

if __name__ == '__main__':
    unittest.main()