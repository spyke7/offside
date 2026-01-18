"""
ML Match Simulator - Uses trained models from laliga_ml_sandbox
Predicts match outcomes using ELO ratings and RandomForest classifier
"""

import os
import sys
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np

# Add laliga_ml_sandbox to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_SANDBOX_DIR = os.path.join(BASE_DIR, 'laliga_ml_sandbox')
sys.path.insert(0, ML_SANDBOX_DIR)

from sklearn.ensemble import RandomForestClassifier


@dataclass
class MatchEvent:
    """Represents a match event (goal, card, etc.)"""
    minute: int
    event_type: str  # 'goal', 'yellow_card', 'red_card', 'substitution'
    team: str  # 'home' or 'away'
    description: str


@dataclass
class MLMatchResult:
    """Result of ML match simulation"""
    home_team: str
    away_team: str
    
    # ELO ratings
    home_elo: float
    away_elo: float
    elo_diff: float
    
    # Predictions
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_outcome: str  # 'H', 'D', 'A'
    
    # Simulated result
    home_goals: int
    away_goals: int
    
    # Match events
    events: List[MatchEvent] = field(default_factory=list)
    
    # Form stats
    home_form: Dict = field(default_factory=dict)
    away_form: Dict = field(default_factory=dict)


class EloRating:
    """Elo rating system for football teams."""
    
    def __init__(self, k_factor=32, initial_rating=1500, home_advantage=100):
        self.k = k_factor
        self.initial_rating = initial_rating
        self.home_advantage = home_advantage
        self.ratings = {}
    
    def get_rating(self, team: str) -> float:
        return self.ratings.get(team, self.initial_rating)
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update(self, home_team: str, away_team: str, home_goals: int, away_goals: int):
        home_rating = self.get_rating(home_team) + self.home_advantage
        away_rating = self.get_rating(away_team)
        
        expected_home = self.expected_score(home_rating, away_rating)
        expected_away = 1 - expected_home
        
        if home_goals > away_goals:
            actual_home, actual_away = 1, 0
        elif home_goals < away_goals:
            actual_home, actual_away = 0, 1
        else:
            actual_home = actual_away = 0.5
        
        base_home_rating = self.get_rating(home_team)
        base_away_rating = self.get_rating(away_team)
        
        self.ratings[home_team] = base_home_rating + self.k * (actual_home - expected_home)
        self.ratings[away_team] = base_away_rating + self.k * (actual_away - expected_away)
    
    def get_elo_diff(self, home_team: str, away_team: str) -> float:
        return (self.get_rating(home_team) + self.home_advantage) - self.get_rating(away_team)


