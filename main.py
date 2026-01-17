"""
Main entry point for OffSide Football Analytics Engine.
"""

import pygame
import sys

from src.data_loader import StatsBombDataLoader
"""
Main Entry Point for Football Match Simulation

This file initializes the game and runs the main loop.

Usage:
    python main.py [match_id]
    
    If no match_id provided, uses default from config.py
"""

import sys
import pygame
from src.data_loader import StatsBombDataLoader
from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    DEFAULT_MATCH_ID,
    BACKGROUND_DARK
)


def main():
    pygame.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Football Match Simulation - StatsBomb Data")
    
    clock = pygame.time.Clock()
    
    print("\n" + "="*60)
    print("FOOTBALL MATCH SIMULATION")
    print("="*60)
    
    match_id = DEFAULT_MATCH_ID
    if len(sys.argv) > 1:
        try:
            match_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid match_id. Using default: {DEFAULT_MATCH_ID}")
    
    loader = StatsBombDataLoader()
    
    try:
        dataset = loader.load_match_data(match_id)
    except Exception as e:
        print(f"\n[-] Error loading match data: {e}")
        print("Please check your internet connection and match ID.")
        pygame.quit()
        sys.exit(1)
    
    team_a = dataset.metadata.teams[0]
    team_b = dataset.metadata.teams[1]
    
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    # Get final score from last period
    final_score_a = dataset.metadata.score.home if dataset.metadata.score else 0
    final_score_b = dataset.metadata.score.away if dataset.metadata.score else 0
    
    running = True
    
    print("\nSimulation window opened")
    print("Press ESC or close window to quit\n")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        screen.fill(BACKGROUND_DARK)
        
        title_text = font.render("Match Data Loaded Successfully!", True, (255, 255, 255))
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        
        # Team names and score
        match_text = f"{team_a.name} {final_score_a} - {final_score_b} {team_b.name}"
        match_surface = font.render(match_text, True, (255, 255, 255))
        screen.blit(match_surface, (SCREEN_WIDTH // 2 - match_surface.get_width() // 2, 200))
        
        # Event count
        events_text = f"Total Events: {len(dataset.events)}"
        events_surface = small_font.render(events_text, True, (180, 180, 180))
        screen.blit(events_surface, (SCREEN_WIDTH // 2 - events_surface.get_width() // 2, 300))
        
        # Instructions
        instructions = [
            "Game engine and renderer coming next!",
            "",
            "Data loaded:",
            f"  • {len(team_a.players)} players for {team_a.name}",
            f"  • {len(team_b.players)} players for {team_b.name}",
            f"  • {len(dataset.events)} match events",
            "",
            "Press ESC to quit"
        ]
        
        y_offset = 400
        for line in instructions:
            text_surface = small_font.render(line, True, (200, 200, 200))
            screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, y_offset))
            y_offset += 30
        
        # Update display
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(FPS)
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    pygame.quit()
    print("Simulation closed. Goodbye!")


if __name__ == "__main__":
    main()
from src.game_engine import GameEngine
from src.renderer import Renderer
from src.stats_tracker import StatsTracker
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


def main():
    """Main application loop."""
    
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("OffSide - Football Analytics Engine")
    clock = pygame.time.Clock()
    
    print("=" * 60)
    print("OffSide - Football Analytics Engine")
    print("=" * 60)
    
    # Load match data
    print("\n[*] Loading match data...")
    try:
        data_loader = StatsBombDataLoader()
        dataset = data_loader.load_data()
        print(f"[+] Loaded {len(dataset.events)} events")
        print(f"[+] Teams: {dataset.metadata.teams[0].name} vs {dataset.metadata.teams[1].name}")
    except Exception as e:
        print(f"[-] Failed to load data: {e}")
        pygame.quit()
        sys.exit(1)
    
    # Initialize stats tracker
    print("\n[*] Initializing stats tracker...")
    stats_tracker = StatsTracker()
    stats_tracker.process_events(dataset.events)
    
    # Initialize game engine
    print("\n[*] Initializing game engine...")
    try:
        game_engine = GameEngine(dataset)
    except Exception as e:
        print(f"[-] Failed to initialize game engine: {e}")
        pygame.quit()
        sys.exit(1)
    
    # Initialize renderer
    print("\n[*] Initializing renderer...")
    try:
        team_a_name = dataset.metadata.teams[0].name
        team_b_name = dataset.metadata.teams[1].name
        renderer = Renderer(screen, team_a_name, team_b_name)
        
        # Build player info for renderer
        player_info = {}
        for team in dataset.metadata.teams:
            for player in team.players:
                player_info[player.player_id] = {
                    'name': player.name,
                    'team': team.name,
                    'jersey_number': player.jersey_no if hasattr(player, 'jersey_no') else '?',
                    'stats': stats_tracker.get_player_stats(player.player_id)
                }
        
        renderer.set_player_info(player_info)
    except Exception as e:
        print(f"[-] Failed to initialize renderer: {e}")
        pygame.quit()
        sys.exit(1)
    
    print("\n[+] Initialization complete!")
    print("\n" + "=" * 60)
    print("CONTROLS:")
    print("  SPACE     - Play/Pause")
    print("  <-/->     - Seek backward/forward")
    print("  Click     - Select player")
    print("  ESC       - Quit")
    print("=" * 60 + "\n")
    
    # Game state
    paused = True
    running = True
    
    # Main game loop
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    print(f"{'[PAUSED]' if paused else '[PLAYING]'}")
                elif event.key == pygame.K_LEFT:
                    # Seek backward 5 seconds
                    new_time = max(0, game_engine.current_timestamp - 5.0)
                    game_engine.seek_to_time(new_time)
                    print(f"[<<] Seeked to {int(new_time)}s")
                elif event.key == pygame.K_RIGHT:
                    # Seek forward 5 seconds
                    new_time = game_engine.current_timestamp + 5.0
                    game_engine.seek_to_time(new_time)
                    print(f"[>>] Seeked to {int(new_time)}s")
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    player_id = renderer.handle_click(event.pos, game_engine.current_state)
                    if player_id:
                        player_name = player_info.get(player_id, {}).get('name', 'Unknown')
                        print(f"\n[SELECTED] {player_name}")
                        # Print stats to console
                        stats_tracker.print_player_stats(player_id)
        
        # Update game state
        if not paused:
            game_engine.update(dt)
            
            # Check if match is finished
            if game_engine.is_finished():
                print("\n[FINISHED] Match complete!")
                paused = True
        
        # Render
        renderer.render(game_engine.current_state)
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    print("\nThanks for using OffSide!")
    sys.exit(0)


if __name__ == "__main__":
    main()
    game = GameEngine()
    game.run()
