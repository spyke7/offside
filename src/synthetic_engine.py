"""
Synthetic Game Engine - Simplified engine for ML-driven simulations
Uses synthetic match data instead of real StatsBomb events.
"""

import random
import math
from dataclasses import dataclass
from typing import Dict, Optional

from src.game_engine import PlayerState, BallState, GameState
from src.synthetic_match import SyntheticDataset, SyntheticEvent


class SyntheticGameEngine:
    """
    Simplified game engine for ML-driven visual simulations.
    
    Generates smooth player/ball movements based on synthetic events.
    """
    
    def __init__(self, dataset: SyntheticDataset, ml_result):
        self.dataset = dataset
        self.ml_result = ml_result
        self.events = dataset.events
        
        # Teams
        self.home_team = dataset.home_team
        self.away_team = dataset.away_team
        
        # Playback state
        self.current_timestamp = 0.0
        self.current_event_index = 0
        self.playback_speed = 1.0
        
        # Initialize game state
        self.current_state = self._initialize_game_state()
        
        # Cache player positions for interpolation
        self._player_targets = {}  # player_id -> (target_x, target_y, start_time)
        
        print(f"[+] Synthetic Engine initialized")
        print(f"  * {len(self.events)} events to process")
        print(f"  * {len(self.current_state.players)} players")
    
    def _initialize_game_state(self) -> GameState:
        """Initialize the game state with all players at starting positions."""
        players = {}
        
        # Add home team players
        for player in self.home_team.players:
            players[player.player_id] = PlayerState(
                player_id=player.player_id,
                x=player.base_x,
                y=player.base_y,
                has_ball=False,
                is_active=True
            )
        
        # Add away team players
        for player in self.away_team.players:
            players[player.player_id] = PlayerState(
                player_id=player.player_id,
                x=player.base_x,
                y=player.base_y,
                has_ball=False,
                is_active=True
            )
        
        # Ball starts at center
        ball = BallState(x=60, y=40, z=0, in_play=True)
        
        return GameState(
            timestamp=0.0,
            period=1,
            score_home=0,
            score_away=0,
            possession_team=self.home_team.team_id,
            players=players,
            ball=ball,
            last_event=None
        )
    
    def update(self, dt: float) -> GameState:
        """Update the game state by time delta."""
        self.current_timestamp += dt * self.playback_speed
        
        # Process events
        while self.current_event_index < len(self.events):
            event = self.events[self.current_event_index]
            if event.timestamp <= self.current_timestamp:
                self._process_event(event)
                self.current_event_index += 1
            else:
                break
        
        # Update player and ball positions (smooth interpolation)
        self._update_positions(dt)
        
        # Update timestamp
        self.current_state.timestamp = self.current_timestamp
        
        return self.current_state
    
    def _process_event(self, event: SyntheticEvent):
        """Process a synthetic event."""
        self.current_state.period = event.period
        self.current_state.possession_team = event.team_id
        
        # Update score on goals
        if event.event_type == 'goal':
            if event.team_id == self.home_team.team_id:
                self.current_state.score_home += 1
            else:
                self.current_state.score_away += 1
            print(f"[GOAL] {event.team_id} scores! ({self.current_state.score_home}-{self.current_state.score_away})")
        
        # Set ball position to event location
        self.current_state.ball.x = event.x
        self.current_state.ball.y = event.y
        
        # Move nearby players toward the event
        self._update_player_targets(event)
    
    def _update_player_targets(self, event: SyntheticEvent):
        """Set player movement targets based on event."""
        for player_id, player_state in self.current_state.players.items():
            # Find the player's base position
            base_x, base_y = self._get_player_base(player_id)
            
            # Determine target based on event and team
            is_possession_team = event.team_id in player_id
            
            if is_possession_team:
                # Move toward ball / attack
                offset_x = random.uniform(-15, 25)
                offset_y = random.uniform(-10, 10)
                target_x = min(115, max(5, event.x + offset_x))
                target_y = min(75, max(5, event.y + offset_y))
            else:
                # Move back toward defensive position
                offset_x = random.uniform(-10, 10)
                offset_y = random.uniform(-10, 10)
                target_x = min(115, max(5, base_x + offset_x))
                target_y = min(75, max(5, base_y + offset_y))
            
            self._player_targets[player_id] = (target_x, target_y, self.current_timestamp)
    
    def _get_player_base(self, player_id: str) -> tuple:
        """Get player's base formation position."""
        for player in self.home_team.players + self.away_team.players:
            if player.player_id == player_id:
                return player.base_x, player.base_y
        return 60, 40  # Default to center
    
    def _update_positions(self, dt: float):
        """Smoothly interpolate player positions toward targets."""
        speed = 30.0 * dt  # Movement speed
        
        for player_id, player_state in self.current_state.players.items():
            if player_id in self._player_targets:
                target_x, target_y, _ = self._player_targets[player_id]
                
                # Move toward target
                dx = target_x - player_state.x
                dy = target_y - player_state.y
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist > 1:
                    move = min(speed, dist)
                    player_state.x += (dx / dist) * move
                    player_state.y += (dy / dist) * move
    
    def seek_to_time(self, target_time: float):
        """Seek to a specific time in the simulation."""
        # Reset if seeking backwards
        if target_time < self.current_timestamp:
            self.current_event_index = 0
            self.current_timestamp = 0.0
            self.current_state = self._initialize_game_state()
        
        # Fast-forward to target time
        while self.current_timestamp < target_time:
            self.update(0.1)
    
    def is_finished(self) -> bool:
        """Check if the simulation is finished."""
        return self.current_timestamp >= 90 * 60  # 90 minutes
    
    def set_speed(self, speed: float):
        """Set playback speed."""
        self.playback_speed = speed

    def set_playback_speed(self, speed: float):
        """Compatibility method for Renderer control events.
        Delegates to set_speed()."""
        self.set_speed(speed)
