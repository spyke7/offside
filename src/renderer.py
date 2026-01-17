import pygame
from src.config import *

class Renderer:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.panel_width = PANEL_WIDTH
        self.pitch_width_screen = PITCH_WIDTH
        
        # StatsBomb pitch dimensions (approx 120x80)
        self.pitch_length = 120.0
        self.pitch_width = 80.0
        
        # Scaling factors (Scale to PITCH_WIDTH only)
        self.scale_x = self.pitch_width_screen / self.pitch_length
        self.scale_y = self.height / self.pitch_width

        # Font
        self.font = pygame.font.SysFont("Arial", 18)
        self.header_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.interactive_elements = [] # Reset on each frame/draw call

    def to_screen_coords(self, x, y):
        """Converts pitch coordinates to screen coordinates."""
        # StatsBomb: (0,0) is top-left.
        screen_x = int(x * self.scale_x)
        screen_y = int(y * self.scale_y)
        return screen_x, screen_y

    def draw_pitch(self):
        """Draws the pitch background and markings."""
        # Draw Pitch Background
        pygame.draw.rect(self.screen, COLOR_GREEN, (0, 0, self.pitch_width_screen, self.height))
        
        # Draw outer boundary
        pygame.draw.rect(self.screen, COLOR_WHITE, (0, 0, self.pitch_width_screen, self.height), 2)
        
        # Center line
        mid_x, _ = self.to_screen_coords(self.pitch_length / 2, 0)
        pygame.draw.line(self.screen, COLOR_WHITE, (mid_x, 0), (mid_x, self.height), 2)
        
        # Center circle
        mid_y, _ = self.to_screen_coords(0, self.pitch_width / 2)
        center = (mid_x, int(self.height / 2))
        radius = int(9.15 * self.scale_x) # 9.15m radius approx 10 yards
        pygame.draw.circle(self.screen, COLOR_WHITE, center, radius, 2)

    def draw_event(self, event, team_colors=None):
        """Draws a visualization of a single event and tracks interactive elements."""
        self.interactive_elements = [] # clear previous
        
        # Simple debug visualization of event location
        if hasattr(event, 'coordinates') and event.coordinates:
            x, y = event.coordinates.x, event.coordinates.y
            screen_x, screen_y = self.to_screen_coords(x, y)
            
            # Determine team color
            player_color = COLOR_RED  # Default
            if hasattr(event, 'team') and event.team and team_colors:
                team_key = str(event.team)
                player_color = team_colors.get(team_key, COLOR_RED)
            
            # Draw event location
            pygame.draw.circle(self.screen, player_color, (screen_x, screen_y), 10)
            
            # Track player associated with this event
            if hasattr(event, 'player') and event.player:
                player_name = str(event.player)
                self.interactive_elements.append({
                    "type": "player",
                    "rect": pygame.Rect(screen_x - 10, screen_y - 10, 20, 20),
                    "data": player_name
                })
                
            # Draw info text (simplified)
            # info = f"Event: {event.event_name}"
            # if hasattr(event, 'player') and event.player:
            #     info += f" - {event.player}"
            # self.draw_info(info)

    def draw_panel(self, selected_player_stats, selected_player_name):
        """Draws the side panel with stats."""
        # Draw Panel Background
        panel_rect = pygame.Rect(self.pitch_width_screen, 0, self.panel_width, self.height)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect)
        
        start_x = self.pitch_width_screen + 20
        start_y = 20
        line_height = 30
        
        # Title
        title_surf = self.header_font.render("Player Stats", True, COLOR_TEXT_HEADER)
        self.screen.blit(title_surf, (start_x, start_y))
        start_y += 40
        
        if selected_player_name:
            # Player Name
            name_surf = self.font.render(f"Name: {selected_player_name}", True, COLOR_TEXT_BODY)
            self.screen.blit(name_surf, (start_x, start_y))
            start_y += line_height
            
            # Stats
            if selected_player_stats:
                for key, value in selected_player_stats.items():
                    stat_surf = self.font.render(f"{key.capitalize()}: {value}", True, COLOR_TEXT_BODY)
                    self.screen.blit(stat_surf, (start_x, start_y))
                    start_y += line_height
        else:
            hint_surf = self.font.render("Click a player to see stats", True, COLOR_TEXT_BODY)
            self.screen.blit(hint_surf, (start_x, start_y))

    def draw_info(self, info_text):
        text_surf = self.font.render(info_text, True, COLOR_BLACK)
        self.screen.blit(text_surf, (10, 10))

    def get_element_at_pos(self, x, y):
        """Returns the data of the element at the given screen coordinates."""
        for element in self.interactive_elements:
            if element["rect"].collidepoint(x, y):
                return element
        return None
