import os
import sys
import subprocess
import shutil

def build_executable():
    """
    Build the comic web application into an executable using PyInstaller
    """
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths
    app_path = os.path.join(current_dir, 'app.py')
    dist_dir = os.path.join(current_dir, 'dist')
    
    # Remove existing dist directory if it exists
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    # PyInstaller command - including both templates and comics directories
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name', 'ComicWeb',
        '--hidden-import', 'flask',
        '--hidden-import', 'flask_cors',
        '--add-data', 'templates;templates',
        app_path
    ]
    
    print("Building executable...")
    print("Command:", ' '.join(cmd))
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=current_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Build successful!")
            print("Executable created in dist/ComicWeb.exe")
            
            # Show the size of the executable
            exe_path = os.path.join(dist_dir, 'ComicWeb.exe')
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path)
                print(f"Executable size: {size / (1024*1024):.2f} MB")
                
            return True
        else:
            print("Build failed!")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"Error running PyInstaller: {e}")
        return False

if __name__ == "__main__":
    build_executable()