class MLSimulator:
    """ML-based match simulator using LaLiga data and trained models."""
    
    def __init__(self):
        self.df = None
        self.elo = None
        self.model = None
        self.teams = []
        self.team_stats = {}
        self._load_data()
        self._build_elo()
        self._train_model()
    
    def _load_data(self):
        """Load LaLiga match data."""
        data_path = os.path.join(ML_SANDBOX_DIR, 'data', 'LaLiga_24-25.csv')
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"LaLiga data not found at {data_path}")
        
        self.df = pd.read_csv(data_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'], dayfirst=True)
        self.df = self.df.sort_values('Date').reset_index(drop=True)
        
        # Get unique teams
        home_teams = set(self.df['HomeTeam'].unique())
        away_teams = set(self.df['AwayTeam'].unique())
        self.teams = sorted(list(home_teams | away_teams))
        
        # Calculate team stats
        self._calculate_team_stats()
        
        print(f"[ML Simulator] Loaded {len(self.df)} matches, {len(self.teams)} teams")
    
    def _calculate_team_stats(self):
        """Calculate average stats for each team."""
        for team in self.teams:
            home_matches = self.df[self.df['HomeTeam'] == team]
            away_matches = self.df[self.df['AwayTeam'] == team]
            
            # Goals scored
            home_goals = home_matches['FTHG'].mean() if len(home_matches) > 0 else 1.5
            away_goals = away_matches['FTAG'].mean() if len(away_matches) > 0 else 1.0
            
            # Goals conceded
            home_conceded = home_matches['FTAG'].mean() if len(home_matches) > 0 else 1.0
            away_conceded = away_matches['FTHG'].mean() if len(away_matches) > 0 else 1.5
            
            # Win rate
            home_wins = len(home_matches[home_matches['FTR'] == 'H'])
            away_wins = len(away_matches[away_matches['FTR'] == 'A'])
            total_matches = len(home_matches) + len(away_matches)
            win_rate = (home_wins + away_wins) / total_matches if total_matches > 0 else 0.33
            
            # Shots
            avg_shots = (home_matches['HS'].mean() + away_matches['AS'].mean()) / 2 if total_matches > 0 else 10
            
            self.team_stats[team] = {
                'home_goals_avg': home_goals,
                'away_goals_avg': away_goals,
                'home_conceded_avg': home_conceded,
                'away_conceded_avg': away_conceded,
                'win_rate': win_rate,
                'avg_shots': avg_shots
            }
    
    def _build_elo(self):
        """Build ELO ratings from historical data."""
        self.elo = EloRating()
        
        for _, match in self.df.iterrows():
            self.elo.update(
                match['HomeTeam'],
                match['AwayTeam'],
                match['FTHG'],
                match['FTAG']
            )
        
        print(f"[ML Simulator] Built ELO ratings for {len(self.elo.ratings)} teams")
    
    def _train_model(self):
        """Train a simple RandomForest classifier on the data."""
        # Build features
        X, y = [], []
        
        temp_elo = EloRating()
        
        for idx, row in self.df.iterrows():
            # Get ELO before match
            elo_diff = temp_elo.get_elo_diff(row['HomeTeam'], row['AwayTeam'])
            
            # Features: elo_diff + match stats
            features = [
                elo_diff,
                row['HS'] if pd.notna(row['HS']) else 10,
                row['AS'] if pd.notna(row['AS']) else 10,
                row['HST'] if pd.notna(row['HST']) else 4,
                row['AST'] if pd.notna(row['AST']) else 4,
                row['HC'] if pd.notna(row['HC']) else 5,
                row['AC'] if pd.notna(row['AC']) else 5
            ]
            X.append(features)
            
            # Target: home win = 1, otherwise = 0
            y.append(1 if row['FTR'] == 'H' else 0)
            
            # Update ELO after match
            temp_elo.update(row['HomeTeam'], row['AwayTeam'], row['FTHG'], row['FTAG'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X, y)
        print(f"[ML Simulator] Trained RandomForest classifier")
    
    def get_teams(self) -> List[str]:
        """Return list of available teams."""
        return self.teams
    
    def simulate_match(self, home_team: str, away_team: str) -> MLMatchResult:
        """Simulate a match between two teams using ML predictions."""
        
        if home_team not in self.teams:
            raise ValueError(f"Unknown team: {home_team}")
        if away_team not in self.teams:
            raise ValueError(f"Unknown team: {away_team}")
        
        # Get ELO ratings
        home_elo = self.elo.get_rating(home_team)
        away_elo = self.elo.get_rating(away_team)
        elo_diff = self.elo.get_elo_diff(home_team, away_team)
        
        # Get team stats for average shots etc
        home_stats = self.team_stats.get(home_team, {})
        away_stats = self.team_stats.get(away_team, {})
        
        # Generate realistic match stats
        home_shots = int(np.random.normal(home_stats.get('avg_shots', 12), 3))
        away_shots = int(np.random.normal(away_stats.get('avg_shots', 10), 3))
        home_shots_on_target = max(1, int(home_shots * random.uniform(0.3, 0.5)))
        away_shots_on_target = max(1, int(away_shots * random.uniform(0.3, 0.5)))
        home_corners = random.randint(3, 8)
        away_corners = random.randint(3, 8)
        
        # Build feature vector for prediction
        features = np.array([[
            elo_diff,
            home_shots,
            away_shots,
            home_shots_on_target,
            away_shots_on_target,
            home_corners,
            away_corners
        ]])
        
        # Get prediction probabilities
        proba = self.model.predict_proba(features)[0]
        home_win_prob = proba[1] if len(proba) > 1 else 0.5
        away_win_prob = 1 - home_win_prob
        
        # Adjust for draws (simple heuristic based on ELO closeness)
        elo_closeness = 1 - min(abs(elo_diff) / 400, 0.5)
        draw_prob = 0.25 * elo_closeness
        home_win_prob = home_win_prob * (1 - draw_prob)
        away_win_prob = away_win_prob * (1 - draw_prob)
        
        # Normalize probabilities
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total  
        away_win_prob /= total
        
        # Simulate actual result based on probabilities
        rand = random.random()
        if rand < home_win_prob:
            predicted_outcome = 'H'
        elif rand < home_win_prob + draw_prob:
            predicted_outcome = 'D'
        else:
            predicted_outcome = 'A'
        
        # Simulate goals based on outcome and team strength
        home_attack = home_stats.get('home_goals_avg', 1.5)
        away_attack = away_stats.get('away_goals_avg', 1.0)
        home_defense = home_stats.get('home_conceded_avg', 1.0)
        away_defense = away_stats.get('away_conceded_avg', 1.5)
        
        # Expected goals
        home_xg = (home_attack + away_defense) / 2 * (1 + elo_diff / 1000)
        away_xg = (away_attack + home_defense) / 2 * (1 - elo_diff / 1000)
        
        # Clamp xG
        home_xg = max(0.5, min(home_xg, 4.0))
        away_xg = max(0.3, min(away_xg, 3.5))
        
        # Generate goals using Poisson distribution
        home_goals = np.random.poisson(home_xg)
        away_goals = np.random.poisson(away_xg)
        
        # Adjust goals to match predicted outcome
        if predicted_outcome == 'H' and home_goals <= away_goals:
            home_goals = away_goals + random.randint(1, 2)
        elif predicted_outcome == 'A' and away_goals <= home_goals:
            away_goals = home_goals + random.randint(1, 2)
        elif predicted_outcome == 'D':
            home_goals = away_goals = random.choice([0, 1, 1, 2, 2])
        
        # Cap goals
        home_goals = min(home_goals, 6)
        away_goals = min(away_goals, 6)
        
        # Generate match events
        events = self._generate_events(home_team, away_team, home_goals, away_goals)
        
        # Build form stats
        home_form = {
            'goals_per_match': round(home_stats.get('home_goals_avg', 1.5), 2),
            'conceded_per_match': round(home_stats.get('home_conceded_avg', 1.0), 2),
            'win_rate': f"{home_stats.get('win_rate', 0.33)*100:.0f}%"
        }
        
        away_form = {
            'goals_per_match': round(away_stats.get('away_goals_avg', 1.0), 2),
            'conceded_per_match': round(away_stats.get('away_conceded_avg', 1.5), 2),
            'win_rate': f"{away_stats.get('win_rate', 0.33)*100:.0f}%"
        }
        
        return MLMatchResult(
            home_team=home_team,
            away_team=away_team,
            home_elo=round(home_elo, 1),
            away_elo=round(away_elo, 1),
            elo_diff=round(elo_diff, 1),
            home_win_prob=round(home_win_prob, 3),
            draw_prob=round(draw_prob, 3),
            away_win_prob=round(away_win_prob, 3),
            predicted_outcome=predicted_outcome,
            home_goals=home_goals,
            away_goals=away_goals,
            events=events,
            home_form=home_form,
            away_form=away_form
        )
    
    def _generate_events(self, home_team: str, away_team: str, 
                         home_goals: int, away_goals: int) -> List[MatchEvent]:
        """Generate realistic match events."""
        events = []
        
        # Generate goal events
        all_goal_minutes = sorted(random.sample(range(1, 91), home_goals + away_goals)
                                  if home_goals + away_goals > 0 else [])
        
        home_goal_count = 0
        away_goal_count = 0
        
        for minute in all_goal_minutes:
            if home_goal_count < home_goals and (away_goal_count >= away_goals or random.random() < 0.5):
                home_goal_count += 1
                events.append(MatchEvent(
                    minute=minute,
                    event_type='goal',
                    team='home',
                    description=f"⚽ GOAL! {home_team} scores!"
                ))
            elif away_goal_count < away_goals:
                away_goal_count += 1
                events.append(MatchEvent(
                    minute=minute,
                    event_type='goal',
                    team='away',
                    description=f"⚽ GOAL! {away_team} scores!"
                ))
        
        # Add some yellow cards
        for _ in range(random.randint(1, 4)):
            minute = random.randint(10, 85)
            team = random.choice(['home', 'away'])
            team_name = home_team if team == 'home' else away_team
            events.append(MatchEvent(
                minute=minute,
                event_type='yellow_card',
                team=team,
                description=f"🟨 Yellow card for {team_name}"
            ))
        
        # Sort by minute
        events.sort(key=lambda x: x.minute)
        
        return events


# Singleton instance
_simulator_instance = None

def get_ml_simulator() -> MLSimulator:
    """Get or create the ML simulator instance."""
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = MLSimulator()
    return _simulator_instance
