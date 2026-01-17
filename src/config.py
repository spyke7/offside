import os

# Screen Dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (34, 139, 34)  # Pitch Green
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MATCHES_DIR = os.path.join(DATA_DIR, 'matches')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')

# Data Configuration
SAMPLE_MATCH_ID = "match"  # Filename without extension
SAMPLE_MATCH_PATH = os.path.join(MATCHES_DIR, f"{SAMPLE_MATCH_ID}.json")
