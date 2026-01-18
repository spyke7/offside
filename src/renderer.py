"""
Renderer Module - Complete UI System
Handles menu, match simulation, and stats display
"""

import os
import pygame
from typing import Optional, Tuple, Dict, List
from enum import Enum

from src.config import *
from src.game_engine import GameState

# Import ML constraints if available
try:
    from src.config import ML_SUPPORTED, MODE_REPLAY, MODE_ML
except ImportError:
    ML_SUPPORTED = {}
    MODE_REPLAY = "replay"
    MODE_ML = "ml"


class UIState(Enum):
    """Application UI states."""
    MENU = "menu"
    SIMULATION = "simulation"
    ML_SIMULATION = "ml_simulation"


class Button:
    """Enhanced button class with rounded corners and visual effects."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font, 
                 color=None, hover_color=None, text_color=None, border_radius=8):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
        self.border_radius = border_radius
        
        # Custom colors with defaults
        self.color = color or BUTTON_BG
        self.hover_color = hover_color or BUTTON_HOVER
        self.text_color = text_color or TEXT_WHITE
    
    def draw(self, screen, active=False):
        """Draw the button with rounded corners and effects."""
        # Determine background color
        if active:
            bg_color = BUTTON_ACTIVE if hasattr(self, 'active_color') is False else self.active_color
        elif self.hovered:
            bg_color = self.hover_color
        else:
            bg_color = self.color
        
        # Draw shadow (offset rectangle)
        shadow_rect = self.rect.move(2, 2)
        shadow_color = (15, 15, 20)
        pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=self.border_radius)
        
        # Draw main button
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=self.border_radius)
        
        # Draw subtle border
        border_color = tuple(min(255, c + 30) for c in bg_color)
        pygame.draw.rect(screen, border_color, self.rect, width=1, border_radius=self.border_radius)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event) -> bool:
        """Handle mouse events. Returns True if clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class Dropdown:
    """Dropdown menu class."""
    
    def __init__(self, x: int, y: int, width: int, height: int, options: List[str], font, default_text: str = "Select..."):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.font = font
        self.default_text = default_text
        self.selected_index = -1
        self.is_open = False
        self.hovered_option = -1
        self.enabled = True 
        self.scroll_offset = 0
        self.max_visible = 6  # Reduced to fit screen better with teams
    
    @property
    def selected(self) -> Optional[str]:
        """Get selected option."""
        if self.selected_index >= 0 and self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None
    
    def draw(self, screen):
        """Draw the dropdown with modern styling."""
        # Determine if disabled
        is_disabled = not self.options or not self.enabled
        border_radius = 6
        
        # Main button
        if is_disabled:
            color = (25, 28, 35)  # Darker when disabled
            border_color = (40, 42, 50)
        elif self.is_open:
            color = BUTTON_HOVER
            border_color = HIGHLIGHT_YELLOW
        else:
            color = DROPDOWN_BG
            border_color = DROPDOWN_BORDER if hasattr(__import__('src.config', fromlist=['DROPDOWN_BORDER']), 'DROPDOWN_BORDER') else (70, 75, 95)
        
        # Draw shadow
        shadow_rect = self.rect.move(2, 2)
        pygame.draw.rect(screen, (15, 15, 20), shadow_rect, border_radius=border_radius)
        
        # Draw main dropdown button
        pygame.draw.rect(screen, color, self.rect, border_radius=border_radius)
        pygame.draw.rect(screen, border_color if not is_disabled else (40, 42, 50), self.rect, 1, border_radius=border_radius)
        
        # Text
        text = self.selected or self.default_text
        text_color = TEXT_DARK_GRAY if is_disabled else TEXT_WHITE
        text_surface = self.font.render(text, True, text_color)
        screen.blit(text_surface, (self.rect.x + 12, self.rect.y + 11))
        
        # Arrow with highlight
        if not is_disabled:
            arrow = "▼" if not self.is_open else "▲"
            arrow_color = HIGHLIGHT_YELLOW if self.is_open else TEXT_GRAY
            arrow_surface = self.font.render(arrow, True, arrow_color)
            screen.blit(arrow_surface, (self.rect.right - 26, self.rect.y + 11))
        
        # Options (if open)
        if self.is_open and self.options:
            visible_options = self.options[self.scroll_offset : self.scroll_offset + self.max_visible]
            
            # Draw dropdown container shadow
            container_height = len(visible_options) * self.rect.height
            container_rect = pygame.Rect(self.rect.x, self.rect.bottom + 2, self.rect.width, container_height)
            shadow_container = container_rect.move(2, 2)
            pygame.draw.rect(screen, (10, 10, 15), shadow_container, border_radius=6)
            pygame.draw.rect(screen, DROPDOWN_BG, container_rect, border_radius=6)
            pygame.draw.rect(screen, border_color, container_rect, 1, border_radius=6)
            
            for i, option in enumerate(visible_options):
                # Calculate rect relative to scroll window
                option_rect = pygame.Rect(
                    self.rect.x + 4,
                    self.rect.bottom + 4 + i * (self.rect.height - 2),
                    self.rect.width - 8,
                    self.rect.height - 4
                )
                
                # Background based on state
                option_index = self.scroll_offset + i
                if option_index == self.hovered_option:
                    pygame.draw.rect(screen, BUTTON_HOVER, option_rect, border_radius=4)
                elif option_index == self.selected_index:
                    pygame.draw.rect(screen, (50, 55, 75), option_rect, border_radius=4)
                
                # Text (truncate if too long)
                option_text = option if len(option) < 22 else option[:19] + "..."
                text_col = HIGHLIGHT_YELLOW if option_index == self.selected_index else TEXT_WHITE
                option_surface = self.font.render(option_text, True, text_col)
                screen.blit(option_surface, (option_rect.x + 8, option_rect.y + 6))
            
            # Scroll indicator (modern pill style)
            if len(self.options) > self.max_visible:
                track_height = container_height - 8
                bar_height = max(20, track_height * (self.max_visible / len(self.options)))
                scroll_ratio = self.scroll_offset / max(1, (len(self.options) - self.max_visible))
                bar_y = self.rect.bottom + 6 + scroll_ratio * (track_height - bar_height)
                
                scrollbar_rect = pygame.Rect(self.rect.right - 8, bar_y, 4, bar_height)
                pygame.draw.rect(screen, (80, 85, 100), scrollbar_rect, border_radius=2)
    
    def handle_event(self, event) -> bool:
        """Handle events. Returns True if selection changed."""
        # Don't handle events if disabled
        if not self.options or not self.enabled:
            return False
        
        if event.type == pygame.MOUSEWHEEL and self.is_open:
            self.scroll_offset -= event.y
            self.scroll_offset = max(0, min(self.scroll_offset, len(self.options) - self.max_visible))
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check main button
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return False
            
            # Check options
            if self.is_open:
                # Calculate visible area rect
                visible_height = min(len(self.options), self.max_visible) * self.rect.height
                dropdown_area = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, visible_height)
                
                if dropdown_area.collidepoint(event.pos):
                    # Find which index was clicked
                    relative_y = event.pos[1] - self.rect.bottom
                    click_index = int(relative_y // self.rect.height)
                    actual_index = self.scroll_offset + click_index
                    
                    if 0 <= actual_index < len(self.options):
                        self.selected_index = actual_index
                        self.is_open = False
                        return True
                
                # Clicked outside - close
                self.is_open = False
        
        elif event.type == pygame.MOUSEMOTION and self.is_open:
             # Calculate visible area rect
            visible_height = min(len(self.options), self.max_visible) * self.rect.height
            dropdown_area = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, visible_height)
            
            if dropdown_area.collidepoint(event.pos):
                relative_y = event.pos[1] - self.rect.bottom
                hover_index = int(relative_y // self.rect.height)
                self.hovered_option = self.scroll_offset + hover_index
            else:
                self.hovered_option = -1
        
        return False


class SeekBar:
    """Interactive seek bar for timeline control."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.hovered = False
        self.dragging = False
    
    def draw(self, screen, progress: float):
        """Draw seek bar with current progress (0.0 to 1.0)."""
        # Background track
        pygame.draw.rect(screen, (40, 40, 50), self.rect, border_radius=4)
        pygame.draw.rect(screen, TEXT_GRAY, self.rect, 1, border_radius=4)
        
        # Progress fill
        fill_width = int(self.rect.width * progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(screen, HIGHLIGHT_YELLOW, fill_rect, border_radius=4)
            
        # Handle knob (circle at end of progress)
        knob_x = self.rect.x + fill_width
        pygame.draw.circle(screen, TEXT_WHITE, (knob_x, self.rect.centery), 8)
        if self.hovered or self.dragging:
            pygame.draw.circle(screen, SELECTED_RING, (knob_x, self.rect.centery), 10, 2)

    def handle_event(self, event) -> Optional[float]:
        """
        Handle mouse events. Returns new progress (0.0-1.0) if changed, else None.
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos) or self.rect.inflate(10, 10).collidepoint(event.pos)
            if self.dragging:
                # Clamp x to bar range
                x = max(self.rect.left, min(event.pos[0], self.rect.right))
                return (x - self.rect.left) / self.rect.width
                
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(10, 15).collidepoint(event.pos):
                self.dragging = True
                x = max(self.rect.left, min(event.pos[0], self.rect.right))
                return (x - self.rect.left) / self.rect.width
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            
        return None


