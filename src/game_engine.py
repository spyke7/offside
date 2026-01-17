import pygame
import sys
from src.config import *
from src.data_loader import DataLoader
from src.renderer import Renderer

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("OffSide - Football Analytics Engine")
        self.clock = pygame.time.Clock()
        self.running = True

        self.renderer = Renderer(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.data_loader = DataLoader()
        self.events = None
        self.current_event_idx = 0

    def load_content(self):
        try:
            self.dataset = self.data_loader.load_data()
            self.events = self.dataset.events
            print(f"Loaded {len(self.events)} events.")
        except Exception as e:
            print(f"Failed to load content: {e}")
            self.events = []

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.current_event_idx = min(self.current_event_idx + 1, len(self.events) - 1)
                elif event.key == pygame.K_LEFT:
                    self.current_event_idx = max(self.current_event_idx - 1, 0)
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        pass

    def draw(self):
        self.renderer.draw_pitch()
        
        if self.events and self.current_event_idx < len(self.events):
            event = self.events[self.current_event_idx]
            
            # Simple debug visualization of event location
            # StatsBomb events have 'coordinates' attribute usually (x, y)
            if hasattr(event, 'coordinates') and event.coordinates:
                x, y = event.coordinates.x, event.coordinates.y
                screen_x, screen_y = self.renderer.to_screen_coords(x, y)
                pygame.draw.circle(self.screen, COLOR_RED, (screen_x, screen_y), 10)
                
                # Draw event info
                info = f"Event {self.current_event_idx + 1}/{len(self.events)}: {event.event_name} ({event.team})"
                self.renderer.draw_info(info)
            else:
                 info = f"Event {self.current_event_idx + 1}/{len(self.events)}: {event.event_name} (No Coords)"
                 self.renderer.draw_info(info)

        pygame.display.flip()

    def run(self):
        self.load_content()
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()
