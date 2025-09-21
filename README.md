# Comic Web

Comic Web is a simple Flask application that allows you to browse comic images stored locally on your computer through a web browser. It supports lazy loading and responsive design, making it suitable for personal local use.

## Features

- Automatically scans the `comics/` directory for comic folders
- Displays a list of comics with cover images
- Shows comics with a clean reading interface
- Lazy loading of images (loads 20 images at a time as you scroll)
- Supports common image formats (JPG, PNG, GIF, BMP, WEBP)

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `comics/` directory in the project folder
4. Add your comics as subdirectories in the `comics/` folder (each comic should be in its own folder with the images inside)

## Usage

Run the application:
```
python app.py
```

Then open your browser and go to `http://localhost:5000` to view your comics.

## Building Executable

To build the application as a standalone executable:

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```

2. Run the build script:
   ```
   python build_exe.py
   ```

This will create a single executable file in the `dist/` directory that you can run without needing Python installed.

Alternatively, you can use PyInstaller directly:
```
pyinstaller --onefile --windowed --add-data "templates;templates" --add-data "comics;comics" app.py
```

Note: When you distribute the executable, you should also include the `comics/` directory with your comic files.

## Security

The application includes protection against directory traversal attacks to ensure that only files within the `comics/` directory can be accessed.