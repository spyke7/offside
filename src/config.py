import os

# Screen Dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PANEL_WIDTH = 300
PITCH_WIDTH = SCREEN_WIDTH - PANEL_WIDTH
FPS = 60

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (34, 139, 34)  # Pitch Green
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_PANEL_BG = (50, 50, 50)
COLOR_TEXT_HEADER = (255, 255, 255)
COLOR_TEXT_BODY = (200, 200, 200)

# Team Colors
COLOR_TEAM_HOME = (0, 100, 255)  # Blue
COLOR_TEAM_AWAY = (255, 50, 50)  # Red

# Rendering Constants
PITCH_LENGTH = 120.0  # StatsBomb pitch length
PITCH_WIDTH_STAT = 80.0  # StatsBomb pitch width  
PITCH_WIDTH_PX = SCREEN_WIDTH - PANEL_WIDTH  # Pitch area width in pixels
PITCH_HEIGHT_PX = SCREEN_HEIGHT - 100  # Pitch area height in pixels (leave room for scoreboard)

# Colors for new renderer
PITCH_GREEN = (34, 139, 34)
LINE_WHITE = (255, 255, 255)
BACKGROUND_DARK = (20, 20, 25)
PANEL_BG = (40, 40, 45)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (180, 180, 180)
TEAM_A_COLOR = (0, 100, 255)  # Blue
TEAM_B_COLOR = (255, 50, 50)  # Red
SELECTED_RING = (255, 255, 0)
HIGHLIGHT_YELLOW = (255, 215, 0)
BALL_COLOR = (255, 255, 255)

# Player/Ball sizes
PLAYER_RADIUS = 12
BALL_RADIUS = 6

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MATCHES_DIR = os.path.join(DATA_DIR, 'matches')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')

# Data Configuration
SAMPLE_MATCH_ID = "match"  # Filename without extension
SAMPLE_MATCH_PATH = os.path.join(MATCHES_DIR, f"{SAMPLE_MATCH_ID}.json")

# StatsBomb API / Repo
STATSBOMB_REPO = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/"
DEFAULT_COMPETITION_ID = 43 # World Cup
DEFAULT_SEASON_ID = 3 # 2018
DEFAULT_MATCH_ID = 8658 # Belgium vs Japan
