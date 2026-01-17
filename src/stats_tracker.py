"""
Stats Tracker Module - Enhanced version
Tracks comprehensive player statistics
"""

from typing import Dict, List
from collections import defaultdict
from kloppy.domain import Event, EventType


class StatsTracker:
    """Tracks and aggregates player statistics from events."""
    
    def __init__(self):
        """Initialize the stats tracker."""
        self.player_stats: Dict[str, Dict] = defaultdict(lambda: {
            'name': '',
            'team': '',
            'jersey_number': '?',
            'position': 'Unknown',
            'passes_attempted': 0,
            'passes_completed': 0,
            'shots': 0,
            'shots_on_target': 0,
            'goals': 0,
            'dribbles': 0,
            'tackles': 0,
            'interceptions': 0,
            'events': 0,
            'touches': 0
        })
        
        self.events_processed = 0
    
    def process_events(self, events: List[Event], player_info: Dict[str, Dict]):
        """Process all events and aggregate statistics."""
        print("Processing match events for statistics...")
        
        for event in events:
            if not event.player:
                continue
            
            player_id = event.player.player_id
            
            # Initialize player info if first time seeing them
            if not self.player_stats[player_id]['name'] and player_id in player_info:
                info = player_info[player_id]
                self.player_stats[player_id]['name'] = info.get('name', 'Unknown')
                self.player_stats[player_id]['team'] = info.get('team', 'Unknown')
                self.player_stats[player_id]['jersey_number'] = info.get('jersey_number', '?')
                self.player_stats[player_id]['position'] = info.get('position', 'Unknown')
            
            # Count touch
            self.player_stats[player_id]['touches'] += 1
            self.player_stats[player_id]['events'] += 1
            
            # Process by event type
            if event.event_type == EventType.PASS:
                self.player_stats[player_id]['passes_attempted'] += 1
                
                if hasattr(event, 'result') and event.result:
                    result_str = str(event.result.name).upper()
                    if 'COMPLETE' in result_str or 'SUCCESS' in result_str:
                        self.player_stats[player_id]['passes_completed'] += 1
            
            elif event.event_type == EventType.SHOT:
                self.player_stats[player_id]['shots'] += 1
                
                if hasattr(event, 'result') and event.result:
                    result_str = str(event.result.name).upper()
                    if 'GOAL' in result_str:
                        self.player_stats[player_id]['goals'] += 1
                        self.player_stats[player_id]['shots_on_target'] += 1
                    elif 'SAVED' in result_str or 'POST' in result_str:
                        self.player_stats[player_id]['shots_on_target'] += 1
            
            elif event.event_type == EventType.TAKE_ON:
                self.player_stats[player_id]['dribbles'] += 1
            
            elif event.event_type == EventType.DUEL:
                self.player_stats[player_id]['tackles'] += 1
            
            elif event.event_type == EventType.INTERCEPTION:
                self.player_stats[player_id]['interceptions'] += 1
            
            self.events_processed += 1
        
        print(f"✓ Processed {self.events_processed} events for {len(self.player_stats)} players")
    
    def get_player_stats(self, player_id: str) -> Dict:
        """Get formatted statistics for a player."""
        if player_id not in self.player_stats:
            return {}
        
        stats = dict(self.player_stats[player_id])
        
        # Calculate percentages
        if stats['passes_attempted'] > 0:
            completion = (stats['passes_completed'] / stats['passes_attempted']) * 100
            stats['pass_completion'] = f"{completion:.1f}%"
        else:
            stats['pass_completion'] = "N/A"
        
        if stats['shots'] > 0:
            accuracy = (stats['shots_on_target'] / stats['shots']) * 100
            stats['shot_accuracy'] = f"{accuracy:.1f}%"
        else:
            stats['shot_accuracy'] = "N/A"
        
        return stats