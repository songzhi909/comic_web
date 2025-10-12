import os
import sys

class Config:
    # Configuration settings for the Comic Web application
    
    # Determine if we're running in a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        TEMPLATE_FOLDER = os.path.join(sys._MEIPASS, 'templates')
        STATIC_FOLDER = os.path.join(sys._MEIPASS, 'static')
        # Comics directory should always be alongside the executable
        EXE_DIR = os.path.dirname(sys.executable)
        COMICS_DIR = os.path.join(EXE_DIR, 'comics')
    else:
        # Running in development (Python interpreter)
        # Use absolute paths for templates and static folders
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
        STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
        # Comics directory is alongside the script file
        COMICS_DIR = os.path.join(BASE_DIR, 'comics')
    
    IMAGES_PER_LOAD = 20