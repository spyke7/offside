"""
Main Entry Point - Complete Application
Handles menu navigation and match simulation
"""

import sys
import pygame

from src.data_loader import StatsBombDataLoader, get_player_info
from src.game_engine import GameEngine
from src.renderer import Renderer, UIState
from src.stats_tracker import StatsTracker
from src.config import *


def main():
    """Main application loop."""
    
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Football Match Simulator")
    clock = pygame.time.Clock()
    
    print("=" * 60)
    print("FOOTBALL MATCH SIMULATOR")
    print("=" * 60)
    
    # Initialize data loader and renderer
    data_loader = StatsBombDataLoader()
    renderer = Renderer(screen)
    
    # State variables
    game_engine = None
    stats_tracker = None
    paused = True
    current_matches = []
    current_competition_id = None
    current_season_id = None
    last_selected_competition = None
    last_selected_team_a = None
    last_selected_team_b = None
    all_teams = []
    
    running = True
    
    print("\n✓ Application started")
    print("Navigate using the menu to select a match\n")
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # 1. Check for competition change
        selected_comp = renderer.competition_dropdown.selected
        if selected_comp and selected_comp != last_selected_competition and selected_comp in COMPETITIONS:
            last_selected_competition = selected_comp
            current_competition_id = COMPETITIONS[selected_comp]['id']
            
            # Reset dependent dropdowns
            renderer.season_dropdown.selected_index = -1
            renderer.season_dropdown.options = []
            renderer.team_a_dropdown.selected_index = -1
            renderer.team_a_dropdown.options = []
            renderer.team_b_dropdown.selected_index = -1
            renderer.team_b_dropdown.options = []
            
            # Populate seasons
            seasons = list(COMPETITIONS[selected_comp]['seasons'].keys())
            renderer.season_dropdown.options = sorted(seasons, reverse=True)
            print(f"✓ Selected {selected_comp} (ID: {current_competition_id})")

        # 2. Check for season change (triggers match loading)
        selected_season = renderer.season_dropdown.selected
        if selected_comp and selected_season and (selected_season != current_season_id or not current_matches):
             # Map season string back to ID
            season_id = COMPETITIONS[selected_comp]['seasons'][selected_season]
            
            if season_id != current_season_id:
                current_season_id = season_id
                
                # Reset team selections
                renderer.team_a_dropdown.selected_index = -1
                renderer.team_b_dropdown.selected_index = -1
                
                # Load matches
                renderer.is_loading = True
                print(f"\n[LOADING] Fetching matches for {selected_comp} {selected_season}...")
                current_matches = data_loader.get_matches_for_competition(current_competition_id, current_season_id)
                renderer.is_loading = False
                
                if current_matches:
                    print(f"✓ Found {len(current_matches)} matches")
                    
                    # Populate teams list (master list)
                    teams = set()
                    for match in current_matches:
                        teams.add(match['home_team']['home_team_name'])
                        teams.add(match['away_team']['away_team_name'])
                    
                    all_teams = sorted(list(teams))
                    
                    # Initial population (no selections yet)
                    renderer.team_a_dropdown.options = all_teams[:]
                    renderer.team_a_dropdown.scroll_offset = 0
                    renderer.team_b_dropdown.options = all_teams[:]
                    renderer.team_b_dropdown.scroll_offset = 0
                else:
                    print("✗ No matches found")
                    all_teams = []
                    renderer.team_a_dropdown.options = []
                    renderer.team_b_dropdown.options = []

        # 3. Check for team changes (Mutual Exclusion Logic)
        selected_team_a = renderer.team_a_dropdown.selected
        selected_team_b = renderer.team_b_dropdown.selected
        
        if (selected_team_a != last_selected_team_a or selected_team_b != last_selected_team_b):
            # If selection changed, we need to re-filter options to ensure mutual exclusion
            # Capture current selections as strings
            current_a = selected_team_a
            current_b = selected_team_b
            
            # Update last selected trackers
            last_selected_team_a = current_a
            last_selected_team_b = current_b
            
            # Filter options for A (exclude B's selection)
            if current_b:
                opts_a = [t for t in all_teams if t != current_b]
            else:
                opts_a = all_teams[:]
                
            renderer.team_a_dropdown.options = opts_a
            renderer.team_a_dropdown.scroll_offset = 0
            # Restore selection for A
            if current_a in opts_a:
                renderer.team_a_dropdown.selected_index = opts_a.index(current_a)
            else:
                renderer.team_a_dropdown.selected_index = -1
            
            # Filter options for B (exclude A's selection)
            if current_a:
                opts_b = [t for t in all_teams if t != current_a]
            else:
                opts_b = all_teams[:]
                
            renderer.team_b_dropdown.options = opts_b
            renderer.team_b_dropdown.scroll_offset = 0
            # Restore selection for B
            if current_b in opts_b:
                renderer.team_b_dropdown.selected_index = opts_b.index(current_b)
            else:
                renderer.team_b_dropdown.selected_index = -1

        # 4. Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if renderer.state == UIState.SIMULATION:
                        # Go back to menu
                        renderer.state = UIState.MENU
                        game_engine = None
                        stats_tracker = None
                        paused = True
                        print("\n[MENU] Returned to menu")
                    else:
                        running = False
                
                elif renderer.state == UIState.SIMULATION and game_engine:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                        print(f"{'[PAUSED]' if paused else '[PLAYING]'}")
                    
                    elif event.key == pygame.K_LEFT:
                        new_time = max(0, game_engine.current_timestamp - 5.0)
                        game_engine.seek_to_time(new_time)
                        print(f"[<<] Seeked to {int(new_time)}s")
                    
                    elif event.key == pygame.K_RIGHT:
                        new_time = game_engine.current_timestamp + 5.0
                        game_engine.seek_to_time(new_time)
                        print(f"[>>] Seeked to {int(new_time)}s")
            
            # Handle events based on state
            if renderer.state == UIState.MENU:
                # Pass all events to menu renderer
                should_start = renderer.handle_menu_event(event)
                
                # Handle start button click
                if should_start:
                    team_a = renderer.team_a_dropdown.selected
                    team_b = renderer.team_b_dropdown.selected
                    
                    if team_a and team_b and team_a != team_b:
                        # Find match ID
                        match_id = None
                        for match in current_matches:
                            home = match['home_team']['home_team_name']
                            away = match['away_team']['away_team_name']
                            if ((home == team_a and away == team_b) or 
                                (home == team_b and away == team_a)):
                                match_id = match['match_id']
                                break
                        
                        if match_id:
                            print(f"\n[LOADING] Starting match {match_id}...")
                            dataset = data_loader.load_match(match_id)
                            
                            if dataset:
                                # Start simulation
                                team_a_name = dataset.metadata.teams[0].name
                                team_b_name = dataset.metadata.teams[1].name
                                print(f"✓ Match: {team_a_name} vs {team_b_name}")
                                
                                player_info = get_player_info(dataset)
                                stats_tracker = StatsTracker()
                                stats_tracker.process_events(dataset.events, player_info)
                                
                                for pid in player_info:
                                    player_info[pid]['stats'] = stats_tracker.get_player_stats(pid)
                                
                                game_engine = GameEngine(dataset)
                                renderer.init_simulation(team_a_name, team_b_name, player_info)
                                paused = True
                                print("✓ Simulation ready!")
                            else:
                                print("✗ Failed to load match")
                        else:
                            print(f"[!] Match not found between {team_a} and {team_b} in this season")
                    else:
                        print("[!] Please select valid teams")
            
            elif renderer.state == UIState.SIMULATION and game_engine:
                 # Handle UI controls (Play/Pause, Speed, Seek)
                 control_action = renderer.handle_control_event(event, game_engine)
                 
                 if control_action == "toggle_pause":
                     paused = not paused
                     print(f"{'[PAUSED]' if paused else '[PLAYING]'}")
                 
                 # Handle player selection (only if not interacting with controls)
                 if not control_action and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Handle player selection
                    player_id = renderer.handle_simulation_click(event.pos, game_engine.current_state)
                    if player_id:
                        player_name = renderer.player_info.get(player_id, {}).get('name', 'Unknown')
                        print(f"\n[SELECTED] {player_name}")
        
        # Update simulation
        if renderer.state == UIState.SIMULATION and game_engine and not paused:
            game_engine.update(dt)
            
            if game_engine.is_finished():
                print("\n[FINISHED] Match complete!")
                paused = True
        
        # Render
        if renderer.state == UIState.MENU:
            renderer.render()
        elif renderer.state == UIState.SIMULATION and game_engine:
            renderer.render(game_engine.current_state)
        
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    print("\nThank you for using Football Match Simulator!")
    sys.exit(0)


if __name__ == "__main__":
    main()