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


class UIState(Enum):
    """Application UI states."""
    MENU = "menu"
    SIMULATION = "simulation"


class Button:
    """Simple button class."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
    
    def draw(self, screen):
        """Draw the button."""
        color = BUTTON_HOVER if self.hovered else BUTTON_BG
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, TEXT_GRAY, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, TEXT_WHITE)
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
        """Draw the dropdown."""
        # Determine if disabled
        is_disabled = not self.options or not self.enabled
        
        # Main button
        if is_disabled:
            color = (30, 30, 35)  # Darker when disabled
        elif self.is_open:
            color = BUTTON_HOVER
        else:
            color = DROPDOWN_BG
        
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, TEXT_GRAY if not is_disabled else TEXT_DARK_GRAY, self.rect, 2)
        
        # Text
        text = self.selected or self.default_text
        text_color = TEXT_DARK_GRAY if is_disabled else TEXT_WHITE
        text_surface = self.font.render(text, True, text_color)
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))
        
        # Arrow
        if not is_disabled:
            arrow = "▼" if not self.is_open else "▲"
            arrow_surface = self.font.render(arrow, True, TEXT_WHITE)
            screen.blit(arrow_surface, (self.rect.right - 25, self.rect.y + 10))
        
        # Options (if open)
        if self.is_open and self.options:
            visible_options = self.options[self.scroll_offset : self.scroll_offset + self.max_visible]
            
            for i, option in enumerate(visible_options):
                # Calculate rect relative to scroll window
                option_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.bottom + i * self.rect.height,
                    self.rect.width,
                    self.rect.height
                )
                
                # Background
                option_index = self.scroll_offset + i
                if option_index == self.hovered_option:
                    pygame.draw.rect(screen, BUTTON_HOVER, option_rect)
                elif option_index == self.selected_index:
                    pygame.draw.rect(screen, DROPDOWN_BG, option_rect) # Selected but not hovered
                else:
                    pygame.draw.rect(screen, DROPDOWN_BG, option_rect)
                
                pygame.draw.rect(screen, TEXT_GRAY, option_rect, 1)
                
                # Text (truncate if too long)
                option_text = option if len(option) < 25 else option[:22] + "..."
                option_surface = self.font.render(option_text, True, TEXT_WHITE)
                screen.blit(option_surface, (option_rect.x + 10, option_rect.y + 10))
            
            # Scroll indicator (simple bars)
            if len(self.options) > self.max_visible:
                total_height = self.max_visible * self.rect.height
                bar_height = max(10, total_height * (self.max_visible / len(self.options)))
                scroll_ratio = self.scroll_offset / (len(self.options) - self.max_visible)
                bar_y = self.rect.bottom + scroll_ratio * (total_height - bar_height)
                
                scrollbar_rect = pygame.Rect(self.rect.right - 5, bar_y, 4, bar_height)
                pygame.draw.rect(screen, TEXT_GRAY, scrollbar_rect)
    
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
        """Initialize menu UI elements."""
        # Competition dropdown - start with actual competitions
        competitions = list(COMPETITIONS.keys())
        self.competition_dropdown = Dropdown(
            20, 140, 260, 40, competitions, self.font_small, "Select Competition"
        )
        
        # Season dropdown (empty until competition selected)
        self.season_dropdown = Dropdown(
            20, 220, 260, 40, [], self.font_small, "Select Season"
        )
        
        # Team dropdowns (moved down)
        self.team_a_dropdown = Dropdown(
            20, 310, 110, 40, [], self.font_small, "Team A"
        )
        
        self.team_b_dropdown = Dropdown(
            150, 310, 110, 40, [], self.font_small, "Team A"
        )
        
        # Start button
        self.start_button = Button(
             20, 400, 260, 50, "Start Simulation", self.font_medium
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
        """Render the menu screen."""
        self.screen.fill(BACKGROUND_DARK)
        
        # Draw left sidebar background first
        pygame.draw.rect(self.screen, SIDEBAR_BG, (0, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        
        # Title
        title = self.font_title.render("Match Selector", True, TEXT_WHITE)
        self.screen.blit(title, (20, 30))
        
        # Labels
        labels = [
            ("1. Competition", 110),
            ("2. Season", 190),
            ("3. Teams", 280),
        ]
        
        for label, y in labels:
            text = self.font_small.render(label, True, TEXT_GRAY)
            self.screen.blit(text, (20, y))
        
        # Draw dropdowns (not expanded ones yet)
        # Competition dropdown
        if not self.competition_dropdown.is_open:
            self.competition_dropdown.draw(self.screen)
        
        # Season dropdown
        if not self.season_dropdown.is_open:
            self.season_dropdown.draw(self.screen)
        
        # Team dropdowns
        if not self.team_a_dropdown.is_open and not self.team_b_dropdown.is_open:
            self.team_a_dropdown.draw(self.screen)
            self.team_b_dropdown.draw(self.screen)
            
            # VS text between teams
            vs_text = self.font_small.render("VS", True, TEXT_WHITE)
            self.screen.blit(vs_text, (100, 320))
        
        # Start button
        self.start_button.draw(self.screen)
        
        # Instructions in main area
        inst_x = SIDEBAR_WIDTH + 50
        inst_y = 200
        
        instructions = [
            "Welcome to Football Match Simulator!",
            "",
            "How to use:",
            "1. Select a competition",
            "2. Select a season",
            "3. Choose two teams",
            "4. Click 'Start Simulation'",
            "",
            "During simulation:",
            "• SPACE - Play/Pause",
            "• left / right - Seek",
            "• Click players to see stats",
            "• ESC - Return to menu"
        ]
        
        for inst in instructions:
            color = TEXT_WHITE if inst and not inst.startswith(" ") and inst[0].isupper() and len(inst) < 40 else TEXT_GRAY
            text = self.font_small.render(inst, True, color)
            self.screen.blit(text, (inst_x, inst_y))
            inst_y += 30
        
        # Loading indicator if needed
        if hasattr(self, 'is_loading') and self.is_loading:
            loading_text = self.font_medium.render("Loading matches...", True, HIGHLIGHT_YELLOW)
            self.screen.blit(loading_text, (inst_x, inst_y + 50))
        
        # Draw expanded dropdowns LAST (so they appear on top)
        if self.competition_dropdown.is_open:
            self.competition_dropdown.draw(self.screen)
        
        if self.season_dropdown.is_open:
            self.season_dropdown.draw(self.screen)
        
        if self.team_a_dropdown.is_open:
            self.team_a_dropdown.draw(self.screen)
        
        if self.team_b_dropdown.is_open:
            self.team_b_dropdown.draw(self.screen)
    
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
        """Draw all players."""
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
            
            # Selection ring
            if player_id == self.selected_player_id:
                pygame.draw.circle(self.screen, SELECTED_RING, (px, py), PLAYER_RADIUS + 5, 3)
            
            # Player
            pygame.draw.circle(self.screen, color, (px, py), PLAYER_RADIUS)
            pygame.draw.circle(self.screen, LINE_WHITE, (px, py), PLAYER_RADIUS, 2)
            
            # Ball indicator
            if player_state.has_ball:
                pygame.draw.circle(self.screen, HIGHLIGHT_YELLOW, (px, py), PLAYER_RADIUS + 3, 2)
            
            # Jersey number
            jersey = str(player_data.get('jersey_number', '?'))
            num_text = self.font_small.render(jersey, True, TEXT_WHITE)
            num_rect = num_text.get_rect(center=(px, py))
            self.screen.blit(num_text, num_rect)
    
    def _draw_ball(self, game_state: GameState):
        """Draw the ball."""
        if not self.pitch or not game_state.ball.in_play:
            return
        
        px, py = self.pitch.statsbomb_to_pixels(game_state.ball.x, game_state.ball.y)
        px += SIDEBAR_WIDTH
        py += 100
        
        pygame.draw.circle(self.screen, (50, 50, 50), (px + 2, py + 2), BALL_RADIUS)
        pygame.draw.circle(self.screen, BALL_COLOR, (px, py), BALL_RADIUS)
    
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
        """Draw right stats panel."""
        panel_x = SIDEBAR_WIDTH + PITCH_WIDTH_PX
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, 0, STATS_PANEL_WIDTH, SCREEN_HEIGHT))
        
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
    
    def handle_menu_event(self, event) -> bool:
        """Handle menu events. Returns should_start."""
        # Handle dropdowns
        self.competition_dropdown.handle_event(event)
        self.season_dropdown.handle_event(event)
        self.team_a_dropdown.handle_event(event)
        self.team_b_dropdown.handle_event(event)
        
        # Handle start button
        if self.start_button.handle_event(event):
            # Will be handled by main.py with match_id lookup
            return True
        
        return False
    
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