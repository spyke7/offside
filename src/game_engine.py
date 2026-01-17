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
        
        # Player tracking
        self.player_positions = self._build_position_timeline()
        
        print(f"[+] Game Engine initialized")
        print(f"  * {len(self.events)} events to process")
        print(f"  * {len(self.player_positions)} players tracked")
        
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
                    default_x = 40.0
                else:
                    default_x = 80.0
                
                default_y = 40.0  # Center of pitch
                
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
            # Convert event timestamp to seconds
            event_time = event.timestamp
            if hasattr(event_time, 'total_seconds'):
                event_time = event_time.total_seconds()
            
            # Get freeze frame data if available
            if hasattr(event, 'freeze_frame') and event.freeze_frame:
                try:
                    for freeze_player in event.freeze_frame:
                        player_id = freeze_player.player.player_id
                        
                        if player_id in position_timeline:
                            # Add position snapshot
                            position_timeline[player_id].append((
                                event_time,
                                freeze_player.coordinates.x,
                                freeze_player.coordinates.y
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
            # No position data, return default
            return (60.0, 40.0)
        
        # Find surrounding positions
        before = None
        after = None
        
        for i, (t, x, y) in enumerate(positions):
            if t <= timestamp:
                before = (t, x, y)
            if t >= timestamp and after is None:
                after = (t, x, y)
                break
        
        # If no surrounding positions, use closest
        if before is None:
            return (positions[0][1], positions[0][2])
        if after is None:
            return (positions[-1][1], positions[-1][2])
        
        # Linear interpolation
        t_before, x_before, y_before = before
        t_after, x_after, y_after = after
        
        if t_after == t_before:
            return (x_before, y_before)
        
        # Interpolation factor (0.0 to 1.0)
        factor = (timestamp - t_before) / (t_after - t_before)
        
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
            event_time = next_event.timestamp
            if hasattr(event_time, 'total_seconds'):
                event_time = event_time.total_seconds()
            
            if self.current_timestamp >= event_time:
                # Process this event
                self._process_event(next_event)
                self.current_event_index += 1
        
        # Update player positions (interpolate)
        for player_id in self.current_state.players:
            x, y = self._interpolate_position(player_id, self.current_timestamp)
            self.current_state.players[player_id].x = x
            self.current_state.players[player_id].y = y
        
        # Update ball position (follows last event)
        if self.current_state.last_event and self.current_state.last_event.coordinates:
            self.current_state.ball.x = self.current_state.last_event.coordinates.x
            self.current_state.ball.y = self.current_state.last_event.coordinates.y
        
        return self.current_state
    
    def _process_event(self, event: Event):
        """
        Process a single event and update game state.
        
        Args:
            event: Event to process
        """
        self.current_state.last_event = event
        
        # Convert timestamp to seconds
        event_time = event.timestamp
        if hasattr(event_time, 'total_seconds'):
            event_time = event_time.total_seconds()
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
            event_time = event.timestamp
            if hasattr(event_time, 'total_seconds'):
                event_time = event_time.total_seconds()
            
            if event_time > timestamp:
                self.current_event_index = i
                break
        
        # Rebuild state up to this point
        self.current_state = self._initialize_game_state()
        
        for event in self.events[:self.current_event_index]:
            self._process_event(event)
    
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
    Smooth interpolation using ease-in-out curve.
    
    Args:
        start: Starting value
        end: Ending value
        progress: Progress from 0.0 to 1.0
        
    Returns:
        Interpolated value
    """
    # Ease-in-out cubic
    if progress < 0.5:
        t = 4 * progress ** 3
    else:
        t = 1 - (-2 * progress + 2) ** 3 / 2
    
    return start + (end - start) * t
