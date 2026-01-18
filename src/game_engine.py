"""
Game Engine Module

Handles the core simulation logic:
- Event timeline management
- Player position interpolation
- Game state tracking
- Animation frame generation

Key Concepts:
- Events are discrete moments (pass at 45.2s, shot at 67.8s)
- We interpolate smooth movement between events
- Game state tracks current score, possession, time
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from kloppy.domain import Dataset, Event, EventType, Team, Player

# Import MatchState wrapper (lazy to avoid circular imports)
_match_state_module = None

def _get_match_state_class():
    """Lazy import to avoid circular dependency."""
    global _match_state_module
    if _match_state_module is None:
        from src import match_state as _match_state_module
    return _match_state_module.MatchState, _match_state_module.MatchHistory


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class PlayerState:
    """
    Represents a player's state at a specific moment.
    """
    player_id: str
    x: float              # X coordinate (0-120 in StatsBomb)
    y: float              # Y coordinate (0-80 in StatsBomb)
    has_ball: bool = False
    is_active: bool = True  # False if substituted off
    
    
@dataclass
class BallState:
    """
    Represents the ball's state at a specific moment.
    """
    x: float
    y: float
    z: float = 0.0        # Height (for aerial balls)
    in_play: bool = True
    

@dataclass
class GameState:
    """
    Complete game state at any moment in time.
    """
    timestamp: float               # Current time in seconds
    period: int                    # 1 or 2 (first/second half)
    score_home: int
    score_away: int
    possession_team: Optional[str] # Team ID with possession
    players: Dict[str, PlayerState]  # player_id -> PlayerState
    ball: BallState
    last_event: Optional[Event] = None
    

class AnimationPhase(Enum):
    """
    Different phases of animation between events.
    """
    IDLE = "idle"           # No animation, static positions
    MOVING = "moving"       # Players moving to positions
    EVENT = "event"         # Event happening (shot, pass)
    

# ============================================================================
# GAME ENGINE CLASS
# ============================================================================

class GameEngine:
    """
    Main game engine that processes events and generates animation frames.
    
    Workflow:
    1. Load all events from dataset
    2. For each event, determine player positions
    3. Interpolate smooth movement between events
    4. Generate 60 FPS animation frames
    """
    
    def __init__(self, dataset: Dataset):
        """
        Initialize the game engine with match data.
        
        Args:
            dataset: Kloppy Dataset containing all match events
        """
        self.dataset = dataset
        
        # Convert events to list - kloppy returns a Frame object
        # We need to iterate through it to get actual events
        self.events = []
        try:
            for event in dataset.events:
                self.events.append(event)
        except Exception as e:
            print(f"Warning: Could not iterate events: {e}")
            # Fallback: try to access events directly
            if hasattr(dataset, 'events') and hasattr(dataset.events, '__iter__'):
                self.events = list(dataset.events)
            else:
                self.events = []
        
        self.teams = dataset.metadata.teams
        
        # OPTIMIZATION: Cache player metadata FIRST
        # This is required for _get_default_position which is called by _initialize_game_state
        self.player_metadata_cache = {}
        self._cache_player_data()
        
        # Current playback state
        self.current_event_index = 0
        self.current_timestamp = 0.0
        self.playback_speed = 1.0  # 1.0 = real-time, 2.0 = 2x speed
        
        # Animation state
        self.animation_phase = AnimationPhase.IDLE
        self.interpolation_progress = 0.0  # 0.0 to 1.0
        
        # Game state
        self.current_state = self._initialize_game_state()
        self.previous_state = None  # For interpolation
        
        # Period offsets for continuous time
        self.period_offsets = {
            1: 0.0,
            2: 45.0 * 60.0,
            3: 90.0 * 60.0,
            4: 105.0 * 60.0,
            5: 120.0 * 60.0
        }
        
        # Player tracking
        self.player_positions = self._build_position_timeline()
        self.ball_positions = self._build_ball_timeline()
        
        # Team IDs for logic
        self.home_team_id = self.teams[0].team_id
        self.away_team_id = self.teams[1].team_id
        
        # MatchState wrapper for ML/replay features
        self._match_state = None
        self._match_history = None
        self._init_match_state()
        
        print(f"[+] Game Engine initialized")
        print(f"  * {len(self.events)} events to process")
        print(f"  * {len(self.player_positions)} players tracked")
        print(f"  * MatchState wrapper initialized")
        print(f"  * Cached metadata for {len(self.player_metadata_cache)} players")
        
    def _cache_player_data(self):
        """Builds a fast lookup cache for player team and default positions."""
        # Detect collisions: (x, y) -> count of players there
        occupied_positions = {}

        for team in self.teams:
            for player in team.players:
                # Resolve position name once
                pos_name = "Unknown"
                if player.position:
                     pos_name = player.position.name
                     
                is_home = (team.team_id == self.teams[0].team_id)
                base_x, base_y = self._calculate_base_coordinates(pos_name, is_home)
                
                # FIX: Check for collisions and spread out
                pos_key = (round(base_x, 1), round(base_y, 1))
                if pos_key in occupied_positions:
                    count = occupied_positions[pos_key]
                    # Spread vertically: +5, -5, +10, -10...
                    offset_y = 5.0 * ((count + 1) // 2)
                    if count % 2 == 0:
                        offset_y = -offset_y
                    
                    base_y += offset_y
                    occupied_positions[pos_key] += 1
                else:
                    occupied_positions[pos_key] = 1
                
                self.player_metadata_cache[player.player_id] = {
                    'team_id': team.team_id,
                    'is_home': is_home,
                    'base_x': base_x,
                    'base_y': base_y,
                    'name': player.name # Useful for UI too
                }

    def _init_match_state(self):
        """
        Initialize the MatchState wrapper and history tracker.
        
        This enables:
        - ML model predictions via to_vector()
        - Replay via MatchHistory
        - What-if simulations via copy()
        """
        try:
            MatchState, MatchHistory = _get_match_state_class()
            
            # Build player -> team mapping
            player_team_map = {
                pid: data['team_id'] 
                for pid, data in self.player_metadata_cache.items()
            }
            
            # Create MatchState from current GameState
            self._match_state = MatchState.from_game_state(
                self.current_state,
                home_team_id=self.home_team_id,
                away_team_id=self.away_team_id,
                player_team_map=player_team_map
            )
            
            # Initialize history tracker (1 second intervals, max 10 mins of history)
            self._match_history = MatchHistory(max_snapshots=600, interval_seconds=1.0)
            
        except Exception as e:
            print(f"Warning: Could not initialize MatchState: {e}")
            self._match_state = None
            self._match_history = None
    
    def get_match_state(self):
        """
        Get the current MatchState wrapper.
        
        Use this for:
        - ML predictions: match_state.to_vector()
        - Serialization: match_state.to_dict()
        - What-if: match_state.copy()
        
        Returns:
            MatchState or None if not initialized
        """
        return self._match_state
    
    def set_match_state(self, match_state):
        """
        Inject a MatchState for what-if simulation.
        
        Args:
            match_state: MatchState to use
        """
        self._match_state = match_state
        # Also sync the GameState from it
        if match_state is not None:
            self.current_state = match_state.to_game_state()
    
    def get_match_history(self):
        """
        Get the match history tracker.
        
        Use for replay and time-series analysis.
        
        Returns:
            MatchHistory or None
        """
        return self._match_history

    def _calculate_base_coordinates(self, position_name: str, is_home_team: bool) -> Tuple[float, float]:
        """Pure logic to get base coordinates from position name."""
        base_pos = (60.0, 40.0) # Midfield
        
        if "Goalkeeper" in position_name:
            base_pos = (5.0, 40.0)
        elif "Defender" in position_name:
            if "Left" in position_name: base_pos = (30.0, 10.0)
            elif "Right" in position_name: base_pos = (30.0, 70.0)
            elif "Center" in position_name: base_pos = (25.0, 40.0)
            else: base_pos = (25.0, 40.0)
        elif "Midfield" in position_name:
            if "Defensive" in position_name: base_pos = (45.0, 40.0)
            elif "Attacking" in position_name: base_pos = (75.0, 40.0)
            elif "Left" in position_name: base_pos = (60.0, 20.0)
            elif "Right" in position_name: base_pos = (60.0, 60.0)
            else: base_pos = (60.0, 40.0)
        elif "Wing" in position_name:
             if "Left" in position_name: base_pos = (90.0, 10.0)
             elif "Right" in position_name: base_pos = (90.0, 70.0)
        elif "Forward" in position_name or "Striker" in position_name:
            base_pos = (100.0, 40.0)
            
        if not is_home_team:
            base_pos = (120.0 - base_pos[0], 80.0 - base_pos[1])
            
        return base_pos

    def _get_default_position(self, player_id: str, team_id: str = None) -> Tuple[float, float]:
        """
        Get default tactical position.
        OPTIMIZED: Uses cache (O(1)) instead of iteration (O(N)).
        """
        if player_id in self.player_metadata_cache:
            data = self.player_metadata_cache[player_id]
            return (data['base_x'], data['base_y'])
            
        # Fallback if player not in cache (shouldn't happen for valid players)
        return (60.0, 40.0)

    def _get_tactical_position(self, player_id: str, timestamp: float) -> Tuple[float, float]:
        """
        Calculate dynamic tactical position based on ball location.
        """
        # 1. Get Base Formation Position (Optimized)
        if player_id in self.player_metadata_cache:
            data = self.player_metadata_cache[player_id]
            team_id = data['team_id']
            base_x = data['base_x']
            base_y = data['base_y']
        else:
            # Fallback (slow path)
            team_id = self.home_team_id
            for team in self.teams:
                for p in team.players:
                    if p.player_id == player_id:
                        team_id = team.team_id
                        break
            base_x, base_y = self._get_default_position(player_id, team_id)
        
        # 2. Get Ball Position
        bx, by, bz = self._interpolate_ball_position(timestamp)
        
        # 3. Calculate Shift
        # Home Team (Attacks > 120): Moves forward as Ball X increases
        # Away Team (Attacks < 0): Moves 'forward' (lower X) as Ball X decreases
        
        is_home = (team_id == self.home_team_id)
        
        # Shift Factor (how much they follow the ball)
        # 0.0 = Statue, 1.0 = Man mark ball
        x_factor = 0.6
        
        if is_home:
            # Shift relative to center (60)
            # Ball at 100 -> shift +24 (40 * 0.6)
            # Ball at 20 -> shift -24
            offset_x = (bx - 60.0) * x_factor
            
            # Goalkeepers shift less
            if base_x < 15: 
                offset_x *= 0.2
                
        else:
            # Away Team
            # Ball at 100 (Deep in def) -> Team should be high X (Back)
            # Ball at 20 (Attacking) -> Team at low X (Forward)
            # Base (flipped) is already high X.
            
            # If Ball is at 100 (Home Atk/Away Def): Away should be compressed back (High X).
            # If Ball is at 20 (Home Def/Away Atk): Away should be pushed up (Low X).
            
            # At 100, (100-60)*0.6 = +24. Add to base (High X). Correct.
            # At 20, (20-60)*0.6 = -24. Subtract from base (Low X). Correct.
            
            offset_x = (bx - 60.0) * x_factor
            
            if base_x > 105: # Goalkeeper
                 offset_x *= 0.2

        # 4. Y-Shift (Compress width slightly when defending)
        offset_y = 0.0 # TODO: Implement later for width compression
        
        # 5. Add Noise (Breathing life)
        import random
        # Pseudo-random based on time + player_id to be smooth but random-looking
        # or use simple sine waves
        seed = hash(player_id) % 1000
        noise_x = np.sin(timestamp * 1.5 + seed) * 1.5
        noise_y = np.cos(timestamp * 1.2 + seed) * 1.5
        
        return (base_x + offset_x + noise_x, base_y + offset_y + noise_y)
        
    def _get_global_time(self, event: Event) -> float:
        """Convert event period/timestamp to global match seconds."""
        t = event.timestamp
        if hasattr(t, 'total_seconds'):
            t = t.total_seconds()
            
        period = 1
        if hasattr(event, 'period'):
             # Handle integer or object with id
             if hasattr(event.period, 'id'):
                 period = event.period.id
             else:
                 period = int(event.period)
                 
        offset = self.period_offsets.get(period, 0.0)
        return offset + t

    def _initialize_game_state(self) -> GameState:
        """
        Create initial game state at kickoff.
        
        Returns:
            GameState with starting positions
        """
        # Get kickoff event (first event)
        kickoff_event = self.events[0] if self.events else None
        
        # Initialize player positions
        players = {}
        
        for team in self.teams:
            for player in team.players:
                # Default starting position (will be updated from events)
                # Home team on left, away team on right
                if team == self.teams[0]:  # Home team
                    is_home = True
                else:
                    is_home = False
                
                default_x, default_y = self._get_default_position(player.player_id, team.team_id)
                
                
                # default_y is now set by _get_default_position
                
                # FIX: Only add starters to the active state
                # Bench players will be added dynamically when they first appear in an event
                is_starter = False
                if player.player_id in self.player_metadata_cache:
                    # We can infer starter status if they have a position that isn't substiute
                    # checking player.position directly better
                    if player.position and str(player.position) != "Substitute":
                         is_starter = True
                
                # Also fallbacks
                if hasattr(player, 'starting_position') and player.starting_position:
                    if str(player.starting_position) != "Substitute":
                        is_starter = True
                elif hasattr(player, 'position') and player.position:
                     if str(player.position) != "Substitute":
                        is_starter = True
                        
                if is_starter:
                    default_x, default_y = self._get_default_position(player.player_id, team.team_id)
                    players[player.player_id] = PlayerState(
                        player_id=player.player_id,
                        x=default_x,
                        y=default_y,
                        has_ball=False,
                        is_active=True
                    )
        
        # Initial ball position (center)
        ball = BallState(x=60.0, y=40.0, z=0.0, in_play=True)
        
        return GameState(
            timestamp=0.0,
            period=1,
            score_home=0,
            score_away=0,
            possession_team=self.teams[0].team_id if self.teams else None,
            players=players,
            ball=ball
        )
    
    def _build_position_timeline(self) -> Dict[str, List[Tuple[float, float, float]]]:
        """
        Build a timeline of positions for each player from events.
        
        StatsBomb provides "freeze frames" - snapshots of all player positions
        at key moments (shots, passes, etc.)
        
        Returns:
            Dict mapping player_id to list of (timestamp, x, y) tuples
        """
        position_timeline = {}
        
        # Initialize timeline for all players
        if hasattr(self.teams, '__iter__'):
            for team in self.teams:
                if hasattr(team, 'players') and hasattr(team.players, '__iter__'):
                    for player in team.players:
                        position_timeline[player.player_id] = []
        
        for event in self.events:
            # Convert event timestamp to seconds with period offset
            event_time = self._get_global_time(event)
            
            # Get freeze frame data if available
            if hasattr(event, 'freeze_frame') and event.freeze_frame:
                try:
                    if hasattr(event.freeze_frame, 'players_coordinates'):
                         for player, point in event.freeze_frame.players_coordinates.items():
                            player_id = player.player_id
                            
                            if player_id in position_timeline:
                                # Add position snapshot
                                position_timeline[player_id].append((
                                    event_time,
                                    point.x,
                                    point.y
                                ))
                except Exception:
                    pass  # Skip if freeze frame structure is unexpected
            
            # Also track player involved in event
            if event.player:
                player_id = event.player.player_id
                if player_id in position_timeline and event.coordinates:
                    position_timeline[player_id].append((
                        event_time,
                        event.coordinates.x,
                        event.coordinates.y
                    ))
        
        return position_timeline
    
    def _build_ball_timeline(self) -> List[Tuple[float, float, float, float]]:
        """
        Build a chronologically ordered timeline of ball positions.
        Returns list of (timestamp, x, y, z).
        """
        timeline = []
        
        # Add initial center spot
        if self.events:
            start_time = self.events[0].timestamp
            if hasattr(start_time, 'total_seconds'):
                start_time = start_time.total_seconds()
            timeline.append((max(0.0, start_time - 1.0), 60.0, 40.0, 0.0))
            
        for event in self.events:
            if event.coordinates:
                t = self._get_global_time(event)
                
                # Some events have 'end_coordinates' (passes, shots)
                # We add the start point at event time
                timeline.append((t, event.coordinates.x, event.coordinates.y, 0.0))
                
                # If there's an end coordinate and duration, add the end point
                if hasattr(event, 'end_coordinates') and event.end_coordinates:
                    # Estimate duration or valid end time? 
                    # Usually next event time is better, but if it has end_coordinates it implies movement *during* event
                    # For now, let's just stick to point-to-point between events for simplicity
                    # or better: if pass, add end point at t + duration?
                    # Kloppy events might have duration
                    pass

        # Sort just in case
        timeline.sort(key=lambda x: x[0])
        return timeline

    def _interpolate_ball_position(self, timestamp: float) -> Tuple[float, float, float]:
        """Interpolate ball position at timestamp."""
        if not self.ball_positions:
            return (60.0, 40.0, 0.0)
            
        # Find surrounding positions
        # Optimization: indices could be cached/tracked if performance is issue
        before = None
        after = None
        
        # Binary search or just iterate (optimize later if needed)
        # Using simple iteration for robustness first
        for data in self.ball_positions:
            t, x, y, z = data
            if t <= timestamp:
                before = data
            if t >= timestamp:
                after = data
                break
                
        if before is None:
            return (self.ball_positions[0][1], self.ball_positions[0][2], self.ball_positions[0][3])
        if after is None:
            return (self.ball_positions[-1][1], self.ball_positions[-1][2], self.ball_positions[-1][3])
            
        t1, x1, y1, z1 = before
        t2, x2, y2, z2 = after
        
        if t2 == t1:
            return (x1, y1, z1)
            
        factor = (timestamp - t1) / (t2 - t1)
        
        # Linear interpolation
        x = x1 + (x2 - x1) * factor
        y = y1 + (y2 - y1) * factor
        z = z1 + (z2 - z1) * factor # Simple linear height for now
        
        return (x, y, z)
    
    def _interpolate_position(self, player_id: str, timestamp: float) -> Tuple[float, float]:
        """
        Interpolate player position at given timestamp.
        
        Uses linear interpolation between known positions.
        
        Args:
            player_id: Player to interpolate
            timestamp: Time to get position for
            
        Returns:
            (x, y) coordinates
        """
        positions = self.player_positions.get(player_id, [])
        
        if not positions:
            # No position data, drift relative to ball or formation?
            # For now, return default tactical position
            # We need to find team_id for this player to be accurate
            # Ideally cache player_team map
            team_id = self.teams[0].team_id # Fallback
            for team in self.teams:
                for p in team.players:
                    if p.player_id == player_id:
                        team_id = team.team_id
                        break
            return self._get_default_position(player_id, team_id)
        
        # Find surrounding positions
        before = None
        after = None
        
        for i, (t, x, y) in enumerate(positions):
            if t <= timestamp:
                before = (t, x, y)
            if t >= timestamp and after is None:
                after = (t, x, y)
                break
        
        # If no surrounding positions, return tactical
        if before is None and after is None:
            return self._get_tactical_position(player_id, timestamp)
            
        if before is None:
             # Only future data? Interpolate from tactical to future?
             # For now just use future
             return (positions[0][1], positions[0][2])
             
        if after is None:
             # Only past data?
             # Interpolate from past to tactical
             t_before, x_before, y_before = before
             
             # If it's been > 5 seconds, blend to tactical
             time_diff = timestamp - t_before
             if time_diff > 5.0:
                 tactical_x, tactical_y = self._get_tactical_position(player_id, timestamp)
                 # Blend factor (0.0 at 5s, 1.0 at 10s)
                 blend = min(1.0, (time_diff - 5.0) / 5.0)
                 x = x_before + (tactical_x - x_before) * blend
                 y = y_before + (tactical_y - y_before) * blend
                 return (x, y)
             else:
                 return (x_before, y_before)
        
        # Linear interpolation between known points
        t_before, x_before, y_before = before
        t_after, x_after, y_after = after
        
        # Check gap size
        gap = t_after - t_before
        if gap > 10.0:
            # Sparse data gap! Use tactical formation bridge
            # Start at actual data, drift to tactical, then drift back to actual data
            
            # Simple approach: Check were we are in the gap
            progress = (timestamp - t_before) / gap
            tactical_x, tactical_y = self._get_tactical_position(player_id, timestamp)
            
            # Weight: 0 at ends, 1 in middle?
            # Or blend: valid -> tactical -> valid
            if progress < 0.2:
                # Departing from valid (0.0 to 0.2) -> 0% to 100% tactical blend
                blend = progress / 0.2
                x = x_before + (tactical_x - x_before) * blend
                y = y_before + (tactical_y - y_before) * blend
            elif progress > 0.8:
                # Arriving at valid (0.8 to 1.0) -> 100% to 0% tactical blend (pure valid)
                blend = (1.0 - progress) / 0.2
                x = x_after + (tactical_x - x_after) * blend
                y = y_after + (tactical_y - y_after) * blend
            else:
                 # Middle of gap: Pure tactical
                 x, y = tactical_x, tactical_y
                 
            return (x, y)
        
        if t_after == t_before:
            return (x_before, y_before)
        
        # Interpolation factor (0.0 to 1.0)
        factor = (timestamp - t_before) / (t_after - t_before)
        
        # FIX: Use smooth interpolation instead of linear
        # This prevents robotic sliding
        factor = smooth_interpolation(0, 1, factor)
        
        x = x_before + (x_after - x_before) * factor
        y = y_before + (y_after - y_before) * factor
        
        return (x, y)
    
    def update(self, dt: float) -> GameState:
        """
        Update game state by time delta.
        
        This is called every frame (60 times per second).
        
        Args:
            dt: Delta time in seconds (typically 1/60 = 0.0167s)
            
        Returns:
            Updated GameState
        """
        # Advance time based on playback speed
        self.current_timestamp += dt * self.playback_speed
        
        # Check if we've reached next event
        if self.current_event_index < len(self.events):
            next_event = self.events[self.current_event_index]
            
            # Convert event timestamp to seconds if needed
            event_time = self._get_global_time(next_event)
            
            if self.current_timestamp >= event_time:
                # Process this event
                self._process_event(next_event)
                self.current_event_index += 1
        
        # Update player positions (interpolate)
        for player_id in self.current_state.players:
            x, y = self._interpolate_position(player_id, self.current_timestamp)
            self.current_state.players[player_id].x = x
            self.current_state.players[player_id].y = y
        
        # Update ball position (interpolate)
        bx, by, bz = self._interpolate_ball_position(self.current_timestamp)
        self.current_state.ball.x = bx
        self.current_state.ball.y = by
        self.current_state.ball.z = bz
        
        # Update state timestamp for smooth UI clock
        self.current_state.timestamp = self.current_timestamp
        
        # Sync MatchState wrapper
        if self._match_state is not None:
            self._match_state.sync_from_game_state(self.current_state)
            # Record to history (at 1 second intervals)
            if self._match_history is not None:
                self._match_history.record(self._match_state)
        
        return self.current_state
    
    def _process_event(self, event: Event):
        """
        Process a single event and update game state.
        
        Args:
            event: Event to process
        """
        self.current_state.last_event = event
        
        # Convert timestamp to seconds
        event_time = self._get_global_time(event)
        self.current_state.timestamp = event_time
        
        # Update period
        if event.period:
            self.current_state.period = event.period.id
        
        # Update score on goal events
        if event.event_type == EventType.SHOT and hasattr(event, 'result'):
            if event.result and event.result.name == 'GOAL':
                if event.team == self.teams[0]:
                    self.current_state.score_home += 1
                else:
                    self.current_state.score_away += 1
        
        # Update possession
        if event.team:
            self.current_state.possession_team = event.team.team_id
        
        # Update player with ball
        for player_state in self.current_state.players.values():
            player_state.has_ball = False
        
        if event.player:
            player_id = event.player.player_id
            if player_id in self.current_state.players:
                self.current_state.players[player_id].has_ball = True
            else:
                # FIX: Dynamically add subbed-in players
                # If a player appears in an event but isn't in state, add them now
                # Need team_id
                team_id = event.team.team_id if event.team else self.home_team_id
                
                # Get default pos (will be updated immediately by interpolation)
                def_x, def_y = self._get_default_position(player_id, team_id)
                
                self.current_state.players[player_id] = PlayerState(
                    player_id=player_id,
                    x=def_x,
                    y=def_y,
                    has_ball=True,
                    is_active=True
                )
    
    def seek_to_time(self, timestamp: float):
        """
        Jump to specific time in match.
        
        Args:
            timestamp: Time in seconds to seek to
        """
        self.current_timestamp = timestamp
        
        # Find corresponding event index
        for i, event in enumerate(self.events):
            # Convert event timestamp to seconds if it's a timedelta
            event_time = self._get_global_time(event)
            
            if event_time > timestamp:
                self.current_event_index = i
                break
        
        # Rebuild state up to this point
        self.current_state = self._initialize_game_state()
        
        for event in self.events[:self.current_event_index]:
            self._process_event(event)

        # FIX: Force position update for current timestamp
        # Otherwise players will be at "kickoff" positions for one frame, causing a "cluster" glitch
        for player_id in self.current_state.players:
            x, y = self._interpolate_position(player_id, self.current_timestamp)
            self.current_state.players[player_id].x = x
            self.current_state.players[player_id].y = y
        
        # Update ball too
        bx, by, bz = self._interpolate_ball_position(self.current_timestamp)
        self.current_state.ball.x = bx
        self.current_state.ball.y = by
        self.current_state.ball.z = bz
        
        self.current_state.timestamp = self.current_timestamp
    
    def set_playback_speed(self, speed: float):
        """
        Change playback speed.
        
        Args:
            speed: Speed multiplier (0.5 = half speed, 2.0 = double speed)
        """
        self.playback_speed = max(0.1, min(10.0, speed))
    
    def get_current_minute(self) -> int:
        """
        Get current match minute for display.
        
        Returns:
            Current minute (0-90+)
        """
        return int(self.current_timestamp / 60)
    
    def is_finished(self) -> bool:
        """
        Check if match simulation is complete.
        
        Returns:
            True if all events processed
        """
        return self.current_event_index >= len(self.events)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def smooth_interpolation(start: float, end: float, progress: float) -> float:
    """
    Ultra-smooth interpolation using quintic ease-in-out curve.
    
    This provides even smoother movement than cubic easing,
    with gentle acceleration and deceleration.
    
    Args:
        start: Starting value
        end: Ending value
        progress: Progress from 0.0 to 1.0
        
    Returns:
        Interpolated value
    """
    # Clamp progress to valid range
    progress = max(0.0, min(1.0, progress))
    
    # Quintic ease-in-out (smoother than cubic)
    if progress < 0.5:
        # Ease in: 16 * t^5
        t = 16 * (progress ** 5)
    else:
        # Ease out: 1 - (-2t + 2)^5 / 2
        t = 1 - ((-2 * progress + 2) ** 5) / 2
    
    return start + (end - start) * t


def bezier_interpolation(p0: tuple, p1: tuple, p2: tuple, t: float) -> tuple:
    """
    Quadratic Bezier interpolation for smooth curved paths.
    
    Args:
        p0: Start point (x, y)
        p1: Control point (x, y)  
        p2: End point (x, y)
        t: Progress from 0.0 to 1.0
        
    Returns:
        Interpolated (x, y) position on curve
    """
    t = max(0.0, min(1.0, t))
    inv_t = 1 - t
    
    x = inv_t * inv_t * p0[0] + 2 * inv_t * t * p1[0] + t * t * p2[0]
    y = inv_t * inv_t * p0[1] + 2 * inv_t * t * p1[1] + t * t * p2[1]
    
    return (x, y)

