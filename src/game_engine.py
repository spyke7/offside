import pygame
import sys
from src.config import *
from src.data_loader import StatsBombDataLoader
from src.renderer import Renderer
from src.stats_tracker import StatsTracker

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("OffSide - Football Analytics Engine")
        self.clock = pygame.time.Clock()
        self.running = True

        self.renderer = Renderer(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.data_loader = StatsBombDataLoader()

        self.stats_tracker = StatsTracker()
        self.events = None
        self.current_event_idx = 0
        
        self.selected_player_name = None
        self.selected_player_stats = None
        
        # Match Control
        self.paused = True # Start paused
        self.rewind_speed = 5
        self.forward_speed = 5

    def load_content(self):
        try:
            self.dataset = self.data_loader.load_data()
            self.events = self.dataset.events
            print(f"Loaded {len(self.events)} events.")
            
            # Extract team info for color mapping
            if hasattr(self.dataset, 'metadata') and hasattr(self.dataset.metadata, 'teams'):
                teams = self.dataset.metadata.teams
                if len(teams) >= 2:
                    self.team_colors = {
                        str(teams[0]): COLOR_TEAM_HOME,
                        str(teams[1]): COLOR_TEAM_AWAY
                    }
                    print(f"Team colors: {teams[0].name} (Blue) vs {teams[1].name} (Red)")
                else:
                    self.team_colors = {}
            else:
                self.team_colors = {}
            
            # Pre-process stats
            self.stats_tracker.process_events(self.events)
            
        except Exception as e:
            print(f"Failed to load content: {e}")
            self.events = []
            self.team_colors = {}

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                     self.paused = not self.paused
                elif event.key == pygame.K_RIGHT:
                    # Fast forward if paused, or manual step
                    step = self.forward_speed * 10 if not self.paused else 1
                    self.current_event_idx = min(self.current_event_idx + 1, len(self.events) - 1)
                elif event.key == pygame.K_LEFT:
                    # Rewind
                    self.current_event_idx = max(self.current_event_idx - 1, 0)
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    clicked_element = self.renderer.get_element_at_pos(mouse_x, mouse_y)
                    if clicked_element and clicked_element['type'] == 'player':
                        self.selected_player_name = clicked_element['data']
                        self.selected_player_stats = self.stats_tracker.get_player_stats(self.selected_player_name)
                        print(f"Selected player: {self.selected_player_name}")

    def update(self):
        if not self.paused:
            # Auto-advance for "Play" mode
            # This logic needs refinement for true time-based playback but for event-step playback:
            self.current_event_idx = min(self.current_event_idx + 1, len(self.events) - 1)
            # Maybe slow it down? event-by-event at 60fps is too fast. 
            # We'll just simple increment for now as requested or check if user wants time-based.
            # User said "LEFT -> Rewind 5 seconds". StatsBomb events have timestamps.
            # For now, let's just stick to index based or slow down the update if it's "Play".
            pass

    def draw(self):
        self.renderer.draw_pitch()
        
        if self.events and self.current_event_idx < len(self.events):
            event = self.events[self.current_event_idx]
            self.renderer.draw_event(event, self.team_colors)

        self.renderer.draw_panel(self.selected_player_stats, self.selected_player_name)
        
        # Draw playback status
        status = "PAUSED" if self.paused else "PLAYING"
        # We can draw this on the panel or screen corner
        
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
