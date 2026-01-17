"""
Elo Rating System for Football Teams
Calculates dynamic team strength based on historical match results.
"""

import pandas as pd
import numpy as np


class EloRating:
    """
    Elo rating system for football teams.
    Updates ratings after each match based on actual vs expected results.
    """
    
    def __init__(self, k_factor=32, initial_rating=1500, home_advantage=100):
        """
        Args:
            k_factor: How much ratings change per match (higher = more volatile)
            initial_rating: Starting rating for new teams
            home_advantage: Bonus added to home team's rating for expected calculation
        """
        self.k = k_factor
        self.initial_rating = initial_rating
        self.home_advantage = home_advantage
        self.ratings = {}
    
    def get_rating(self, team: str) -> float:
        """Get current rating for a team (or initial if new)."""
        return self.ratings.get(team, self.initial_rating)
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate expected score (0-1) for team A vs team B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update(self, home_team: str, away_team: str, home_goals: int, away_goals: int):
        """
        Update ratings after a match.
        
        Args:
            home_team: Name of home team
            away_team: Name of away team
            home_goals: Goals scored by home team
            away_goals: Goals scored by away team
        """
        # Get current ratings (with home advantage for expected calculation)
        home_rating = self.get_rating(home_team) + self.home_advantage
        away_rating = self.get_rating(away_team)
        
        # Calculate expected scores
        expected_home = self.expected_score(home_rating, away_rating)
        expected_away = 1 - expected_home
        
        # Actual scores (1 = win, 0.5 = draw, 0 = loss)
        if home_goals > away_goals:
            actual_home, actual_away = 1, 0
        elif home_goals < away_goals:
            actual_home, actual_away = 0, 1
        else:
            actual_home = actual_away = 0.5
        
        # Update ratings (without home advantage in stored rating)
        base_home_rating = self.get_rating(home_team)
        base_away_rating = self.get_rating(away_team)
        
        self.ratings[home_team] = base_home_rating + self.k * (actual_home - expected_home)
        self.ratings[away_team] = base_away_rating + self.k * (actual_away - expected_away)
    
    def get_elo_diff(self, home_team: str, away_team: str) -> float:
        """Get Elo rating difference (home - away) INCLUDING home advantage."""
        return (self.get_rating(home_team) + self.home_advantage) - self.get_rating(away_team)


def add_elo_features(df: pd.DataFrame, k_factor=32, initial_rating=1500, home_advantage=100) -> pd.DataFrame:
    """
    Add Elo rating features to the dataframe.
    
    IMPORTANT: This calculates Elo BEFORE each match (no leakage).
    Ratings are updated AFTER the match result is used.
    
    Args:
        df: DataFrame with match data (must have Date, HomeTeam, AwayTeam, FTHG, FTAG)
        k_factor: Elo k-factor
        initial_rating: Starting rating for teams
        home_advantage: Home field advantage in Elo points
    
    Returns:
        DataFrame with added Elo columns
    """
    df = df.copy()
    
    # Ensure sorted by date
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Initialize Elo system
    elo = EloRating(k_factor=k_factor, initial_rating=initial_rating, home_advantage=home_advantage)
    
    # Initialize columns
    df['home_elo'] = 0.0
    df['away_elo'] = 0.0
    df['elo_diff'] = 0.0  # home - away (with home advantage)
    
    for idx in range(len(df)):
        home_team = df.loc[idx, 'HomeTeam']
        away_team = df.loc[idx, 'AwayTeam']
        
        # Get ratings BEFORE the match (no leakage)
        home_rating = elo.get_rating(home_team)
        away_rating = elo.get_rating(away_team)
        
        df.loc[idx, 'home_elo'] = home_rating
        df.loc[idx, 'away_elo'] = away_rating
        df.loc[idx, 'elo_diff'] = elo.get_elo_diff(home_team, away_team)
        
        # Update ratings AFTER recording (using match result)
        home_goals = df.loc[idx, 'FTHG']
        away_goals = df.loc[idx, 'FTAG']
        elo.update(home_team, away_team, home_goals, away_goals)
    
    return df


