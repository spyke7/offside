from collections import defaultdict

class StatsTracker:
    def __init__(self):
        self.player_stats = defaultdict(lambda: {"passes": 0, "shots": 0, "dribbles": 0, "tackles": 0})
        self.events_processed = False

    def process_events(self, events):
        """Aggregates stats from a list of events."""
        if self.events_processed:
            return

        print("Processing events for stats...")
        for event in events:
            # Check if event has a player associated with it
            if hasattr(event, "player") and event.player:
                player_name = str(event.player) # format: "FirstName LastName"
                event_type = event.event_name.lower()
                
                # Simple string matching for event types - Kloppy events are objects but have string names
                if "pass" in event_type:
                    self.player_stats[player_name]["passes"] += 1
                elif "shot" in event_type:
                    self.player_stats[player_name]["shots"] += 1
                elif "dribble" in event_type:
                    self.player_stats[player_name]["dribbles"] += 1
                elif "tackle" in event_type or "duel" in event_type: # simplified
                     self.player_stats[player_name]["tackles"] += 1
        
        self.events_processed = True
        print("Stats processing complete.")

    def get_player_stats(self, player_name):
        """Returns a dictionary of stats for the given player."""
        if player_name in self.player_stats:
            return self.player_stats[player_name]
        return {"error": "Player not found"}

    def get_all_players(self):
        return list(self.player_stats.keys())
