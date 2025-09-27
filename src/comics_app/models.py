"""
Data models for the Comic Web application
"""

class Comic:
    """
    Represents a comic in the system
    """
    def __init__(self, name, cover_image=None):
        self.name = name
        self.cover_image = cover_image

class ComicImage:
    """
    Represents an image in a comic
    """
    def __init__(self, filename, path):
        self.filename = filename
        self.path = path