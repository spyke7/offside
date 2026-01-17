"""
Renderer Module

Handles all visual rendering:
- Football pitch drawing
- Player sprites and movements
- Ball rendering
- UI elements (scoreboard, stats panel)
- Player selection and highlighting

Uses Pygame for 2D graphics and mplsoccer for pitch layout.
"""

import pygame
import numpy as np
from typing import Optional, Tuple, Dict

from src.config import *
from src.game_engine import GameState, PlayerState, BallState


# ============================================================================
# PITCH RENDERER
# ============================================================================

class PitchRenderer:
    """
    Renders the football pitch using mplsoccer layout.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize pitch renderer.
        
        Args:
            width: Pitch area width in pixels
            height: Pitch area height in pixels
        """
        self.width = width
        self.height = height
        
        # Create surface for pitch (drawn once, then reused)
        self.surface = pygame.Surface((width, height))
        
        # Draw the pitch
        self._draw_pitch()
        
    def _draw_pitch(self):
        """
        Draw the football pitch with all markings.
        
        Uses standard pitch dimensions and markings.
        """
        # Fill with green
        self.surface.fill(PITCH_GREEN)
        
        # Padding from edges
        padding = 50
        
        # Pitch boundaries (actual playing area)
        pitch_x = padding
        pitch_y = padding
        pitch_w = self.width - 2 * padding
        pitch_h = self.height - 2 * padding
        
        # Draw outer boundary
        pygame.draw.rect(self.surface, LINE_WHITE, 
                        (pitch_x, pitch_y, pitch_w, pitch_h), 3)
        
        # Center line
        center_x = pitch_x + pitch_w // 2
        pygame.draw.line(self.surface, LINE_WHITE,
                        (center_x, pitch_y),
                        (center_x, pitch_y + pitch_h), 3)
        
        # Center circle
        center_y = pitch_y + pitch_h // 2
        pygame.draw.circle(self.surface, LINE_WHITE,
                          (center_x, center_y), 
                          int(pitch_h * 0.15), 3)
        
        # Center spot
        pygame.draw.circle(self.surface, LINE_WHITE,
                          (center_x, center_y), 4)
        
        # Penalty areas
        penalty_w = pitch_w * 0.15
        penalty_h = pitch_h * 0.5
        
        # Left penalty area
        left_penalty_x = pitch_x
        left_penalty_y = center_y - penalty_h // 2
        pygame.draw.rect(self.surface, LINE_WHITE,
                        (left_penalty_x, left_penalty_y, penalty_w, penalty_h), 3)
        
        # Right penalty area
        right_penalty_x = pitch_x + pitch_w - penalty_w
        pygame.draw.rect(self.surface, LINE_WHITE,
                        (right_penalty_x, left_penalty_y, penalty_w, penalty_h), 3)
        
        # Goal areas (smaller boxes)
        goal_w = pitch_w * 0.07
        goal_h = pitch_h * 0.25
        
        # Left goal area
        left_goal_y = center_y - goal_h // 2
        pygame.draw.rect(self.surface, LINE_WHITE,
                        (pitch_x, left_goal_y, goal_w, goal_h), 3)
        
        # Right goal area
        right_goal_x = pitch_x + pitch_w - goal_w
        pygame.draw.rect(self.surface, LINE_WHITE,
                        (right_goal_x, left_goal_y, goal_w, goal_h), 3)
        
        # Penalty spots
        penalty_spot_x_left = pitch_x + penalty_w // 2
        penalty_spot_x_right = pitch_x + pitch_w - penalty_w // 2
        
        pygame.draw.circle(self.surface, LINE_WHITE,
                          (penalty_spot_x_left, center_y), 4)
        pygame.draw.circle(self.surface, LINE_WHITE,
                          (penalty_spot_x_right, center_y), 4)
        
        # Corner arcs
        arc_radius = 20
        
        # Top-left
        pygame.draw.arc(self.surface, LINE_WHITE,
                       (pitch_x - arc_radius, pitch_y - arc_radius, 
                        arc_radius * 2, arc_radius * 2),
                       0, np.pi / 2, 3)
        
        # Top-right
        pygame.draw.arc(self.surface, LINE_WHITE,
                       (pitch_x + pitch_w - arc_radius, pitch_y - arc_radius,
                        arc_radius * 2, arc_radius * 2),
                       np.pi / 2, np.pi, 3)
        
        # Bottom-left
        pygame.draw.arc(self.surface, LINE_WHITE,
                       (pitch_x - arc_radius, pitch_y + pitch_h - arc_radius,
                        arc_radius * 2, arc_radius * 2),
                       -np.pi / 2, 0, 3)
        
        # Bottom-right
        pygame.draw.arc(self.surface, LINE_WHITE,
                       (pitch_x + pitch_w - arc_radius, pitch_y + pitch_h - arc_radius,
                        arc_radius * 2, arc_radius * 2),
                       np.pi, 3 * np.pi / 2, 3)
    
    def get_surface(self) -> pygame.Surface:
        """Return the pitch surface."""
        return self.surface
    
    def statsbomb_to_pixels(self, x: float, y: float) -> Tuple[int, int]:
        """
        Convert StatsBomb coordinates (120x80) to pixel coordinates.
        
        Args:
            x: X coordinate in StatsBomb system (0-120)
            y: Y coordinate in StatsBomb system (0-80)
            
        Returns:
            (pixel_x, pixel_y) tuple
        """
        padding = 50
        
        # Scale to fit within pitch area
        pixel_x = padding + (x / PITCH_LENGTH) * (self.width - 2 * padding)
        pixel_y = padding + (y / PITCH_WIDTH_STAT) * (self.height - 2 * padding)
        
        return (int(pixel_x), int(pixel_y))


