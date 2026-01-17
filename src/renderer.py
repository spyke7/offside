import pygame
from src.config import *

class Renderer:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        # StatsBomb pitch dimensions (approx 120x80)
        self.pitch_length = 120.0
        self.pitch_width = 80.0
        
        # Scaling factors
        self.scale_x = self.width / self.pitch_length
        self.scale_y = self.height / self.pitch_width

        # Font
        self.font = pygame.font.SysFont("Arial", 18)

    def to_screen_coords(self, x, y):
        """Converts pitch coordinates to screen coordinates."""
        # StatsBomb: (0,0) is top-left.
        screen_x = int(x * self.scale_x)
        screen_y = int(y * self.scale_y)
        return screen_x, screen_y

    def draw_pitch(self):
        """Draws the pitch background and markings."""
        self.screen.fill(COLOR_GREEN)
        
        # Draw outer boundary
        pygame.draw.rect(self.screen, COLOR_WHITE, (0, 0, self.width, self.height), 2)
        
        # Center line
        mid_x, _ = self.to_screen_coords(self.pitch_length / 2, 0)
        pygame.draw.line(self.screen, COLOR_WHITE, (mid_x, 0), (mid_x, self.height), 2)
        
        # Center circle
        mid_y, _ = self.to_screen_coords(0, self.pitch_width / 2)
        center = (mid_x, int(self.height / 2))
        radius = int(9.15 * self.scale_x) # 9.15m radius approx 10 yards
        pygame.draw.circle(self.screen, COLOR_WHITE, center, radius, 2)

    def draw_event(self, event):
        """Draws a visualization of a single event."""
        # Placeholder for event visualization
        # For now, just draw a marker at the event location if available
        pass

    def draw_frame(self, frame_data):
        """Draws players and ball from tracking data (if available)."""
        # StatsBomb data is event-based, but 360 frames might be available.
        # For this task, we might be visualizing events.
        pass
    
    def draw_info(self, info_text):
        text_surf = self.font.render(info_text, True, COLOR_BLACK)
        self.screen.blit(text_surf, (10, 10))