class PitchRenderer:
    """Renders the football pitch."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        self.texture = None
        
        # Try loading texture
        if os.path.exists("assets/pitch_texture.png"):
            try:
                self.texture = pygame.image.load("assets/pitch_texture.png")
                self.texture = pygame.transform.scale(self.texture, (width, height))
            except Exception as e:
                print(f"Could not load pitch texture: {e}")
                
        self._draw_pitch()
    
    def _draw_pitch(self):
        """Draw the pitch with all markings."""
        # Use texture if available
        if self.texture:
            self.surface.blit(self.texture, (0, 0))
            return

        self.surface.fill(PITCH_GREEN)
        
        padding = 30
        pitch_x = padding
        pitch_y = padding
        pitch_w = self.width - 2 * padding
        pitch_h = self.height - 2 * padding
        
        # Draw grass stripes
        self.surface.fill(PITCH_GREEN)
        num_stripes = 12
        stripe_width = pitch_w / num_stripes
        for i in range(num_stripes):
            if i % 2 == 1:
                stripe_rect = (pitch_x + i * stripe_width, pitch_y, stripe_width, pitch_h)
                pygame.draw.rect(self.surface, PITCH_DARK_GREEN, stripe_rect)
        
        # Outer boundary
        pygame.draw.rect(self.surface, LINE_WHITE, (pitch_x, pitch_y, pitch_w, pitch_h), 3)
        
        # Center line
        center_x = pitch_x + pitch_w // 2
        pygame.draw.line(self.surface, LINE_WHITE, (center_x, pitch_y), (center_x, pitch_y + pitch_h), 3)
        
        # Center circle
        center_y = pitch_y + pitch_h // 2
        pygame.draw.circle(self.surface, LINE_WHITE, (center_x, center_y), int(pitch_h * 0.15), 3)
        pygame.draw.circle(self.surface, LINE_WHITE, (center_x, center_y), 4)
        
        # Penalty areas
        penalty_w = pitch_w * 0.15
        penalty_h = pitch_h * 0.5
        
        left_penalty_y = center_y - penalty_h // 2
        pygame.draw.rect(self.surface, LINE_WHITE, (pitch_x, left_penalty_y, penalty_w, penalty_h), 3)
        
        right_penalty_x = pitch_x + pitch_w - penalty_w
        pygame.draw.rect(self.surface, LINE_WHITE, (right_penalty_x, left_penalty_y, penalty_w, penalty_h), 3)
        
        # Goal areas
        goal_w = pitch_w * 0.07
        goal_h = pitch_h * 0.25
        
        left_goal_y = center_y - goal_h // 2
        pygame.draw.rect(self.surface, LINE_WHITE, (pitch_x, left_goal_y, goal_w, goal_h), 3)
        
        right_goal_x = pitch_x + pitch_w - goal_w
        pygame.draw.rect(self.surface, LINE_WHITE, (right_goal_x, left_goal_y, goal_w, goal_h), 3)
        
        # Penalty spots
        penalty_spot_x_left = pitch_x + penalty_w // 2
        penalty_spot_x_right = pitch_x + pitch_w - penalty_w // 2
        pygame.draw.circle(self.surface, LINE_WHITE, (penalty_spot_x_left, center_y), 4)
        pygame.draw.circle(self.surface, LINE_WHITE, (penalty_spot_x_right, center_y), 4)
    
    def get_surface(self):
        return self.surface
    
    def statsbomb_to_pixels(self, x: float, y: float) -> Tuple[int, int]:
        """Convert StatsBomb coordinates to pixels."""
        padding = 30
        pixel_x = padding + (x / PITCH_LENGTH) * (self.width - 2 * padding)
        pixel_y = padding + (y / PITCH_WIDTH_STAT) * (self.height - 2 * padding)
        return (int(pixel_x), int(pixel_y))


class Renderer:
    """Main renderer handling all UI states."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.state = UIState.MENU
        
        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.Font(None, 56)
        self.font_large = pygame.font.Font(None, 40)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Menu UI
        self.competition_dropdown = None
        self.team_a_dropdown = None
        self.team_b_dropdown = None
        self.team_b_dropdown = None
        self.season_dropdown = None
        self.start_button = None
        
        # ML Simulation state (initialized before _init_menu_ui)
        self.ml_result = None
        self.ml_button = None
        self.ml_back_button = None
        self.ml_resim_button = None
        
        # Mode-first UI: track which mode user selected
        self.menu_mode = None  # None, MODE_REPLAY, or MODE_ML
        self.mode_replay_button = None
        self.mode_ml_button = None
        
        self._init_menu_ui()
        
        # Simulation state
        self.pitch = None
        self.selected_player_id = None
        self.player_info = {}
        self.team_a_name = ""
        self.team_b_name = ""
        
        # Simulation UI Controls
        self.btn_play_pause = None
        self.btn_speed_1x = None
        self.btn_speed_2x = None
        self.btn_speed_4x = None
        self.seek_bar = None
    
    def _init_simulation_ui(self):
        """Initialize controls for simulation view."""
        # Bottom control bar area
        bar_y = SCREEN_HEIGHT - 80
        
        # Play/Pause button
        self.btn_play_pause = Button(
            SIDEBAR_WIDTH + 20, bar_y + 15, 80, 40, "Pause", self.font_medium
        )
        
        # Speed buttons
        self.btn_speed_1x = Button(
            SIDEBAR_WIDTH + 140, bar_y + 15, 40, 40, "1x", self.font_small
        )
        self.btn_speed_2x = Button(
            SIDEBAR_WIDTH + 190, bar_y + 15, 40, 40, "2x", self.font_small
        )
        self.btn_speed_4x = Button(
            SIDEBAR_WIDTH + 240, bar_y + 15, 40, 40, "4x", self.font_small
        )
        
        # Seek bar
        # Adjusted layout to fit time labels:
        # Buttons end at ~SIDEBAR + 280
        # Text needs ~60px
        # So seek bar starts at SIDEBAR + 360
        seek_x = SIDEBAR_WIDTH + 360
        seek_w = PITCH_WIDTH_PX - 440 # Leaves ~80px on right for total time
        self.seek_bar = SeekBar(seek_x, bar_y + 25, seek_w, 20)
        
    
    def _init_menu_ui(self):
        """Initialize menu UI elements with mode-first design."""
        # ================================================================
        # MODE SELECTION BUTTONS (Primary - shown first)
        # ================================================================
        self.mode_replay_button = Button(
            20, 100, 260, 55, "Replay Match", self.font_medium,
            color=BUTTON_SUCCESS, hover_color=BUTTON_SUCCESS_HOVER
        )
        
        self.mode_ml_button = Button(
            20, 170, 260, 55, "ML Prediction", self.font_medium,
            color=BUTTON_PRIMARY, hover_color=BUTTON_PRIMARY_HOVER
        )
        
        # ================================================================
        # REPLAY MODE CONTROLS
        # ================================================================
        # Competition dropdown - all StatsBomb supported
        competitions = list(COMPETITIONS.keys())
        self.competition_dropdown = Dropdown(
            20, 260, 260, 40, competitions, self.font_small, "Select Competition"
        )
        
        # Season dropdown (empty until competition selected)
        self.season_dropdown = Dropdown(
            20, 320, 260, 40, [], self.font_small, "Select Season"
        )
        
        # Team dropdowns
        self.team_a_dropdown = Dropdown(
            20, 390, 120, 40, [], self.font_small, "Home Team"
        )
        
        self.team_b_dropdown = Dropdown(
            160, 390, 120, 40, [], self.font_small, "Away Team"
        )
        
        # Start Replay button
        self.start_button = Button(
            20, 460, 260, 48, "Start Replay", self.font_medium,
            color=BUTTON_SUCCESS, hover_color=BUTTON_SUCCESS_HOVER
        )
        
        # ================================================================
        # ML MODE CONTROLS
        # ================================================================
        # ML Competition dropdown (locked to supported competitions)
        ml_competitions = list(ML_SUPPORTED.keys()) if ML_SUPPORTED else ["La Liga"]
        self.ml_competition_dropdown = Dropdown(
            20, 260, 260, 40, ml_competitions, self.font_small, "Competition"
        )
        # Pre-select if only one option
        if len(ml_competitions) == 1:
            self.ml_competition_dropdown.selected_index = 0
        
        # ML Season dropdown (only supported seasons)
        ml_seasons = []
        if ML_SUPPORTED and ml_competitions:
            ml_seasons = ML_SUPPORTED.get(ml_competitions[0], {}).get("seasons", [])
        self.ml_season_dropdown = Dropdown(
            20, 320, 260, 40, ml_seasons, self.font_small, "Select Season"
        )
        
        # ML Team dropdowns (only supported teams)
        ml_teams = []
        if ML_SUPPORTED and ml_competitions:
            ml_teams = ML_SUPPORTED.get(ml_competitions[0], {}).get("teams", [])
        self.ml_home_dropdown = Dropdown(
            20, 390, 120, 40, ml_teams, self.font_small, "Home Team"
        )
        self.ml_away_dropdown = Dropdown(
            160, 390, 120, 40, ml_teams, self.font_small, "Away Team"
        )
        
        # ML Predict button
        self.ml_button = Button(
            20, 460, 260, 48, "Predict Match", self.font_medium,
            color=BUTTON_PRIMARY, hover_color=BUTTON_PRIMARY_HOVER
        )
        
        # Loading state
        self.is_loading = False
    
    
    def init_simulation(self, team_a: str, team_b: str, player_info: Dict):
        """Initialize simulation view."""
        self.state = UIState.SIMULATION
        self.team_a_name = team_a
        self.team_b_name = team_b
        self.player_info = player_info
        self.pitch = PitchRenderer(PITCH_WIDTH_PX, PITCH_HEIGHT_PX)
        self._init_simulation_ui()
    
    def render_menu(self):
        """Render the menu screen with mode-first design."""
        # ================================================================
        # BACKGROUND RENDERING
        # ================================================================
        # Draw gradient background for main area
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(BACKGROUND_GRADIENT_TOP[0] + (BACKGROUND_GRADIENT_BOTTOM[0] - BACKGROUND_GRADIENT_TOP[0]) * ratio)
            g = int(BACKGROUND_GRADIENT_TOP[1] + (BACKGROUND_GRADIENT_BOTTOM[1] - BACKGROUND_GRADIENT_TOP[1]) * ratio)
            b = int(BACKGROUND_GRADIENT_TOP[2] + (BACKGROUND_GRADIENT_BOTTOM[2] - BACKGROUND_GRADIENT_TOP[2]) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (SIDEBAR_WIDTH, y), (SCREEN_WIDTH, y))
        
        # Draw left sidebar with subtle gradient
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            base = SIDEBAR_BG
            r = int(base[0] * (1 - ratio * 0.2))
            g = int(base[1] * (1 - ratio * 0.2))
            b = int(base[2] * (1 - ratio * 0.2))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SIDEBAR_WIDTH, y))
        
        # Sidebar border accent line
        pygame.draw.line(self.screen, (50, 55, 75), (SIDEBAR_WIDTH - 1, 0), (SIDEBAR_WIDTH - 1, SCREEN_HEIGHT), 1)
        
        # ================================================================
        # TITLE AND MODE SELECTION (Always visible)
        # ================================================================
        title = self.font_title.render("Match Selector", True, TEXT_WHITE)
        self.screen.blit(title, (20, 25))
        pygame.draw.line(self.screen, HIGHLIGHT_YELLOW, (20, 75), (200, 75), 2)
        
        # Mode selection label
        mode_label = self.font_small.render("Select Mode:", True, TEXT_GRAY)
        self.screen.blit(mode_label, (20, 85))
        
        # Draw mode buttons with active state
        is_replay_active = self.menu_mode == MODE_REPLAY
        is_ml_active = self.menu_mode == MODE_ML
        self.mode_replay_button.draw(self.screen, active=is_replay_active)
        self.mode_ml_button.draw(self.screen, active=is_ml_active)
        
        # ================================================================
        # CONTEXT-AWARE CONTROLS (Based on mode)
        # ================================================================
        if self.menu_mode == MODE_REPLAY:
            self._render_replay_controls()
        elif self.menu_mode == MODE_ML:
            self._render_ml_controls()
        
        # ================================================================
        # RIGHT PANEL (Context help + Results)
        # ================================================================
        self._render_right_panel()
        
        # ================================================================
        # DRAW EXPANDED DROPDOWNS LAST (On top)
        # ================================================================
        self._render_expanded_dropdowns()
    
    def _render_replay_controls(self):
        """Render controls for Replay mode."""
        # Labels
        labels = [
            ("1. Competition", 240),
            ("2. Season", 300),
            ("3. Teams", 370),
        ]
        for label, y in labels:
            text = self.font_small.render(label, True, TEXT_GRAY)
            self.screen.blit(text, (20, y))
        
        # Dropdowns (only draw if not expanded elsewhere)
        if not self.competition_dropdown.is_open:
            self.competition_dropdown.draw(self.screen)
        if not self.season_dropdown.is_open:
            self.season_dropdown.draw(self.screen)
        if not self.team_a_dropdown.is_open and not self.team_b_dropdown.is_open:
            self.team_a_dropdown.draw(self.screen)
            self.team_b_dropdown.draw(self.screen)
            # VS text
            vs_text = self.font_small.render("VS", True, TEXT_WHITE)
            self.screen.blit(vs_text, (140, 400))
        
        # Start button
        self.start_button.draw(self.screen)
    
    def _render_ml_controls(self):
        """Render controls for ML Prediction mode."""
        # Labels
        labels = [
            ("Competition (La Liga)", 240),
            ("Season", 300),
            ("Teams", 370),
        ]
        for label, y in labels:
            text = self.font_small.render(label, True, TEXT_GRAY)
            self.screen.blit(text, (20, y))
        
        # ML Dropdowns
        if not self.ml_competition_dropdown.is_open:
            self.ml_competition_dropdown.draw(self.screen)
        if not self.ml_season_dropdown.is_open:
            self.ml_season_dropdown.draw(self.screen)
        if not self.ml_home_dropdown.is_open and not self.ml_away_dropdown.is_open:
            self.ml_home_dropdown.draw(self.screen)
            self.ml_away_dropdown.draw(self.screen)
            # VS text
            vs_text = self.font_small.render("VS", True, TEXT_WHITE)
            self.screen.blit(vs_text, (140, 400))
        
        # Predict button
        self.ml_button.draw(self.screen)
    
    def _render_right_panel(self):
        """Render the right panel with context help or ML results."""
        content_x = SIDEBAR_WIDTH + 50
        content_y = 50
        
        if self.ml_result:
            # Show ML Prediction Results
            self._render_ml_result(content_x, content_y)
        else:
            # Show mode-specific instructions
            self._render_instructions(content_x, content_y)
        
        # Loading indicator
        if hasattr(self, 'is_loading') and self.is_loading:
            loading_text = self.font_medium.render("Loading...", True, HIGHLIGHT_YELLOW)
            self.screen.blit(loading_text, (content_x, SCREEN_HEIGHT - 100))
    
    def _render_instructions(self, x, y):
        """Render context-aware instructions based on mode."""
        if self.menu_mode is None:
            # No mode selected yet
            instructions = [
                "Welcome to Football Match Simulator!",
                "",
                "Choose a mode to get started:",
                "",
                "Replay Match",
                "  Watch real match data with player",
                "  movement, events, and live stats.",
                "",
                "ML Prediction", 
                "  AI-powered match prediction using",
                "  trained models on La Liga data.",
                "",
                "Select a mode on the left to continue."
            ]
        elif self.menu_mode == MODE_REPLAY:
            instructions = [
                "Replay Match Mode",
                "",
                "Watch real matches with:",
                "  - Actual player positions",
                "  - Real match events",
                "  - Live statistics",
                "",
                "Controls during replay:",
                "  SPACE - Play/Pause",
                "  Left/Right - Seek +/-5s",
                "  Click player - View stats",
                "  ESC - Return to menu",
                "",
                "Select competition, season, and teams."
            ]
        else:  # MODE_ML
            instructions = [
                "ML Prediction Mode",
                "",
                "AI-powered predictions using:",
                "  - ELO ratings",
                "  - Historical La Liga data",
                "  - Random Forest classifier",
                "",
                "Outputs:",
                "  - Win probability",
                "  - Expected score",
                "  - Simulated goal events",
                "",
                "Select season and teams, then predict."
            ]
        
        for inst in instructions:
            color = TEXT_WHITE if inst and not inst.startswith(" ") else TEXT_GRAY
            text = self.font_small.render(inst, True, color)
            self.screen.blit(text, (x, y))
            y += 26
    
    def _render_ml_result(self, x, y):
        """Render ML prediction results."""
        result = self.ml_result
        
        # Title
        title = self.font_title.render("ML Match Prediction", True, HIGHLIGHT_YELLOW)
        self.screen.blit(title, (x, y))
        y += 60
        
        # Teams and Score
        match_text = f"{result.home_team}  vs  {result.away_team}"
        self.screen.blit(self.font_large.render(match_text, True, TEXT_WHITE), (x, y))
        y += 50
        
        # Predicted Score
        score_text = f"Predicted: {result.home_goals} - {result.away_goals}"
        self.screen.blit(self.font_large.render(score_text, True, TEXT_WHITE), (x, y))
        y += 45
        
        # Outcome
        outcome_colors = {'H': (100, 255, 100), 'D': (255, 255, 100), 'A': (255, 100, 100)}
        outcome_labels = {'H': 'HOME WIN', 'D': 'DRAW', 'A': 'AWAY WIN'}
        outcome_color = outcome_colors.get(result.predicted_outcome, TEXT_GRAY)
        outcome_text = outcome_labels.get(result.predicted_outcome, 'UNKNOWN')
        self.screen.blit(self.font_medium.render(outcome_text, True, outcome_color), (x, y))
        y += 50
        
        # ELO Ratings
        self.screen.blit(self.font_medium.render("ELO Ratings", True, TEXT_WHITE), (x, y))
        y += 28
        self.screen.blit(self.font_small.render(f"  {result.home_team}: {result.home_elo:.0f}", True, TEAM_A_COLOR), (x, y))
        y += 22
        self.screen.blit(self.font_small.render(f"  {result.away_team}: {result.away_elo:.0f}", True, TEAM_B_COLOR), (x, y))
        y += 22
        diff_color = (100, 255, 100) if result.elo_diff > 0 else (255, 100, 100)
        self.screen.blit(self.font_small.render(f"  Diff: {result.elo_diff:+.0f}", True, diff_color), (x, y))
        y += 35
        
        # Win Probabilities (compact)
        self.screen.blit(self.font_medium.render("Win Probability", True, TEXT_WHITE), (x, y))
        y += 28
        bar_width = 280
        bar_height = 20
        probs = [
            (f"Home: {result.home_win_prob*100:.0f}%", result.home_win_prob, TEAM_A_COLOR),
            (f"Draw: {result.draw_prob*100:.0f}%", result.draw_prob, (200, 200, 100)),
            (f"Away: {result.away_win_prob*100:.0f}%", result.away_win_prob, TEAM_B_COLOR)
        ]
        for text, prob, color in probs:
            pygame.draw.rect(self.screen, (50, 50, 60), (x, y, bar_width, bar_height))
            pygame.draw.rect(self.screen, color, (x, y, int(bar_width * prob), bar_height))
            self.screen.blit(self.font_small.render(text, True, TEXT_WHITE), (x + 5, y + 2))
            y += 26
        
        # Hint
        y += 15
        self.screen.blit(self.font_small.render("Click 'Predict Match' to resimulate", True, TEXT_DARK_GRAY), (x, y))
    
    def _render_expanded_dropdowns(self):
        """Render expanded dropdowns on top of other elements."""
        if self.menu_mode == MODE_REPLAY:
            if self.competition_dropdown.is_open:
                self.competition_dropdown.draw(self.screen)
            if self.season_dropdown.is_open:
                self.season_dropdown.draw(self.screen)
            if self.team_a_dropdown.is_open:
                self.team_a_dropdown.draw(self.screen)
            if self.team_b_dropdown.is_open:
                self.team_b_dropdown.draw(self.screen)
        elif self.menu_mode == MODE_ML:
            if self.ml_competition_dropdown.is_open:
                self.ml_competition_dropdown.draw(self.screen)
            if self.ml_season_dropdown.is_open:
                self.ml_season_dropdown.draw(self.screen)
            if self.ml_home_dropdown.is_open:
                self.ml_home_dropdown.draw(self.screen)
            if self.ml_away_dropdown.is_open:
                self.ml_away_dropdown.draw(self.screen)

    
    def render_simulation(self, game_state: GameState):
        """Render the simulation screen."""
        self.screen.fill(BACKGROUND_DARK)
        
        # Draw pitch
        if self.pitch:
            self.screen.blit(self.pitch.get_surface(), (SIDEBAR_WIDTH, 100))
        
        # Draw players
        self._draw_players(game_state)
        
        # Draw ball
        self._draw_ball(game_state)
        
        # Draw UI panels
        self._draw_top_bar(game_state)
        self._draw_left_sidebar(game_state)
        self._draw_top_bar(game_state)
        self._draw_left_sidebar(game_state)
        self._draw_stats_panel(game_state)
        self._draw_controls(game_state)
    
    def _draw_controls(self, game_state: GameState):
        """Draw simulation controls at bottom."""
        # Background bar
        ctrl_y = SCREEN_HEIGHT - 80
        pygame.draw.rect(self.screen, PANEL_BG, (SIDEBAR_WIDTH, ctrl_y, PITCH_WIDTH_PX, 80))
        pygame.draw.line(self.screen, TEXT_GRAY, (SIDEBAR_WIDTH, ctrl_y), (SIDEBAR_WIDTH + PITCH_WIDTH_PX, ctrl_y), 1)
        
        self.btn_play_pause.draw(self.screen)
        self.btn_speed_1x.draw(self.screen)
        self.btn_speed_2x.draw(self.screen)
        self.btn_speed_4x.draw(self.screen)
        
        # Calculate progress
        # Assume max 90 mins (5400s) + extra time, or based on last event?
        # Use 125 mins (7500s) as safe max for seek bar scaling
        progress = min(1.0, game_state.timestamp / 7500.0)
        self.seek_bar.draw(self.screen, progress)
        
        # FIX: Draw time labels left and right of seek bar
        # Current time
        cur_min = int(game_state.timestamp / 60)
        cur_sec = int(game_state.timestamp % 60)
        cur_text = self.font_small.render(f"{cur_min:02d}:{cur_sec:02d}", True, TEXT_WHITE)
        self.screen.blit(cur_text, (self.seek_bar.rect.left - 50, self.seek_bar.rect.y))
        
        # Total time (Total is ~125 mins max for seeker)
        # Or should we show "90:00" / "120:00"?
        # Let's show the max scale of the seek bar which is 125m
        total_text = self.font_small.render("125:00", True, TEXT_GRAY)
        self.screen.blit(total_text, (self.seek_bar.rect.right + 10, self.seek_bar.rect.y))
        
        # Time tooltip on hover? (optional)
    
    def _draw_players(self, game_state: GameState):
        """Draw all players with enhanced visuals."""
        if not self.pitch:
            return
        
        for player_id, player_state in game_state.players.items():
            if not player_state.is_active:
                continue
            
            px, py = self.pitch.statsbomb_to_pixels(player_state.x, player_state.y)
            px += SIDEBAR_WIDTH
            py += 100
            
            # Team color
            player_data = self.player_info.get(player_id, {})
            team_name = player_data.get('team', '')
            color = TEAM_A_COLOR if team_name == self.team_a_name else TEAM_B_COLOR
            
            # Draw shadow first
            shadow_offset = 2
            shadow_color = (20, 20, 25)
            pygame.draw.circle(self.screen, shadow_color, (px + shadow_offset, py + shadow_offset), PLAYER_RADIUS)
            
            # Ball possession glow (outer)
            if player_state.has_ball:
                glow_color = (255, 220, 100, 100)  # Golden glow
                for r in range(PLAYER_RADIUS + 8, PLAYER_RADIUS + 2, -2):
                    alpha = int(80 * (1 - (r - PLAYER_RADIUS - 2) / 6))
                    glow = (255, min(255, 215 + alpha // 4), 50)
                    pygame.draw.circle(self.screen, glow, (px, py), r, 2)
            
            # Selection ring (animated feel)
            if player_id == self.selected_player_id:
                pygame.draw.circle(self.screen, SELECTED_RING, (px, py), PLAYER_RADIUS + 6, 3)
                # Inner ring for emphasis
                pygame.draw.circle(self.screen, (255, 255, 200), (px, py), PLAYER_RADIUS + 4, 1)
            
            # Main player circle with gradient effect (simulated)
            # Darker center for depth
            pygame.draw.circle(self.screen, color, (px, py), PLAYER_RADIUS)
            # Highlight on top left
            highlight_color = tuple(min(255, c + 50) for c in color)
            pygame.draw.circle(self.screen, highlight_color, (px - 2, py - 2), PLAYER_RADIUS - 4)
            # Border
            pygame.draw.circle(self.screen, LINE_WHITE, (px, py), PLAYER_RADIUS, 2)
            
            # Jersey number with better contrast
            jersey = str(player_data.get('jersey_number', '?'))
            # Draw text shadow
            num_shadow = self.font_small.render(jersey, True, (0, 0, 0))
            shadow_rect = num_shadow.get_rect(center=(px + 1, py + 1))
            self.screen.blit(num_shadow, shadow_rect)
            # Draw text
            num_text = self.font_small.render(jersey, True, TEXT_WHITE)
            num_rect = num_text.get_rect(center=(px, py))
            self.screen.blit(num_text, num_rect)
    
    def _draw_ball(self, game_state: GameState):
        """Draw the ball with glow effect."""
        if not self.pitch or not game_state.ball.in_play:
            return
        
        px, py = self.pitch.statsbomb_to_pixels(game_state.ball.x, game_state.ball.y)
        px += SIDEBAR_WIDTH
        py += 100
        
        # Outer glow effect
        glow_colors = [(255, 255, 200), (255, 255, 240), (255, 255, 255)]
        for i, glow_color in enumerate(reversed(glow_colors)):
            pygame.draw.circle(self.screen, glow_color, (px, py), BALL_RADIUS + 3 - i, 1)
        
        # Shadow
        pygame.draw.circle(self.screen, (30, 30, 35), (px + 2, py + 2), BALL_RADIUS)
        
        # Main ball with slight gradient (highlight)
        pygame.draw.circle(self.screen, BALL_COLOR, (px, py), BALL_RADIUS)
        pygame.draw.circle(self.screen, (200, 200, 200), (px, py), BALL_RADIUS, 1)
        
        # Highlight dot for 3D effect
        pygame.draw.circle(self.screen, (255, 255, 255), (px - 1, py - 1), 2)
    
    def _draw_top_bar(self, game_state: GameState):
        """Draw top scoreboard."""
        pygame.draw.rect(self.screen, PANEL_BG, (SIDEBAR_WIDTH, 0, PITCH_WIDTH_PX, 100))
        
        # Score
        score_text = f"{self.team_a_name} {game_state.score_home} - {game_state.score_away} {self.team_b_name}"
        score_surface = self.font_large.render(score_text, True, TEXT_WHITE)
        score_rect = score_surface.get_rect(center=(SIDEBAR_WIDTH + PITCH_WIDTH_PX // 2, 35))
        self.screen.blit(score_surface, score_rect)
        
        # Time
        minute = int(game_state.timestamp / 60)
        second = int(game_state.timestamp % 60)
        time_text = f"{minute:02d}:{second:02d}"
        time_surface = self.font_medium.render(time_text, True, TEXT_GRAY)
        self.screen.blit(time_surface, (SIDEBAR_WIDTH + 20, 70))
        
        # Period
        period_text = f"{'1st' if game_state.period == 1 else '2nd'} Half"
        period_surface = self.font_small.render(period_text, True, TEXT_GRAY)
        self.screen.blit(period_surface, (SIDEBAR_WIDTH + PITCH_WIDTH_PX - 120, 75))
    
    def _draw_left_sidebar(self, game_state: GameState):
        """Draw left sidebar with controls."""
        pygame.draw.rect(self.screen, SIDEBAR_BG, (0, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        
        # Title
        title = self.font_medium.render("Controls", True, TEXT_WHITE)
        self.screen.blit(title, (20, 20))
        
        # Controls list
        controls = [
            ("SPACE", "Play/Pause"),
            ("left / right", "Seek ±5s"),
            ("Click", "Select Player"),
            ("ESC", "Back to Menu")
        ]
        
        y = 70
        for key, action in controls:
            key_surface = self.font_small.render(key, True, HIGHLIGHT_YELLOW)
            self.screen.blit(key_surface, (20, y))
            
            action_surface = self.font_small.render(action, True, TEXT_GRAY)
            self.screen.blit(action_surface, (20, y + 25))
            
            y += 70
        
        # Match info
        pygame.draw.line(self.screen, TEXT_GRAY, (20, y), (SIDEBAR_WIDTH - 20, y), 1)
        y += 20
        
        info_title = self.font_small.render("Match Info", True, TEXT_WHITE)
        self.screen.blit(info_title, (20, y))
        y += 35
        
        minute = int(game_state.timestamp / 60)
        info_lines = [
            f"Minute: {minute}'",
            f"Period: {game_state.period}",
            f"Score: {game_state.score_home}-{game_state.score_away}"
        ]
        
        for line in info_lines:
            text = self.font_small.render(line, True, TEXT_GRAY)
            self.screen.blit(text, (20, y))
            y += 30
    
    def _draw_stats_panel(self, game_state: GameState):
        """Draw right stats panel - shows ML predictions if available, else player stats."""
        panel_x = SIDEBAR_WIDTH + PITCH_WIDTH_PX
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, 0, STATS_PANEL_WIDTH, SCREEN_HEIGHT))
        
        # If ML prediction is available, show it instead of player stats
        if self.ml_result:
            self._draw_ml_predictions_panel(panel_x, game_state)
        else:
            self._draw_player_stats_panel(panel_x)
    
    def _draw_ml_predictions_panel(self, panel_x: int, game_state: GameState):
        """Draw ML predictions in the stats panel."""
        result = self.ml_result
        y = 20
        
        # Title
        title = self.font_medium.render("ML Prediction", True, HIGHLIGHT_YELLOW)
        self.screen.blit(title, (panel_x + 20, y))
        y += 45
        
        # Predicted Score
        pred_label = self.font_small.render("Predicted:", True, TEXT_GRAY)
        self.screen.blit(pred_label, (panel_x + 20, y))
        y += 25
        
        score_text = f"{result.home_goals} - {result.away_goals}"
        score_surface = self.font_large.render(score_text, True, TEXT_WHITE)
        self.screen.blit(score_surface, (panel_x + 20, y))
        y += 45
        
        # Outcome
        outcome_colors = {'H': (100, 255, 100), 'D': (255, 255, 100), 'A': (255, 100, 100)}
        outcome_labels = {'H': 'HOME WIN', 'D': 'DRAW', 'A': 'AWAY WIN'}
        outcome_color = outcome_colors.get(result.predicted_outcome, TEXT_GRAY)
        outcome_text = outcome_labels.get(result.predicted_outcome, 'UNKNOWN')
        outcome_surface = self.font_small.render(outcome_text, True, outcome_color)
        self.screen.blit(outcome_surface, (panel_x + 20, y))
        y += 40
        
        pygame.draw.line(self.screen, TEXT_GRAY, (panel_x + 20, y), (panel_x + STATS_PANEL_WIDTH - 20, y), 1)
        y += 20
        
        # Win Probabilities
        prob_title = self.font_small.render("Win Probability", True, TEXT_WHITE)
        self.screen.blit(prob_title, (panel_x + 20, y))
        y += 28
        
        bar_width = STATS_PANEL_WIDTH - 50
        bar_height = 18
        probs = [
            ("Home", result.home_win_prob, TEAM_A_COLOR),
            ("Draw", result.draw_prob, (200, 200, 100)),
            ("Away", result.away_win_prob, TEAM_B_COLOR)
        ]
        
        for label, prob, color in probs:
            # Label
            label_surf = self.font_small.render(f"{label}: {prob*100:.0f}%", True, TEXT_GRAY)
            self.screen.blit(label_surf, (panel_x + 20, y))
            y += 20
            # Bar background
            pygame.draw.rect(self.screen, (40, 40, 50), (panel_x + 20, y, bar_width, bar_height))
            # Bar fill
            fill_width = int(bar_width * prob)
            pygame.draw.rect(self.screen, color, (panel_x + 20, y, fill_width, bar_height))
            y += 25
        
        y += 10
        pygame.draw.line(self.screen, TEXT_GRAY, (panel_x + 20, y), (panel_x + STATS_PANEL_WIDTH - 20, y), 1)
        y += 20
        
        # ELO Ratings
        elo_title = self.font_small.render("ELO Ratings", True, TEXT_WHITE)
        self.screen.blit(elo_title, (panel_x + 20, y))
        y += 28
        
        home_elo = f"{result.home_team[:12]}: {result.home_elo:.0f}"
        away_elo = f"{result.away_team[:12]}: {result.away_elo:.0f}"
        self.screen.blit(self.font_small.render(home_elo, True, TEAM_A_COLOR), (panel_x + 20, y))
        y += 22
        self.screen.blit(self.font_small.render(away_elo, True, TEAM_B_COLOR), (panel_x + 20, y))
        y += 22
        
        diff_color = (100, 255, 100) if result.elo_diff > 0 else (255, 100, 100)
        diff_text = f"Diff: {result.elo_diff:+.0f}"
        self.screen.blit(self.font_small.render(diff_text, True, diff_color), (panel_x + 20, y))
        y += 35
        
        pygame.draw.line(self.screen, TEXT_GRAY, (panel_x + 20, y), (panel_x + STATS_PANEL_WIDTH - 20, y), 1)
        y += 20
        
        # Predicted Goals
        goals_title = self.font_small.render("Predicted Goals", True, TEXT_WHITE)
        self.screen.blit(goals_title, (panel_x + 20, y))
        y += 25
        
        goal_events = [e for e in result.events if e.event_type == 'goal']
        for event in goal_events[:8]:
            color = TEAM_A_COLOR if event.team == 'home' else TEAM_B_COLOR
            event_text = f"{event.minute}'"
            team_name = result.home_team if event.team == 'home' else result.away_team
            self.screen.blit(self.font_small.render(event_text, True, color), (panel_x + 20, y))
            self.screen.blit(self.font_small.render(team_name[:15], True, TEXT_GRAY), (panel_x + 50, y))
            y += 22
        
        if not goal_events:
            self.screen.blit(self.font_small.render("0-0 Draw predicted", True, TEXT_DARK_GRAY), (panel_x + 20, y))
    
    def _draw_player_stats_panel(self, panel_x: int):
        """Draw player stats in the stats panel (original behavior)."""
        # Title
        title = self.font_medium.render("Player Stats", True, TEXT_WHITE)
        self.screen.blit(title, (panel_x + 20, 20))
        
        if self.selected_player_id and self.selected_player_id in self.player_info:
            player = self.player_info[self.selected_player_id]
            y = 70
            
            # Player name
            name = player.get('name', 'Unknown')
            name_surface = self.font_medium.render(name, True, TEXT_WHITE)
            self.screen.blit(name_surface, (panel_x + 20, y))
            y += 40
            
            # Jersey and position
            jersey = player.get('jersey_number', '?')
            position = player.get('position', 'Unknown')
            info_text = f"#{jersey} | {position}"
            info_surface = self.font_small.render(info_text, True, TEXT_GRAY)
            self.screen.blit(info_surface, (panel_x + 20, y))
            y += 40
            
            # Team
            team = player.get('team', 'Unknown')
            team_surface = self.font_small.render(f"Team: {team}", True, TEXT_GRAY)
            self.screen.blit(team_surface, (panel_x + 20, y))
            y += 50
            
            # Stats
            stats = player.get('stats', {})
            if stats:
                pygame.draw.line(self.screen, TEXT_GRAY, (panel_x + 20, y), (panel_x + STATS_PANEL_WIDTH - 20, y), 1)
                y += 30
                
                stat_lines = [
                    ("Touches", stats.get('touches', 0)),
                    ("Passes", f"{stats.get('passes_completed', 0)}/{stats.get('passes_attempted', 0)}"),
                    ("Pass Acc.", stats.get('pass_completion', 'N/A')),
                    ("Shots", stats.get('shots', 0)),
                    ("Goals", stats.get('goals', 0)),
                    ("Shot Acc.", stats.get('shot_accuracy', 'N/A')),
                    ("Dribbles", stats.get('dribbles', 0)),
                    ("Tackles", stats.get('tackles', 0)),
                    ("Interceptions", stats.get('interceptions', 0))
                ]
                
                for label, value in stat_lines:
                    label_surface = self.font_small.render(label, True, TEXT_GRAY)
                    self.screen.blit(label_surface, (panel_x + 20, y))
                    
                    value_surface = self.font_small.render(str(value), True, TEXT_WHITE)
                    value_rect = value_surface.get_rect(right=panel_x + STATS_PANEL_WIDTH - 20)
                    value_rect.y = y
                    self.screen.blit(value_surface, value_rect)
                    
                    y += 35
        else:
            hint = self.font_small.render("Click a player to", True, TEXT_DARK_GRAY)
            self.screen.blit(hint, (panel_x + 20, 100))
            
            hint2 = self.font_small.render("view their stats", True, TEXT_DARK_GRAY)
            self.screen.blit(hint2, (panel_x + 20, 130))
    
    def handle_menu_event(self, event) -> str:
        """
        Handle menu events with mode-first logic.
        
        Returns action type: 'start', 'ml', or ''.
        """
        # ================================================================
        # MODE SELECTION BUTTONS (Always visible, handle first)
        # ================================================================
        if self.mode_replay_button.handle_event(event):
            if self.menu_mode != MODE_REPLAY:
                self.menu_mode = MODE_REPLAY
                self._reset_selections()
            return ''
        
        if self.mode_ml_button.handle_event(event):
            if self.menu_mode != MODE_ML:
                self.menu_mode = MODE_ML
                self._reset_selections()
            return ''
        
        # ================================================================
        # MODE-SPECIFIC CONTROLS
        # ================================================================
        if self.menu_mode == MODE_REPLAY:
            # Handle Replay mode dropdowns
            self.competition_dropdown.handle_event(event)
            self.season_dropdown.handle_event(event)
            self.team_a_dropdown.handle_event(event)
            self.team_b_dropdown.handle_event(event)
            
            # Handle start button
            if self.start_button.handle_event(event):
                return 'start'
                
        elif self.menu_mode == MODE_ML:
            # Handle ML mode dropdowns
            self.ml_competition_dropdown.handle_event(event)
            self.ml_season_dropdown.handle_event(event)
            self.ml_home_dropdown.handle_event(event)
            self.ml_away_dropdown.handle_event(event)
            
            # Handle ML button
            if self.ml_button.handle_event(event):
                return 'ml'
        
        return ''
    
    def _reset_selections(self):
        """Reset dropdown selections when mode changes."""
        # Reset Replay mode dropdowns
        self.competition_dropdown.selected_index = -1
        self.season_dropdown.selected_index = -1
        self.season_dropdown.options = []
        self.team_a_dropdown.selected_index = -1
        self.team_a_dropdown.options = []
        self.team_b_dropdown.selected_index = -1
        self.team_b_dropdown.options = []
        
        # Reset ML mode dropdowns
        self.ml_season_dropdown.selected_index = -1
        self.ml_home_dropdown.selected_index = -1
        self.ml_away_dropdown.selected_index = -1
        
        # Clear ML result when switching modes
        self.ml_result = None
    
    def handle_simulation_click(self, pos: Tuple[int, int], game_state: GameState) -> Optional[str]:
        """Handle click in simulation. Returns selected player_id."""
        if not self.pitch:
            return None
        
        mx, my = pos
        mx -= SIDEBAR_WIDTH
        my -= 100
        
        for player_id, player_state in game_state.players.items():
            px, py = self.pitch.statsbomb_to_pixels(player_state.x, player_state.y)
            
            distance = ((mx - px) ** 2 + (my - py) ** 2) ** 0.5
            if distance <= PLAYER_RADIUS + 5:
                self.selected_player_id = player_id
                return player_id
        
        return None
        
    def handle_control_event(self, event, game_engine) -> bool:
        """
        Handle events for simulation controls. 
        Returns True if an action was taken.
        """
        if not self.btn_play_pause:
            return False
            
        # Play/Pause
        if self.btn_play_pause.handle_event(event):
            # Toggle handled by caller looking at game engine state usually, 
            # but we can return 'toggle' action or just modify here?
            # Ideally main loop handles logic. We just report click.
            return "toggle_pause"
            
        # Speed
        if self.btn_speed_1x.handle_event(event):
            game_engine.set_playback_speed(1.0)
            return True
        if self.btn_speed_2x.handle_event(event):
            game_engine.set_playback_speed(2.0)
            return True
        if self.btn_speed_4x.handle_event(event):
            game_engine.set_playback_speed(4.0)
            return True
            
        # Seek Bar
        seek_progress = self.seek_bar.handle_event(event)
        if seek_progress is not None:
            # Seek to time (0-7500s covers 125 mins)
            target_time = seek_progress * 7500.0
            game_engine.seek_to_time(target_time)
            return "seeking"
            
        return False
    
    def render(self, game_state: Optional[GameState] = None):
        """Main render function."""
        if self.state == UIState.MENU:
            self.render_menu()
        elif self.state == UIState.SIMULATION and game_state:
            self.render_simulation(game_state)
        elif self.state == UIState.ML_SIMULATION:
            self.render_ml_simulation()
    
    def init_ml_simulation(self, ml_result):
        """Initialize ML simulation view."""
        self.state = UIState.ML_SIMULATION
        self.ml_result = ml_result
        
        # Create back and resimulate buttons
        self.ml_back_button = Button(
            SIDEBAR_WIDTH + 50, SCREEN_HEIGHT - 80, 150, 45, "← Back to Menu", self.font_small
        )
        self.ml_resim_button = Button(
            SIDEBAR_WIDTH + 220, SCREEN_HEIGHT - 80, 150, 45, "🔄 Resimulate", self.font_small
        )
    
    def handle_ml_event(self, event) -> str:
        """Handle ML simulation events. Returns 'back', 'resim', or ''."""
        if self.ml_back_button and self.ml_back_button.handle_event(event):
            return 'back'
        if self.ml_resim_button and self.ml_resim_button.handle_event(event):
            return 'resim'
        return ''
    
    def render_ml_simulation(self):
        """Render the ML simulation results screen."""
        if not self.ml_result:
            return
        
        result = self.ml_result
        self.screen.fill(BACKGROUND_DARK)
        
        # Left sidebar
        pygame.draw.rect(self.screen, SIDEBAR_BG, (0, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        
        # Title
        title = self.font_title.render("ML Match Prediction", True, TEXT_WHITE)
        self.screen.blit(title, (20, 20))
        
        # ELO Ratings section
        y = 90
        elo_title = self.font_medium.render("ELO Ratings", True, HIGHLIGHT_YELLOW)
        self.screen.blit(elo_title, (20, y))
        y += 35
        
        home_elo_text = self.font_small.render(f"{result.home_team}: {result.home_elo:.0f}", True, TEXT_WHITE)
        self.screen.blit(home_elo_text, (20, y))
        y += 25
        
        away_elo_text = self.font_small.render(f"{result.away_team}: {result.away_elo:.0f}", True, TEXT_WHITE)
        self.screen.blit(away_elo_text, (20, y))
        y += 25
        
        diff_color = (100, 255, 100) if result.elo_diff > 0 else (255, 100, 100) if result.elo_diff < 0 else TEXT_GRAY
        diff_text = self.font_small.render(f"Difference: {result.elo_diff:+.0f}", True, diff_color)
        self.screen.blit(diff_text, (20, y))
        y += 45
        
        # Probabilities section
        prob_title = self.font_medium.render("Win Probability", True, HIGHLIGHT_YELLOW)
        self.screen.blit(prob_title, (20, y))
        y += 35
        
        prob_data = [
            (f"Home Win: {result.home_win_prob*100:.1f}%", result.home_win_prob),
            (f"Draw: {result.draw_prob*100:.1f}%", result.draw_prob),
            (f"Away Win: {result.away_win_prob*100:.1f}%", result.away_win_prob)
        ]
        
        for text, prob in prob_data:
            # Draw probability bar
            bar_width = int(220 * prob)
            pygame.draw.rect(self.screen, (60, 60, 70), (20, y, 220, 20))
            pygame.draw.rect(self.screen, HIGHLIGHT_YELLOW, (20, y, bar_width, 20))
            
            prob_text = self.font_small.render(text, True, TEXT_WHITE)
            self.screen.blit(prob_text, (25, y + 2))
            y += 30
        
        y += 20
        
        # Form statistics
        form_title = self.font_medium.render("Recent Form", True, HIGHLIGHT_YELLOW)
        self.screen.blit(form_title, (20, y))
        y += 30
        
        # Home team form
        home_form_text = self.font_small.render(f"{result.home_team}:", True, TEXT_WHITE)
        self.screen.blit(home_form_text, (20, y))
        y += 22
        
        for key, val in result.home_form.items():
            stat_text = self.font_small.render(f"  {key}: {val}", True, TEXT_GRAY)
            self.screen.blit(stat_text, (20, y))
            y += 20
        y += 10
        
        # Away team form
        away_form_text = self.font_small.render(f"{result.away_team}:", True, TEXT_WHITE)
        self.screen.blit(away_form_text, (20, y))
        y += 22
        
        for key, val in result.away_form.items():
            stat_text = self.font_small.render(f"  {key}: {val}", True, TEXT_GRAY)
            self.screen.blit(stat_text, (20, y))
            y += 20
        
        # Main content area - Score and Events
        content_x = SIDEBAR_WIDTH + 40
        
        # Match header
        pygame.draw.rect(self.screen, PANEL_BG, (SIDEBAR_WIDTH, 0, SCREEN_WIDTH - SIDEBAR_WIDTH, 140))
        
        # Team names and score
        home_name = self.font_large.render(result.home_team, True, TEAM_A_COLOR)
        away_name = self.font_large.render(result.away_team, True, TEAM_B_COLOR)
        
        center_x = SIDEBAR_WIDTH + (SCREEN_WIDTH - SIDEBAR_WIDTH) // 2
        
        # Home team name (left)
        self.screen.blit(home_name, (center_x - 200 - home_name.get_width(), 40))
        
        # Score
        score_text = f"{result.home_goals} - {result.away_goals}"
        score_surface = self.font_title.render(score_text, True, TEXT_WHITE)
        score_rect = score_surface.get_rect(center=(center_x, 55))
        self.screen.blit(score_surface, score_rect)
        
        # Away team name (right)
        self.screen.blit(away_name, (center_x + 200, 40))
        
        # Outcome badge
        outcome_colors = {'H': (100, 200, 100), 'D': (200, 200, 100), 'A': (200, 100, 100)}
        outcome_labels = {'H': 'HOME WIN', 'D': 'DRAW', 'A': 'AWAY WIN'}
        outcome_color = outcome_colors.get(result.predicted_outcome, TEXT_GRAY)
        outcome_text = outcome_labels.get(result.predicted_outcome, 'UNKNOWN')
        
        outcome_surface = self.font_medium.render(outcome_text, True, outcome_color)
        outcome_rect = outcome_surface.get_rect(center=(center_x, 100))
        self.screen.blit(outcome_surface, outcome_rect)
        
        # Match events timeline
        events_title = self.font_medium.render("Match Events", True, TEXT_WHITE)
        self.screen.blit(events_title, (content_x, 160))
        
        # Draw timeline
        timeline_y = 210
        timeline_start = content_x
        timeline_end = SCREEN_WIDTH - 100
        timeline_width = timeline_end - timeline_start
        
        pygame.draw.line(self.screen, TEXT_GRAY, (timeline_start, timeline_y), (timeline_end, timeline_y), 2)
        
        # Draw minute markers
        for minute in [0, 15, 30, 45, 60, 75, 90]:
            x = timeline_start + int(timeline_width * minute / 90)
            pygame.draw.line(self.screen, TEXT_GRAY, (x, timeline_y - 5), (x, timeline_y + 5), 1)
            minute_text = self.font_small.render(str(minute), True, TEXT_DARK_GRAY)
            self.screen.blit(minute_text, (x - 8, timeline_y + 10))
        
        # Draw events on timeline
        for event in result.events:
            x = timeline_start + int(timeline_width * min(event.minute, 90) / 90)
            color = TEAM_A_COLOR if event.team == 'home' else TEAM_B_COLOR
            
            if event.event_type == 'goal':
                pygame.draw.circle(self.screen, color, (x, timeline_y), 10)
                pygame.draw.circle(self.screen, TEXT_WHITE, (x, timeline_y), 10, 2)
            elif event.event_type == 'yellow_card':
                pygame.draw.rect(self.screen, (255, 255, 0), (x - 4, timeline_y - 8, 8, 12))
        
        # Events list
        events_y = 260
        for i, event in enumerate(result.events[:12]):  # Limit to 12 events
            event_color = TEAM_A_COLOR if event.team == 'home' else TEAM_B_COLOR
            minute_str = f"{event.minute}'"
            
            minute_surface = self.font_small.render(minute_str, True, event_color)
            self.screen.blit(minute_surface, (content_x, events_y))
            
            desc_surface = self.font_small.render(event.description, True, TEXT_WHITE)
            self.screen.blit(desc_surface, (content_x + 50, events_y))
            
            events_y += 28
        
        # Buttons
        if self.ml_back_button:
            self.ml_back_button.draw(self.screen)
        if self.ml_resim_button:
            self.ml_resim_button.draw(self.screen)