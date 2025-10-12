"""
Database module for the Comic Web application
"""

import sqlite3
import os
import logging
import json
import hashlib
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

# Database file path
DB_FILE = os.path.join(Config.COMICS_DIR, 'comics.db')

def init_db():
    """Initialize the database with required tables"""
    try:
        with get_db_connection() as conn:
            # Create comics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS comics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    title TEXT,
                    author TEXT,
                    tags TEXT,
                    description TEXT,
                    cover_image TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create bookmarks table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comic_name TEXT UNIQUE NOT NULL,
                    comic_title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster searches
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_comics_name ON comics(name)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
            ''')
            
            # Insert default admin user if no users exist
            cursor = conn.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            if count == 0:
                # Create default admin user with password "admin"
                password_hash = hashlib.sha256("admin".encode()).hexdigest()
                conn.execute('''
                    INSERT INTO users (username, password_hash) VALUES (?, ?)
                ''', ("admin", password_hash))
                logger.info("Created default admin user with username 'admin' and password 'admin'")
            
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        # Ensure the comics directory exists
        os.makedirs(Config.COMICS_DIR, exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def get_comic_metadata(comic_name):
    """Get metadata for a specific comic from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                'SELECT title, author, tags, description, cover_image FROM comics WHERE name = ?',
                (comic_name,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'title': row['title'],
                    'author': row['author'],
                    'tags': row['tags'],
                    'description': row['description'],
                    'cover_image': row['cover_image']
                }
    except Exception as e:
        logger.error(f"Error getting metadata for {comic_name}: {str(e)}")
    return {}

def save_comic_metadata(comic_name, metadata):
    """Save or update comic metadata in database"""
    try:
        with get_db_connection() as conn:
            # Check if comic already exists
            cursor = conn.execute('SELECT id, cover_image FROM comics WHERE name = ?', (comic_name,))
            existing = cursor.fetchone()
            
            # If this is an update and no cover_image is provided in metadata, keep the existing one
            cover_image = metadata.get('cover_image')
            if existing and cover_image is None:
                cover_image = existing['cover_image']
            
            if existing:
                # Update existing comic
                conn.execute('''
                    UPDATE comics 
                    SET title = ?, author = ?, tags = ?, description = ?, cover_image = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                ''', (
                    metadata.get('title'),
                    metadata.get('author'),
                    ','.join(metadata.get('tags', [])) if isinstance(metadata.get('tags'), list) else metadata.get('tags'),
                    metadata.get('description'),
                    cover_image,  # Use the determined cover_image
                    comic_name
                ))
            else:
                # Insert new comic
                conn.execute('''
                    INSERT INTO comics (name, title, author, tags, description, cover_image)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    comic_name,
                    metadata.get('title'),
                    metadata.get('author'),
                    ','.join(metadata.get('tags', [])) if isinstance(metadata.get('tags'), list) else metadata.get('tags'),
                    metadata.get('description'),
                    cover_image
                ))
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error saving metadata for {comic_name}: {str(e)}")
        return False

