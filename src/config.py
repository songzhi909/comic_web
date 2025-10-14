import os
import sys
import configparser

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
        # Config file location when running as executable - should be alongside the exe, not bundled
        CONFIG_FILE = os.path.join(EXE_DIR, 'comic_web.conf')
    else:
        # Running in development (Python interpreter)
        # Use absolute paths for templates and static folders
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
        STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
        # Comics directory is alongside the script file
        COMICS_DIR = os.path.join(BASE_DIR, 'comics')
        # Config file location when running in development
        CONFIG_FILE = os.path.join(BASE_DIR, 'comic_web.conf')
    
    IMAGES_PER_LOAD = 20
    
    # Read from config file
    config = configparser.ConfigParser()
    
    # Try to read the config file
    files_read = config.read(CONFIG_FILE)
    
    # If config file was not found, create a default one
    if not files_read:
        # Create a default config file if it doesn't exist
        # This is helpful for first-time users
        config_dict = {
            'app': {
                'enable_registration': 'false'
            },
            'logging': {
                'log_level': 'ERROR',
                'log_file_max_bytes': '10485760',
                'log_file_backup_count': '5',
                'log_enable_console': 'true',
                'log_enable_file': 'true'
            }
        }
        
        # Write default config to file
        os.makedirs(os.path.dirname(CONFIG_FILE) if os.path.dirname(CONFIG_FILE) else '.', exist_ok=True)
        config.read_dict(config_dict)
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print(f"Created default config file at {CONFIG_FILE}")
    
    # Registration settings
    ENABLE_REGISTRATION = config.getboolean('app', 'enable_registration', fallback=False)
    
    # Logging settings
    LOG_LEVEL = config.get('logging', 'log_level', fallback='ERROR')
    LOG_FILE_MAX_BYTES = config.getint('logging', 'log_file_max_bytes', fallback=10*1024*1024)
    LOG_FILE_BACKUP_COUNT = config.getint('logging', 'log_file_backup_count', fallback=5)
    LOG_ENABLE_CONSOLE = config.getboolean('logging', 'log_enable_console', fallback=True)
    LOG_ENABLE_FILE = config.getboolean('logging', 'log_enable_file', fallback=True)