"""
Configuration file for the football match simulation.
Contains all constants, settings, and file paths.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'matches')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# SCREEN SETTINGS
SCREEN_WIDTH = 1600  
SCREEN_HEIGHT = 900    
FPS = 60               

# Stats panel 
PITCH_WIDTH_PX = 1200    # Pygame pitch area width
PITCH_HEIGHT_PX = 800    # Pygame pitch area height
STATS_PANEL_WIDTH = 400  # Right sidebar width

# PITCH DIMENSIONS (StatsBomb coordinate system)
PITCH_LENGTH = 120       
PITCH_WIDTH = 80        

PITCH_GREEN = (34, 139, 34)
PITCH_DARK_GREEN = (20, 100, 20)
LINE_WHITE = (255, 255, 255)
BACKGROUND_DARK = (20, 20, 30)
PANEL_BG = (40, 40, 50)

# Team colors
TEAM_A_COLOR = (255, 0, 0)      
TEAM_B_COLOR = (0, 0, 255)   
BALL_COLOR = (255, 255, 255)    

# UI Colors
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (180, 180, 180)
HIGHLIGHT_YELLOW = (255, 255, 0)
SELECTED_RING = (255, 215, 0)  

# GAME OBJECTS
PLAYER_RADIUS = 12       # Player circle radius in pixels
BALL_RADIUS = 6          # Ball circle radius in pixels
PLAYER_NUMBER_SIZE = 16  # Font size for player numbers

# ANIMATION SETTINGS
ANIMATION_SPEED = 1.0    # Multiplier for animation speed (1.0 = real-time)
INTERPOLATION_STEPS = 30 # Frames to interpolate

STATSBOMB_REPO = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/"

# Default match to load (La Liga: Barcelona vs Real Madrid)
DEFAULT_COMPETITION_ID = 11  # La Liga
DEFAULT_SEASON_ID = 90        # 2020/2021
DEFAULT_MATCH_ID = 3788741    # Example match

# STATS TRACKING
STATS_UPDATE_INTERVAL = 1.0 
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