def build_classification_features(df: pd.DataFrame, include_elo: bool = True, include_rolling: bool = True, window: int = 5) -> tuple:
    """
    Build feature set for classification (Home Win vs Not Home Win).
    
    Args:
        df: DataFrame with match data
        include_elo: Whether to include Elo rating features
        include_rolling: Whether to include rolling form features
        window: Rolling window size
    
    Returns:
        Tuple of (X, y_class, y_reg) where:
            X: Feature matrix
            y_class: Binary classification target (1=Home Win, 0=Not Home Win)
            y_reg: Regression target (goal difference)
    """
    df = df.copy()
    
    # Ensure date is datetime and sorted
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Add Elo features if requested
    if include_elo:
        df = add_elo_features(df)
    
    # Target variables
    df['goal_diff'] = df['FTHG'] - df['FTAG']
    df['home_win'] = (df['goal_diff'] > 0).astype(int)  # 1 = Home Win, 0 = Draw/Away
    
    # Base features (match stats)
    base_features = ['HS', 'AS', 'HST', 'AST', 'HC', 'AC']
    
    # Elo features
    elo_features = ['elo_diff'] if include_elo else []
    
    # Rolling form features
    rolling_features = []
    if include_rolling:
        df = _add_rolling_form_features(df, window=window)
        rolling_features = [
            'home_goals_rolling', 'home_conceded_rolling',
            'away_goals_rolling', 'away_conceded_rolling',
            'home_points_rolling', 'away_points_rolling',
            'home_win_rate', 'away_win_rate'
        ]
    
    # Combine all features
    all_features = base_features + elo_features + rolling_features
    
    X = df[all_features].copy()
    y_class = df['home_win'].copy()
    y_reg = df['goal_diff'].copy()
    
    # Fill any NaN values with column means
    X = X.fillna(X.mean())
    
    return X, y_class, y_reg


def _add_rolling_form_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Add rolling form features to dataframe."""
    
    # Initialize columns
    rolling_cols = [
        'home_goals_rolling', 'home_conceded_rolling',
        'away_goals_rolling', 'away_conceded_rolling',
        'home_points_rolling', 'away_points_rolling',
        'home_win_rate', 'away_win_rate'
    ]
    
    for col in rolling_cols:
        df[col] = np.nan
    
    for idx in range(len(df)):
        home_team = df.loc[idx, 'HomeTeam']
        away_team = df.loc[idx, 'AwayTeam']
        
        # Get previous matches for home team
        home_prev = df[(df.index < idx) & 
                       ((df['HomeTeam'] == home_team) | (df['AwayTeam'] == home_team))].tail(window)
        
        # Get previous matches for away team
        away_prev = df[(df.index < idx) & 
                       ((df['HomeTeam'] == away_team) | (df['AwayTeam'] == away_team))].tail(window)
        
        # Calculate home team stats
        if len(home_prev) > 0:
            home_goals, home_conc, home_pts, home_wins = [], [], [], 0
            for _, m in home_prev.iterrows():
                if m['HomeTeam'] == home_team:
                    home_goals.append(m['FTHG'])
                    home_conc.append(m['FTAG'])
                    if m['FTR'] == 'H': home_pts.append(3); home_wins += 1
                    elif m['FTR'] == 'D': home_pts.append(1)
                    else: home_pts.append(0)
                else:
                    home_goals.append(m['FTAG'])
                    home_conc.append(m['FTHG'])
                    if m['FTR'] == 'A': home_pts.append(3); home_wins += 1
                    elif m['FTR'] == 'D': home_pts.append(1)
                    else: home_pts.append(0)
            
            df.loc[idx, 'home_goals_rolling'] = np.mean(home_goals)
            df.loc[idx, 'home_conceded_rolling'] = np.mean(home_conc)
            df.loc[idx, 'home_points_rolling'] = np.mean(home_pts)
            df.loc[idx, 'home_win_rate'] = home_wins / len(home_prev)
        
        # Calculate away team stats
        if len(away_prev) > 0:
            away_goals, away_conc, away_pts, away_wins = [], [], [], 0
            for _, m in away_prev.iterrows():
                if m['HomeTeam'] == away_team:
                    away_goals.append(m['FTHG'])
                    away_conc.append(m['FTAG'])
                    if m['FTR'] == 'H': away_pts.append(3); away_wins += 1
                    elif m['FTR'] == 'D': away_pts.append(1)
                    else: away_pts.append(0)
                else:
                    away_goals.append(m['FTAG'])
                    away_conc.append(m['FTHG'])
                    if m['FTR'] == 'A': away_pts.append(3); away_wins += 1
                    elif m['FTR'] == 'D': away_pts.append(1)
                    else: away_pts.append(0)
            
            df.loc[idx, 'away_goals_rolling'] = np.mean(away_goals)
            df.loc[idx, 'away_conceded_rolling'] = np.mean(away_conc)
            df.loc[idx, 'away_points_rolling'] = np.mean(away_pts)
            df.loc[idx, 'away_win_rate'] = away_wins / len(away_prev)
    
    return df
