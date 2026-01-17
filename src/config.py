"""
Configuration file for the football match simulation.
Contains all constants, settings, and file paths.
"""

import os

# ============================================================================
# PROJECT PATHS
# ============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'matches')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# ============================================================================
# SCREEN SETTINGS
# ============================================================================
SCREEN_WIDTH = 1280      # Total window width
SCREEN_HEIGHT = 720      # Total window height
FPS = 60                 # Frames per second

# Layout
SIDEBAR_WIDTH = 300      # Left sidebar for menu
STATS_PANEL_WIDTH = 350  # Right sidebar for stats
PITCH_WIDTH_PX = SCREEN_WIDTH - SIDEBAR_WIDTH - STATS_PANEL_WIDTH  
PITCH_HEIGHT_PX = 600    # Pitch area height

PANEL_WIDTH = STATS_PANEL_WIDTH  # Alias for compatibility

# ============================================================================
# PITCH DIMENSIONS (StatsBomb coordinate system)
# ============================================================================
PITCH_LENGTH = 120       # Length in StatsBomb units
PITCH_WIDTH_STAT = 80    # Width in StatsBomb units (renamed from PITCH_WIDTH)

# ============================================================================
# COLORS (R, G, B)
# ============================================================================
PITCH_GREEN = (34, 139, 34)
PITCH_DARK_GREEN = (20, 100, 20)
LINE_WHITE = (255, 255, 255)
BACKGROUND_DARK = (18, 18, 20)
PANEL_BG = (40, 40, 50)
SIDEBAR_BG = (30, 30, 40)

# Team colors
TEAM_A_COLOR = (255, 50, 50)    # Red
TEAM_B_COLOR = (50, 100, 255)   # Blue
BALL_COLOR = (255, 255, 255)    # White

# UI Colors
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (180, 180, 180)
TEXT_DARK_GRAY = (120, 120, 120)
HIGHLIGHT_YELLOW = (255, 255, 0)
SELECTED_RING = (255, 215, 0)
BUTTON_BG = (60, 60, 70)
BUTTON_HOVER = (80, 80, 90)
DROPDOWN_BG = (50, 50, 60)

# ============================================================================
# GAME OBJECTS
# ============================================================================
PLAYER_RADIUS = 10
BALL_RADIUS = 5
PLAYER_NUMBER_SIZE = 14

# ============================================================================
# ANIMATION SETTINGS
# ============================================================================
ANIMATION_SPEED = 1.0
INTERPOLATION_STEPS = 30

# ============================================================================
# STATSBOMB DATA SETTINGS
# ============================================================================
STATSBOMB_REPO = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/"

# Competition mappings
COMPETITIONS = {
    "FIFA World Cup": {"id": 43, "seasons": {
        "2022": 106,
        "2018": 3
    }},
    "La Liga": {"id": 11, "seasons": {
        "2020/2021": 90,
        "2019/2020": 42
    }},
    "Premier League": {"id": 2, "seasons": {
        "2003/2004": 44
    }}
}

DEFAULT_COMPETITION_ID = 43
DEFAULT_SEASON_ID = 106
DEFAULT_MATCH_ID = 3869685  # World Cup 2022 Final

STATS_UPDATE_INTERVAL = 1.0