"""
Stats Tracker Module

Aggregates player statistics from match events:
- Passes (completed, attempted)
- Shots (on target, off target)
- Dribbles
- Tackles
- Interceptions
- Distance covered
"""

from typing import Dict, List
from collections import defaultdict
from kloppy.domain import Event, EventType


class StatsTracker:
    """
    Tracks and aggregates player statistics from events.
    """
    
    def __init__(self):
        """Initialize the stats tracker."""
        self.player_stats: Dict[str, Dict] = defaultdict(lambda: {
            'name': '',
            'team': '',
            'passes_attempted': 0,
            'passes_completed': 0,
            'shots': 0,
            'shots_on_target': 0,
            'dribbles': 0,
            'tackles': 0,
            'interceptions': 0,
            'events': 0,
            'distance_covered': 0.0
        })
        
        self.events_processed = 0
        
    def process_events(self, events: List[Event]):
        """
        Process all events and aggregate statistics.
        
        Args:
            events: List of match events
        """
        print("Processing events for stats...")
        
        for event in events:
            if not event.player:
                continue
                
            player_id = event.player.player_id
            player_name = event.player.name
            team_name = event.team.name if event.team else 'Unknown'
            
            # Initialize player info
            if not self.player_stats[player_id]['name']:
                self.player_stats[player_id]['name'] = player_name
                self.player_stats[player_id]['team'] = team_name
            
            # Count event
            self.player_stats[player_id]['events'] += 1
            
            # Process by event type
            event_name = str(event.event_name).lower() if hasattr(event, 'event_name') else ''
            
            if event.event_type == EventType.PASS:
                self.player_stats[player_id]['passes_attempted'] += 1
                
                # Check if pass was successful
                if hasattr(event, 'result') and event.result:
                    if 'COMPLETE' in str(event.result).upper() or 'SUCCESS' in str(event.result).upper():
                        self.player_stats[player_id]['passes_completed'] += 1
            
            elif event.event_type == EventType.SHOT:
                self.player_stats[player_id]['shots'] += 1
                
                # Check if shot was on target
                if hasattr(event, 'result') and event.result:
                    result_str = str(event.result).upper()
                    if 'GOAL' in result_str or 'SAVED' in result_str:
                        self.player_stats[player_id]['shots_on_target'] += 1
            
            elif 'dribble' in event_name:
                self.player_stats[player_id]['dribbles'] += 1
            
            elif 'tackle' in event_name or 'duel' in event_name:
                self.player_stats[player_id]['tackles'] += 1
            
            elif 'interception' in event_name:
                self.player_stats[player_id]['interceptions'] += 1
            
            self.events_processed += 1
        
        print(f"Stats processing complete. Processed {self.events_processed} events for {len(self.player_stats)} players.")
    
    def get_player_stats(self, player_id: str) -> Dict:
        """
        Get statistics for a specific player.
        
        Args:
            player_id: Player ID to get stats for
            
        Returns:
            Dictionary of player statistics
        """
        if player_id in self.player_stats:
            stats = dict(self.player_stats[player_id])
            
            # Calculate pass completion rate
            if stats['passes_attempted'] > 0:
                stats['pass_completion'] = f"{(stats['passes_completed'] / stats['passes_attempted'] * 100):.1f}%"
            else:
                stats['pass_completion'] = "N/A"
            
            # Calculate shot accuracy
            if stats['shots'] > 0:
                stats['shot_accuracy'] = f"{(stats['shots_on_target'] / stats['shots'] * 100):.1f}%"
            else:
                stats['shot_accuracy'] = "N/A"
            
            return stats
        
        return {}
    
    def get_top_players(self, stat_name: str, limit: int = 5) -> List[tuple]:
        """
        Get top players by a specific statistic.
        
        Args:
            stat_name: Name of the stat to sort by
            limit: Number of players to return
            
        Returns:
            List of (player_id, player_name, stat_value) tuples
        """
        players = []
        for player_id, stats in self.player_stats.items():
            if stat_name in stats:
                players.append((player_id, stats['name'], stats[stat_name]))
        
        # Sort by stat value (descending)
        players.sort(key=lambda x: x[2], reverse=True)
        
        return players[:limit]
    
    def print_player_stats(self, player_id: str):
        """
        Print formatted statistics for a player.
        
        Args:
            player_id: Player ID to print stats for
        """
        stats = self.get_player_stats(player_id)
        
        if not stats:
            print(f"No stats found for player {player_id}")
            return
        
        print("\n" + "=" * 50)
        print(f"PLAYER: {stats['name']}")
        print(f"TEAM: {stats['team']}")
        print("=" * 50)
        print(f"Events: {stats['events']}")
        print(f"Passes: {stats['passes_completed']}/{stats['passes_attempted']} ({stats['pass_completion']})")
        print(f"Shots: {stats['shots']} ({stats['shots_on_target']} on target, {stats['shot_accuracy']})")
        print(f"Dribbles: {stats['dribbles']}")
        print(f"Tackles: {stats['tackles']}")
        print(f"Interceptions: {stats['interceptions']}")
        print("=" * 50 + "\n")
