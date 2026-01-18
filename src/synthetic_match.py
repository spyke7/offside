"""
Synthetic Match Generator - Creates GameEngine-compatible data from ML predictions
Enables visual simulation (pitch, players, ball) driven by ML prediction results.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

# Import ML result type
from src.ml_simulator import MLMatchResult, MatchEvent


@dataclass
class SyntheticPlayer:
    """A synthetic player for the simulation."""
    player_id: str
    name: str
    team_id: str
    position: str  # GK, DEF, MID, FWD
    jersey_number: int
    base_x: float
    base_y: float


@dataclass
class SyntheticTeam:
    """A synthetic team."""
    team_id: str
    name: str
    players: List[SyntheticPlayer] = field(default_factory=list)


@dataclass
class SyntheticEvent:
    """A synthetic match event compatible with GameEngine."""
    timestamp: float  # Seconds from start
    period: int
    event_type: str  # 'pass', 'shot', 'goal', 'foul', etc.
    team_id: str
    player_id: str
    x: float
    y: float
    
    # For compatibility with kloppy Event
    def __post_init__(self):
        self.period_obj = type('Period', (), {'id': self.period})()


@dataclass
class SyntheticDataset:
    """Dataset compatible with GameEngine requirements."""
    home_team: SyntheticTeam
    away_team: SyntheticTeam
    events: List[SyntheticEvent]
    
    # For compatibility with kloppy Dataset
    @property
    def metadata(self):
        return type('Metadata', (), {'teams': [self.home_team, self.away_team]})()


# Standard 4-3-3 formation positions (StatsBomb coordinates: 0-120 x, 0-80 y)
FORMATION_433 = {
    'GK': [(5, 40)],
    'DEF': [(25, 10), (25, 30), (25, 50), (25, 70)],
    'MID': [(45, 20), (45, 40), (45, 60)],
    'FWD': [(65, 15), (65, 40), (65, 65)]
}


class SyntheticMatchGenerator:
    """
    Generates a synthetic match from ML prediction results.
    
    Creates:
    - 22 players (11 per team)
    - Events based on ML prediction (goals, cards)
    - Player position timeline
    - Ball movement based on events
    """
    
    def __init__(self):
        self.match_duration = 90 * 60  # 90 minutes in seconds
    
    def generate(self, ml_result: MLMatchResult) -> SyntheticDataset:
        """
        Generate a synthetic match from ML prediction.
        
        Args:
            ml_result: ML prediction result with teams, scores, events
            
        Returns:
            SyntheticDataset compatible with GameEngine
        """
        # Create teams
        home_team = self._create_team(ml_result.home_team, is_home=True)
        away_team = self._create_team(ml_result.away_team, is_home=False)
        
        # Generate events from ML prediction
        events = self._generate_events(ml_result, home_team, away_team)
        
        return SyntheticDataset(
            home_team=home_team,
            away_team=away_team,
            events=events
        )
    
    def _create_team(self, team_name: str, is_home: bool) -> SyntheticTeam:
        """Create a synthetic team with 11 players in 4-3-3 formation."""
        team_id = f"{'home' if is_home else 'away'}_{team_name.replace(' ', '_')}"
        
        team = SyntheticTeam(
            team_id=team_id,
            name=team_name,
            players=[]
        )
        
        # Flip coordinates for away team
        flip_x = lambda x: 120 - x if not is_home else x
        
        jersey = 1
        position_map = {0: 'GK', 1: 'DEF', 2: 'DEF', 3: 'DEF', 4: 'DEF',
                        5: 'MID', 6: 'MID', 7: 'MID',
                        8: 'FWD', 9: 'FWD', 10: 'FWD'}
        
        # Create players
        gk = FORMATION_433['GK'][0]
        team.players.append(SyntheticPlayer(
            player_id=f"{team_id}_player_{jersey}",
            name=f"GK {jersey}",
            team_id=team_id,
            position="Goalkeeper",
            jersey_number=jersey,
            base_x=flip_x(gk[0]),
            base_y=gk[1]
        ))
        jersey += 1
        
        for pos_type, positions in [('DEF', FORMATION_433['DEF']), 
                                     ('MID', FORMATION_433['MID']),
                                     ('FWD', FORMATION_433['FWD'])]:
            for x, y in positions:
                pos_name = {"DEF": "Defender", "MID": "Midfielder", "FWD": "Forward"}[pos_type]
                team.players.append(SyntheticPlayer(
                    player_id=f"{team_id}_player_{jersey}",
                    name=f"{pos_type} {jersey}",
                    team_id=team_id,
                    position=pos_name,
                    jersey_number=jersey,
                    base_x=flip_x(x),
                    base_y=y
                ))
                jersey += 1
        
        return team
    
    def _generate_events(self, ml_result: MLMatchResult, 
                         home_team: SyntheticTeam, 
                         away_team: SyntheticTeam) -> List[SyntheticEvent]:
        """Generate synthetic events from ML prediction."""
        events = []
        
        # Start event
        events.append(SyntheticEvent(
            timestamp=0.0,
            period=1,
            event_type='kickoff',
            team_id=home_team.team_id,
            player_id=home_team.players[5].player_id,  # Midfielder
            x=60, y=40
        ))
        
        # Generate passes and build-up play throughout the match
        current_time = 10.0  # Start 10 seconds in
        possession = 'home'
        
        while current_time < self.match_duration:
            # Generate a passage of play
            team = home_team if possession == 'home' else away_team
            opp_team = away_team if possession == 'home' else home_team
            
            # Pick a random attacker
            attackers = [p for p in team.players if 'Forward' in p.position or 'Midfielder' in p.position]
            player = random.choice(attackers)
            
            # Is this a goal moment?
            is_goal_moment = False
            for ml_event in ml_result.events:
                if ml_event.event_type == 'goal':
                    goal_time = ml_event.minute * 60  # Convert to seconds
                    if abs(current_time - goal_time) < 30:
                        is_goal_moment = True
                        # Generate a shot/goal
                        goal_x = 115 if possession == 'home' else 5
                        events.append(SyntheticEvent(
                            timestamp=goal_time,
                            period=1 if goal_time < 45*60 else 2,
                            event_type='goal',
                            team_id=team.team_id,
                            player_id=player.player_id,
                            x=goal_x,
                            y=40 + random.randint(-10, 10)
                        ))
                        current_time = goal_time + 60  # Skip ahead
                        break
            
            if not is_goal_moment:
                # Generate a pass
                direction = 1 if possession == 'home' else -1
                x = player.base_x + random.randint(-20, 20) * direction
                x = max(5, min(115, x))
                y = player.base_y + random.randint(-15, 15)
                y = max(5, min(75, y))
                
                events.append(SyntheticEvent(
                    timestamp=current_time,
                    period=1 if current_time < 45*60 else 2,
                    event_type='pass',
                    team_id=team.team_id,
                    player_id=player.player_id,
                    x=x, y=y
                ))
                
                # Occasionally change possession
                if random.random() < 0.15:
                    possession = 'away' if possession == 'home' else 'home'
            
            current_time += random.uniform(5, 15)  # 5-15 seconds between events
        
        # Half-time marker
        events.append(SyntheticEvent(
            timestamp=45*60,
            period=2,
            event_type='kickoff',
            team_id=away_team.team_id,
            player_id=away_team.players[5].player_id,
            x=60, y=40
        ))
        
        # Sort by time
        events.sort(key=lambda e: e.timestamp)
        
        return events


# Singleton
_generator = None

def get_synthetic_generator() -> SyntheticMatchGenerator:
    """Get or create the generator instance."""
    global _generator
    if _generator is None:
        _generator = SyntheticMatchGenerator()
    return _generator