def get_all_comics():
    """Get all comics from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT name, title, author, tags, description, cover_image 
                FROM comics 
                ORDER BY name
            ''')
            comics = []
            for row in cursor.fetchall():
                # Skip hidden comics (starting with dot)
                if row['name'].startswith('.'):
                    continue
                    
                # Handle tags - ensure it's always a list
                tags = row['tags']
                if isinstance(tags, str):
                    # Split string into list
                    tags = tags.split(',') if tags else []
                elif tags is None:
                    # If None, make it an empty list
                    tags = []
                elif not isinstance(tags, list):
                    # If it's something else, make it a list with one item
                    tags = [str(tags)]
                    
                comics.append({
                    'name': row['name'],
                    'title': row['title'],
                    'author': row['author'],
                    'tags': tags,
                    'description': row['description'],
                    'cover_image': row['cover_image']
                })
            return comics
    except Exception as e:
        logger.error(f"Error getting all comics: {str(e)}")
        return []

def save_bookmark(comic_name, comic_title):
    """Save a bookmark in database"""
    try:
        with get_db_connection() as conn:
            # Check if bookmark already exists
            cursor = conn.execute('SELECT id FROM bookmarks WHERE comic_name = ?', (comic_name,))
            existing = cursor.fetchone()
            
            if not existing:
                # Insert new bookmark
                conn.execute('''
                    INSERT INTO bookmarks (comic_name, comic_title)
                    VALUES (?, ?)
                ''', (comic_name, comic_title))
                conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error saving bookmark for {comic_name}: {str(e)}")
        return False

def remove_bookmark(comic_name):
    """Remove a bookmark from database"""
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM bookmarks WHERE comic_name = ?', (comic_name,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error removing bookmark for {comic_name}: {str(e)}")
        return False

def get_bookmarks():
    """Get all bookmarks from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT comic_name, comic_title, created_at 
                FROM bookmarks 
                ORDER BY created_at DESC
            ''')
            bookmarks = {}
            for row in cursor.fetchall():
                bookmarks[row['comic_name']] = {
                    'title': row['comic_title'],
                    'timestamp': row['created_at']
                }
            return bookmarks
    except Exception as e:
        logger.error(f"Error getting bookmarks: {str(e)}")
        return {}

def sync_comics_with_db():
    """Sync comics directory with database"""
    try:
        # Get all comics from directory
        if not os.path.exists(Config.COMICS_DIR):
            logger.warning("Comics directory does not exist")
            return []
            
        comic_dirs = []
        for item in os.listdir(Config.COMICS_DIR):
            # Skip hidden directories (starting with dot)
            if item.startswith('.'):
                logger.debug(f"Skipping hidden directory: {item}")
                continue
                
            item_path = os.path.join(Config.COMICS_DIR, item)
            if os.path.isdir(item_path):
                comic_dirs.append(item)
        
        # Get all comics from database
        db_comics = get_all_comics()
        db_comic_names = [comic['name'] for comic in db_comics]
        
        # Find new comics that need to be added to database
        new_comics = [name for name in comic_dirs if name not in db_comic_names]
        
        # Add new comics to database
        for comic_name in new_comics:
            # Load existing metadata if it exists
            metadata_path = os.path.join(Config.COMICS_DIR, comic_name, "metadata.json")
            metadata = {}
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading metadata for {comic_name}: {str(e)}")
            
            # Get cover image only for new comics
            from comics_app.utils import get_comic_cover
            cover_image = get_comic_cover(Config.COMICS_DIR, comic_name)
            
            # Update metadata with cover image
            metadata['cover_image'] = cover_image
            
            # Save to database
            save_comic_metadata(comic_name, metadata)
            
            # Remove old metadata file if it exists
            if os.path.exists(metadata_path):
                try:
                    os.remove(metadata_path)
                except Exception as e:
                    logger.warning(f"Could not remove old metadata file for {comic_name}: {str(e)}")
        
        # Update existing comics without changing their cover images
        existing_comics = [name for name in comic_dirs if name in db_comic_names]
        for comic_name in existing_comics:
            # Only resync metadata from file if it exists, but don't change cover image
            metadata_path = os.path.join(Config.COMICS_DIR, comic_name, "metadata.json")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        # Explicitly set cover_image to None so it doesn't overwrite existing one
                        metadata['cover_image'] = None
                        save_comic_metadata(comic_name, metadata)
                        
                    # Remove old metadata file
                    try:
                        os.remove(metadata_path)
                    except Exception as e:
                        logger.warning(f"Could not remove old metadata file for {comic_name}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error loading metadata for {comic_name}: {str(e)}")
        
        logger.info(f"Synced comics with database. Added {len(new_comics)} new comics.")
        return new_comics
    except Exception as e:
        logger.error(f"Error syncing comics with database: {str(e)}")
        return []

def get_user_by_username(username):
    """Get user by username"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT id, username, password_hash FROM users WHERE username = ?
            ''', (username,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'password_hash': row[2]
                }
            return None
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None

def create_user(username, password):
    """Create a new user"""
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO users (username, password_hash) VALUES (?, ?)
            ''', (username, password_hash))
            conn.commit()
            logger.info(f"Created user: {username}")
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"User already exists: {username}")
        return False
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False

def verify_user_password(username, password):
    """Verify user password"""
    try:
        user = get_user_by_username(username)
        if not user:
            return False
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return user['password_hash'] == password_hash
    except Exception as e:
        logger.error(f"Error verifying user password: {e}")
        return False
