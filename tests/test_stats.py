import os
import sys

# Add src to path just in case
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.stats_tracker import StatsTracker
    from src.data_loader import DataLoader
    
    # Load data
    loader = DataLoader()
    dataset = loader.load_data()
    
    # Init tracker
    tracker = StatsTracker()
    tracker.process_events(dataset.events)
    
    # Verify we have players
    players = tracker.get_all_players()
    print(f"Found {len(players)} players.")
    
    if len(players) > 0:
        sample_player = players[0]
        stats = tracker.get_player_stats(sample_player)
        print(f"Stats for specific player: {stats}")
        # Encode for safe printing on Windows console if needed, or just print keys
        print("Player stats keys: ", list(stats.keys()))
        
    print("Stats Test Passed.")
except Exception as e:
    print(f"Test Failed: {e}")
    sys.exit(1)
