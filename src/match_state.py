"""
MatchState - Unified Simulation State Wrapper

This module provides a centralized state wrapper that enables:
- Fast NumPy-based access for ML models
- History/replay via deep copy
- Monte Carlo simulation
- "What-if" tactical experiments

The MatchState wraps the existing GameState without replacing it,
ensuring backward compatibility with the renderer and other modules.
"""

import numpy as np
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

# Import existing state classes for compatibility
from src.game_engine import GameState, PlayerState, BallState


@dataclass
class MatchState:
    """
    Unified match state wrapper for research-grade simulation.
    
    Provides both dictionary-based access (backward compatible)
    and NumPy array access (fast, ML-friendly).
    
    Attributes:
        time: Current match time in seconds
        period: Match period (1 = first half, 2 = second half)
        score: Tuple of (home_goals, away_goals)
        positions: NumPy array of shape (N, 2) for player/ball positions
        velocities: NumPy array of shape (N, 2) for velocities
        stamina: NumPy array of shape (N-1,) for player stamina
        team_ids: NumPy array indicating team (0=home, 1=away)
        ball_owner_idx: Index of player with ball (None if loose)
        possession_team: 0 for home, 1 for away
    """
    
    # ===== Core State =====
    time: float = 0.0
    period: int = 1
    score: Tuple[int, int] = (0, 0)
    
    # ===== NumPy Arrays =====
    # Shape: (num_players + 1, 2) - last row is ball
    positions: np.ndarray = field(default_factory=lambda: np.zeros((23, 2)))
    velocities: np.ndarray = field(default_factory=lambda: np.zeros((23, 2)))
    # Shape: (num_players,)
    stamina: np.ndarray = field(default_factory=lambda: np.ones(22))
    team_ids: np.ndarray = field(default_factory=lambda: np.array([0]*11 + [1]*11))
    
    # ===== Possession =====
    ball_owner_idx: Optional[int] = None
    possession_team: int = 0  # 0 = home, 1 = away
    
    # ===== Player Mapping =====
    # Maps player_id <-> array index
    player_id_to_idx: Dict[str, int] = field(default_factory=dict)
    idx_to_player_id: Dict[int, str] = field(default_factory=dict)
    
    # ===== Events =====
    last_event: Optional[Any] = None
    events: List[Any] = field(default_factory=list)
    
    # ===== Reference to original GameState =====
    _game_state: Optional[GameState] = field(default=None, repr=False)
    
    @property
    def ball_position(self) -> np.ndarray:
        """Get ball position (last row of positions array)."""
        return self.positions[-1]
    
    @ball_position.setter
    def ball_position(self, value: np.ndarray):
        """Set ball position."""
        self.positions[-1] = value
    
    @property
    def player_positions(self) -> np.ndarray:
        """Get only player positions (excluding ball)."""
        return self.positions[:-1]
    
    @property
    def num_players(self) -> int:
        """Number of players currently tracked."""
        return len(self.player_id_to_idx)
    
    @property
    def home_score(self) -> int:
        """Home team score."""
        return self.score[0]
    
    @property
    def away_score(self) -> int:
        """Away team score."""
        return self.score[1]
    
    # =========================================================================
    # FACTORY METHODS
    # =========================================================================
    
    @classmethod
    def from_game_state(cls, game_state: GameState, 
                        home_team_id: str = None,
                        away_team_id: str = None,
                        player_team_map: Dict[str, str] = None) -> 'MatchState':
        """
        Create MatchState from existing GameState.
        
        Args:
            game_state: Existing GameState object
            home_team_id: ID of the home team
            away_team_id: ID of the away team  
            player_team_map: Dict mapping player_id -> team_id
            
        Returns:
            New MatchState wrapping the GameState
        """
        # Build player mappings
        player_ids = list(game_state.players.keys())
        num_players = len(player_ids)
        
        player_id_to_idx = {pid: i for i, pid in enumerate(player_ids)}
        idx_to_player_id = {i: pid for i, pid in enumerate(player_ids)}
        
        # Build position array (players + ball)
        positions = np.zeros((num_players + 1, 2))
        velocities = np.zeros((num_players + 1, 2))
        stamina = np.ones(num_players)
        team_ids = np.zeros(num_players, dtype=int)
        
        # Fill player positions
        ball_owner_idx = None
        for player_id, player_state in game_state.players.items():
            idx = player_id_to_idx[player_id]
            positions[idx] = [player_state.x, player_state.y]
            
            if player_state.has_ball:
                ball_owner_idx = idx
            
            # Determine team from map if provided
            if player_team_map and player_id in player_team_map:
                team_id = player_team_map[player_id]
                if team_id == away_team_id:
                    team_ids[idx] = 1
        
        # Ball position (last row)
        positions[-1] = [game_state.ball.x, game_state.ball.y]
        
        # Determine possession
        possession_team = 0
        if game_state.possession_team == away_team_id:
            possession_team = 1
        
        return cls(
            time=game_state.timestamp,
            period=game_state.period,
            score=(game_state.score_home, game_state.score_away),
            positions=positions,
            velocities=velocities,
            stamina=stamina,
            team_ids=team_ids,
            ball_owner_idx=ball_owner_idx,
            possession_team=possession_team,
            player_id_to_idx=player_id_to_idx,
            idx_to_player_id=idx_to_player_id,
            last_event=game_state.last_event,
            _game_state=game_state
        )
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_vector(self, include_velocities: bool = False) -> np.ndarray:
        """
        Convert state to flat feature vector for ML models.
        
        Returns:
            1D numpy array with format:
            [time, period, score_home, score_away, possession,
             player1_x, player1_y, player2_x, player2_y, ...,
             ball_x, ball_y, (optional: velocities)]
        """
        features = [
            self.time / 5400.0,  # Normalize to 90 minutes
            float(self.period),
            float(self.score[0]),
            float(self.score[1]),
            float(self.possession_team)
        ]
        
        # Flatten positions
        features.extend(self.positions.flatten() / 120.0)  # Normalize to pitch size
        
        if include_velocities:
            features.extend(self.velocities.flatten())
        
        return np.array(features, dtype=np.float32)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert state to JSON-serializable dictionary.
        
        Returns:
            Dictionary representation of the state
        """
        return {
            'time': self.time,
            'period': self.period,
            'score': list(self.score),
            'positions': self.positions.tolist(),
            'velocities': self.velocities.tolist(),
            'stamina': self.stamina.tolist(),
            'team_ids': self.team_ids.tolist(),
            'ball_owner_idx': self.ball_owner_idx,
            'possession_team': self.possession_team,
            'player_id_to_idx': self.player_id_to_idx,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchState':
        """
        Create MatchState from dictionary.
        
        Args:
            data: Dictionary from to_dict()
            
        Returns:
            New MatchState
        """
        return cls(
            time=data['time'],
            period=data['period'],
            score=tuple(data['score']),
            positions=np.array(data['positions']),
            velocities=np.array(data['velocities']),
            stamina=np.array(data['stamina']),
            team_ids=np.array(data['team_ids']),
            ball_owner_idx=data['ball_owner_idx'],
            possession_team=data['possession_team'],
            player_id_to_idx=data['player_id_to_idx'],
            idx_to_player_id={int(k): v for k, v in 
                              enumerate(data['player_id_to_idx'].keys())},
        )
    
    # =========================================================================
    # COPY & SNAPSHOT
    # =========================================================================
    
    def copy(self) -> 'MatchState':
        """
        Create deep copy for replay/history.
        
        Returns:
            Independent copy of this state
        """
        return MatchState(
            time=self.time,
            period=self.period,
            score=self.score,
            positions=self.positions.copy(),
            velocities=self.velocities.copy(),
            stamina=self.stamina.copy(),
            team_ids=self.team_ids.copy(),
            ball_owner_idx=self.ball_owner_idx,
            possession_team=self.possession_team,
            player_id_to_idx=self.player_id_to_idx.copy(),
            idx_to_player_id=self.idx_to_player_id.copy(),
            last_event=self.last_event,
            events=self.events.copy(),
            # Don't copy the game_state reference
        )
    
    # =========================================================================
    # CONVERSION BACK TO GAMESTATE
    # =========================================================================
    
    def to_game_state(self) -> GameState:
        """
        Convert back to GameState for renderer compatibility.
        
        Returns:
            GameState object with current data
        """
        # If we have the original, just update it
        if self._game_state is not None:
            return self._game_state
        
        # Build players dict
        players = {}
        for idx, player_id in self.idx_to_player_id.items():
            if idx < len(self.positions) - 1:  # Exclude ball
                players[player_id] = PlayerState(
                    player_id=player_id,
                    x=float(self.positions[idx, 0]),
                    y=float(self.positions[idx, 1]),
                    has_ball=(idx == self.ball_owner_idx),
                    is_active=True
                )
        
        # Ball state
        ball = BallState(
            x=float(self.positions[-1, 0]),
            y=float(self.positions[-1, 1]),
            z=0.0,
            in_play=True
        )
        
        return GameState(
            timestamp=self.time,
            period=self.period,
            score_home=self.score[0],
            score_away=self.score[1],
            possession_team=None,  # Would need team_id mapping
            players=players,
            ball=ball,
            last_event=self.last_event
        )
    
    # =========================================================================
    # SYNC WITH GAMESTATE
    # =========================================================================
    
    def sync_from_game_state(self, game_state: GameState):
        """
        Update this MatchState from a GameState.
        
        Call this during GameEngine.update() to keep MatchState in sync.
        
        Args:
            game_state: The current GameState from game engine
        """
        self.time = game_state.timestamp
        self.period = game_state.period
        self.score = (game_state.score_home, game_state.score_away)
        self.last_event = game_state.last_event
        
        # Update player positions
        self.ball_owner_idx = None
        for player_id, player_state in game_state.players.items():
            if player_id not in self.player_id_to_idx:
                # New player (substitute) - add to arrays
                new_idx = len(self.player_id_to_idx)
                self.player_id_to_idx[player_id] = new_idx
                self.idx_to_player_id[new_idx] = player_id
                
                # Expand arrays
                self.positions = np.vstack([
                    self.positions[:-1],  # Players
                    [[player_state.x, player_state.y]],  # New player
                    [self.positions[-1]]  # Ball (last)
                ])
                self.velocities = np.vstack([
                    self.velocities[:-1],
                    [[0.0, 0.0]],
                    [self.velocities[-1]]
                ])
                self.stamina = np.append(self.stamina, 1.0)
                self.team_ids = np.append(self.team_ids, 0)  # Default home
            
            idx = self.player_id_to_idx[player_id]
            
            # Calculate velocity from position change
            old_pos = self.positions[idx].copy()
            new_pos = np.array([player_state.x, player_state.y])
            self.velocities[idx] = new_pos - old_pos
            
            # Update position
            self.positions[idx] = new_pos
            
            if player_state.has_ball:
                self.ball_owner_idx = idx
        
        # Update ball position
        self.positions[-1] = [game_state.ball.x, game_state.ball.y]
        
        # Store reference
        self._game_state = game_state
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_player_position(self, player_id: str) -> Optional[np.ndarray]:
        """Get position of a specific player."""
        if player_id in self.player_id_to_idx:
            return self.positions[self.player_id_to_idx[player_id]]
        return None
    
    def set_player_position(self, player_id: str, x: float, y: float):
        """Set position of a specific player."""
        if player_id in self.player_id_to_idx:
            idx = self.player_id_to_idx[player_id]
            self.positions[idx] = [x, y]
    
    def get_team_positions(self, team: int) -> np.ndarray:
        """
        Get all positions for a team.
        
        Args:
            team: 0 for home, 1 for away
            
        Returns:
            Array of (x, y) positions for team players
        """
        mask = self.team_ids == team
        return self.player_positions[mask]
    
    def distance_to_ball(self, player_idx: int) -> float:
        """Calculate distance from a player to the ball."""
        player_pos = self.positions[player_idx]
        ball_pos = self.ball_position
        return float(np.linalg.norm(player_pos - ball_pos))
    
    def closest_player_to_ball(self) -> int:
        """Find index of player closest to ball."""
        distances = np.linalg.norm(self.player_positions - self.ball_position, axis=1)
        return int(np.argmin(distances))
    
    def __repr__(self) -> str:
        return (f"MatchState(time={self.time:.1f}, period={self.period}, "
                f"score={self.score}, players={self.num_players})")


# =============================================================================
# HISTORY TRACKER
# =============================================================================

class MatchHistory:
    """
    Tracks match state history for replay and analysis.
    
    Usage:
        history = MatchHistory(max_snapshots=1000)
        
        # During simulation
        history.record(match_state)
        
        # For replay
        for state in history.iter_states():
            render(state)
    """
    
    def __init__(self, max_snapshots: int = 1000, interval_seconds: float = 1.0):
        """
        Initialize history tracker.
        
        Args:
            max_snapshots: Maximum number of snapshots to keep
            interval_seconds: Minimum time between snapshots
        """
        self.max_snapshots = max_snapshots
        self.interval = interval_seconds
        self.snapshots: List[MatchState] = []
        self.last_snapshot_time = -float('inf')
    
    def record(self, state: MatchState, force: bool = False) -> bool:
        """
        Record a state snapshot if interval has passed.
        
        Args:
            state: Current MatchState
            force: If True, record regardless of interval
            
        Returns:
            True if snapshot was recorded
        """
        if not force and state.time - self.last_snapshot_time < self.interval:
            return False
        
        # Make a copy
        snapshot = state.copy()
        self.snapshots.append(snapshot)
        self.last_snapshot_time = state.time
        
        # Trim if over max
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)
        
        return True
    
    def get_state_at_time(self, time: float) -> Optional[MatchState]:
        """Get closest snapshot to given time."""
        if not self.snapshots:
            return None
        
        closest = min(self.snapshots, key=lambda s: abs(s.time - time))
        return closest.copy()
    
    def iter_states(self):
        """Iterate over all recorded states."""
        for state in self.snapshots:
            yield state.copy()
    
    def clear(self):
        """Clear all snapshots."""
        self.snapshots.clear()
        self.last_snapshot_time = -float('inf')
    
    def __len__(self) -> int:
        return len(self.snapshots)