# ============================================================================
# MAIN RENDERER
# ============================================================================

class Renderer:
    """
    Main renderer that handles all visual elements.
    """
    
    def __init__(self, screen: pygame.Surface, team_a_name: str, team_b_name: str):
        """
        Initialize the renderer.
        
        Args:
            screen: Pygame screen surface
            team_a_name: Home team name
            team_b_name: Away team name
        """
        self.screen = screen
        self.team_a_name = team_a_name
        self.team_b_name = team_b_name
        
        # Create pitch renderer
        self.pitch = PitchRenderer(PITCH_WIDTH_PX, PITCH_HEIGHT_PX)
        
        # Fonts
        pygame.font.init()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Selected player
        self.selected_player_id: Optional[str] = None
        
        # Player info for display
        self.player_info: Dict[str, Dict] = {}
        
        print("[+] Renderer initialized")
    
    def set_player_info(self, player_info: Dict[str, Dict]):
        """
        Set player information for display.
        
        Args:
            player_info: Dict mapping player_id to player data
        """
        self.player_info = player_info
    
    def render(self, game_state: GameState):
        """
        Render the complete frame.
        
        Args:
            game_state: Current game state to render
        """
        # Clear screen
        self.screen.fill(BACKGROUND_DARK)
        
        # Draw pitch
        self.screen.blit(self.pitch.get_surface(), (0, 50))
        
        # Draw players
        self._draw_players(game_state)
        
        # Draw ball
        self._draw_ball(game_state)
        
        # Draw UI
        self._draw_scoreboard(game_state)
        self._draw_stats_panel(game_state)
        
        # Draw controls hint
        self._draw_controls()
    
    def _draw_players(self, game_state: GameState):
        """
        Draw all players on the pitch.
        
        Args:
            game_state: Current game state
        """
        for player_id, player_state in game_state.players.items():
            if not player_state.is_active:
                continue
            
            # Get pixel coordinates
            px, py = self.pitch.statsbomb_to_pixels(player_state.x, player_state.y)
            py += 50  # Offset for scoreboard
            
            # Determine team color
            player_data = self.player_info.get(player_id, {})
            team_name = player_data.get('team', '')
            
            if team_name == self.team_a_name:
                color = TEAM_A_COLOR
            else:
                color = TEAM_B_COLOR
            
            # Draw selection ring if selected
            if player_id == self.selected_player_id:
                pygame.draw.circle(self.screen, SELECTED_RING,
                                 (px, py), PLAYER_RADIUS + 5, 3)
            
            # Draw player circle
            pygame.draw.circle(self.screen, color, (px, py), PLAYER_RADIUS)
            pygame.draw.circle(self.screen, LINE_WHITE, (px, py), PLAYER_RADIUS, 2)
            
            # Draw ball indicator if player has ball
            if player_state.has_ball:
                pygame.draw.circle(self.screen, HIGHLIGHT_YELLOW,
                                 (px, py), PLAYER_RADIUS + 3, 2)
            
            # Draw jersey number
            jersey_no = player_data.get('jersey_number', '?')
            number_text = self.font_small.render(str(jersey_no), True, TEXT_WHITE)
            number_rect = number_text.get_rect(center=(px, py))
            self.screen.blit(number_text, number_rect)
    
    def _draw_ball(self, game_state: GameState):
        """
        Draw the ball.
        
        Args:
            game_state: Current game state
        """
        if not game_state.ball.in_play:
            return
        
        px, py = self.pitch.statsbomb_to_pixels(game_state.ball.x, game_state.ball.y)
        py += 50
        
        # Draw ball with shadow for depth
        pygame.draw.circle(self.screen, (50, 50, 50), (px + 2, py + 2), BALL_RADIUS)
        pygame.draw.circle(self.screen, BALL_COLOR, (px, py), BALL_RADIUS)
        pygame.draw.circle(self.screen, (200, 200, 200), (px, py), BALL_RADIUS, 1)
    
    def _draw_scoreboard(self, game_state: GameState):
        """
        Draw the scoreboard at the top.
        
        Args:
            game_state: Current game state
        """
        # Background
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, PITCH_WIDTH_PX, 50))
        
        # Score text
        score_text = f"{self.team_a_name} {game_state.score_home} - {game_state.score_away} {self.team_b_name}"
        score_surface = self.font_medium.render(score_text, True, TEXT_WHITE)
        score_rect = score_surface.get_rect(center=(PITCH_WIDTH_PX // 2, 25))
        self.screen.blit(score_surface, score_rect)
        
        # Time
        minute = int(game_state.timestamp / 60)
        second = int(game_state.timestamp % 60)
        time_text = f"{minute:02d}:{second:02d}"
        time_surface = self.font_small.render(time_text, True, TEXT_GRAY)
        self.screen.blit(time_surface, (20, 15))
        
        # Period
        period_text = f"{'1st' if game_state.period == 1 else '2nd'} Half"
        period_surface = self.font_small.render(period_text, True, TEXT_GRAY)
        self.screen.blit(period_surface, (PITCH_WIDTH_PX - 120, 15))
    
    def _draw_stats_panel(self, game_state: GameState):
        """
        Draw the stats panel on the right side.
        
        Args:
            game_state: Current game state
        """
        panel_x = PITCH_WIDTH_PX
        
        # Background
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT))
        
        # Title
        title = self.font_medium.render("Player Stats", True, TEXT_WHITE)
        self.screen.blit(title, (panel_x + 20, 20))
        
        # Selected player info
        if self.selected_player_id and self.selected_player_id in self.player_info:
            player = self.player_info[self.selected_player_id]
            y_offset = 70
            
            # Player name
            name_text = self.font_small.render(player.get('name', 'Unknown'), True, TEXT_WHITE)
            self.screen.blit(name_text, (panel_x + 20, y_offset))
            y_offset += 40
            
            # Stats
            stats = player.get('stats', {})
            for stat_name, stat_value in stats.items():
                stat_text = f"{stat_name}: {stat_value}"
                stat_surface = self.font_small.render(stat_text, True, TEXT_GRAY)
                self.screen.blit(stat_surface, (panel_x + 20, y_offset))
                y_offset += 30
        else:
            hint = self.font_small.render("Click a player to see stats", True, TEXT_GRAY)
            self.screen.blit(hint, (panel_x + 20, 70))
    
    def _draw_controls(self):
        """Draw control hints at the bottom."""
        controls = [
            "SPACE: Play/Pause",
            "←/→: Seek",
            "Click: Select Player"
        ]
        
        y_offset = SCREEN_HEIGHT - 80
        for control in controls:
            text = self.font_small.render(control, True, TEXT_GRAY)
            self.screen.blit(text, (20, y_offset))
            y_offset += 25
    
    def handle_click(self, pos: Tuple[int, int], game_state: GameState) -> Optional[str]:
        """
        Handle mouse click to select player.
        
        Args:
            pos: Mouse position (x, y)
            game_state: Current game state
            
        Returns:
            Selected player_id or None
        """
        mx, my = pos
        my -= 50  # Adjust for scoreboard offset
        
        for player_id, player_state in game_state.players.items():
            px, py = self.pitch.statsbomb_to_pixels(player_state.x, player_state.y)
            
            # Check if click is within player radius
            distance = ((mx - px) ** 2 + (my - py) ** 2) ** 0.5
            if distance <= PLAYER_RADIUS + 5:
                self.selected_player_id = player_id
                return player_id
        
        return None
