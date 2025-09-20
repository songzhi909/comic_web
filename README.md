# Comic Web

A Python-based web application for displaying comic images from local directories with lazy loading functionality.

## Features

- Display comics from local directory structure
- Comic cover images (first image in each folder used as cover)
- Lazy loading of images (loads 20 images at a time)
- Responsive design
- Automatic image sorting
- Directory traversal protection

## Requirements

- Python 3.6+
- Flask
- Flask-Cors

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Directory Structure

The application expects comics to be organized in the following structure:

```
comic_web/
├── app.py
├── comics/
│   ├── comic_name_1/
│   │   ├── 001.jpg
│   │   ├── 002.jpg
│   │   └── ...
│   ├── comic_name_2/
│   │   ├── 001.png
│   │   ├── 002.png
│   │   └── ...
│   └── ...
└── ...
```

Create a `comics` directory in the root of the project and add your comics as subdirectories with image files.

The first image in each comic folder will be used as the cover image for that comic on the main page.

## Supported Image Formats

- PNG
- JPG/JPEG
- GIF
- BMP
- WEBP

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5000`

3. You will see a list of available comics with their cover images. Click on any comic to view it.

4. As you scroll down, additional images will be automatically loaded (lazy loading).

## Configuration

You can modify the lazy loading behavior by changing the `IMAGES_PER_LOAD` variable in [app.py](file:///d%3A/workspace/python/comic_web/app.py):

```python
IMAGES_PER_LOAD = 20  # Number of images to load at once
```

## How Lazy Loading Works

- Initially, only the first 20 images are loaded
- As you scroll down and approach the bottom of the page, additional batches of 20 images are loaded
- This continues until all images are loaded
- Uses native browser lazy loading (`loading="lazy"`) for additional performance

## Security

The application includes protection against directory traversal attacks to ensure that only files within the designated comics directory can be accessed.