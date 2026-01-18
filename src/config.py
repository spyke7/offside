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
# COLORS (R, G, B) - Modern Premium Palette
# ============================================================================
# Pitch colors
PITCH_GREEN = (30, 120, 50)
PITCH_DARK_GREEN = (20, 90, 35)
PITCH_LIGHT_GREEN = (45, 140, 65)
LINE_WHITE = (255, 255, 255)

# Background gradients (top, bottom)
BACKGROUND_DARK = (15, 15, 25)
BACKGROUND_GRADIENT_TOP = (25, 25, 45)
BACKGROUND_GRADIENT_BOTTOM = (10, 10, 20)

# Panel colors
PANEL_BG = (35, 38, 52)
PANEL_BG_LIGHT = (45, 48, 62)
SIDEBAR_BG = (25, 28, 40)

# Team colors (vibrant)
TEAM_A_COLOR = (255, 75, 85)      # Coral Red
TEAM_B_COLOR = (65, 135, 255)     # Electric Blue
BALL_COLOR = (255, 255, 255)

# UI Colors
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (170, 175, 185)
TEXT_DARK_GRAY = (100, 105, 115)
HIGHLIGHT_YELLOW = (255, 215, 0)
HIGHLIGHT_CYAN = (0, 220, 255)
SELECTED_RING = (255, 200, 50)

# Button colors
BUTTON_BG = (55, 60, 80)
BUTTON_HOVER = (75, 80, 110)
BUTTON_ACTIVE = (90, 95, 130)
BUTTON_SUCCESS = (45, 160, 90)
BUTTON_SUCCESS_HOVER = (55, 180, 105)
BUTTON_PRIMARY = (60, 120, 220)
BUTTON_PRIMARY_HOVER = (80, 140, 240)

# Dropdown colors
DROPDOWN_BG = (40, 45, 60)
DROPDOWN_HOVER = (55, 60, 80)
DROPDOWN_BORDER = (70, 75, 95)

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

# ============================================================================
# ML PREDICTION CONSTRAINTS
# Only these options are valid for ML prediction mode
# ============================================================================
ML_SUPPORTED = {
    "La Liga": {
        "seasons": ["2021/2022", "2022/2023", "2023/2024"],
        "teams": [
            "Real Madrid", "Barcelona", "Atletico Madrid",
            "Sevilla", "Real Betis", "Real Sociedad",
            "Villarreal", "Athletic Bilbao", "Valencia",
            "Osasuna", "Celta Vigo", "Rayo Vallecano",
            "Getafe", "Espanyol", "Mallorca", "Cadiz",
            "Girona", "Almeria", "Las Palmas", "Alaves"
        ]
    }
}

# Mode constants
MODE_REPLAY = "replay"
MODE_ML = "ml"