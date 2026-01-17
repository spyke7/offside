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
        print(f"\n✗ Error loading match data: {e}")
        print("Please check your internet connection and match ID.")
        pygame.quit()
        sys.exit(1)
    
    team_a = dataset.teams[0]
    team_b = dataset.teams[1]
    
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