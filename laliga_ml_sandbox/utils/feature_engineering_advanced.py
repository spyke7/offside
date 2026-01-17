import pandas as pd
import numpy as np


def add_rolling_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Add rolling average features for each team based on their historical performance.
    
    Args:
        df: DataFrame with match data (must be sorted by date)
        window: Number of previous matches to consider
    
    Returns:
        DataFrame with additional rolling feature columns
    """
    df = df.copy()
    
    # Ensure data is sorted by date
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Initialize feature columns
    rolling_features = [
        'home_goals_rolling', 'home_conceded_rolling',
        'away_goals_rolling', 'away_conceded_rolling',
        'home_shots_rolling', 'away_shots_rolling',
        'home_sot_rolling', 'away_sot_rolling',
        'home_corners_rolling', 'away_corners_rolling',
        'home_points_rolling', 'away_points_rolling'
    ]
    
    for feat in rolling_features:
        df[feat] = np.nan
    
    # Get unique teams
    teams = pd.concat([df['HomeTeam'], df['AwayTeam']]).unique()
    
    # For each match, calculate rolling stats from PREVIOUS matches only
    for idx in range(len(df)):
        home_team = df.loc[idx, 'HomeTeam']
        away_team = df.loc[idx, 'AwayTeam']
        current_date = df.loc[idx, 'Date']
        
        # Get previous matches for home team (before current match)
        home_prev = df[(df.index < idx) & 
                       ((df['HomeTeam'] == home_team) | (df['AwayTeam'] == home_team))].tail(window)
        
        # Get previous matches for away team (before current match)
        away_prev = df[(df.index < idx) & 
                       ((df['HomeTeam'] == away_team) | (df['AwayTeam'] == away_team))].tail(window)
        
        # Calculate home team rolling stats
        if len(home_prev) > 0:
            home_goals = []
            home_conceded = []
            home_shots = []
            home_sot = []
            home_corners = []
            home_points = []
            
            for _, match in home_prev.iterrows():
                if match['HomeTeam'] == home_team:
                    # Home team was playing at home
                    home_goals.append(match['FTHG'])
                    home_conceded.append(match['FTAG'])
                    home_shots.append(match['HS'])
                    home_sot.append(match['HST'])
                    home_corners.append(match['HC'])
                    # Points: 3 for win, 1 for draw, 0 for loss
                    if match['FTR'] == 'H':
                        home_points.append(3)
                    elif match['FTR'] == 'D':
                        home_points.append(1)
                    else:
                        home_points.append(0)
                else:
                    # Home team was playing away
                    home_goals.append(match['FTAG'])
                    home_conceded.append(match['FTHG'])
                    home_shots.append(match['AS'])
                    home_sot.append(match['AST'])
                    home_corners.append(match['AC'])
                    # Points
                    if match['FTR'] == 'A':
                        home_points.append(3)
                    elif match['FTR'] == 'D':
                        home_points.append(1)
                    else:
                        home_points.append(0)
            
            df.loc[idx, 'home_goals_rolling'] = np.mean(home_goals)
            df.loc[idx, 'home_conceded_rolling'] = np.mean(home_conceded)
            df.loc[idx, 'home_shots_rolling'] = np.mean(home_shots)
            df.loc[idx, 'home_sot_rolling'] = np.mean(home_sot)
            df.loc[idx, 'home_corners_rolling'] = np.mean(home_corners)
            df.loc[idx, 'home_points_rolling'] = np.mean(home_points)
        
        # Calculate away team rolling stats
        if len(away_prev) > 0:
            away_goals = []
            away_conceded = []
            away_shots = []
            away_sot = []
            away_corners = []
            away_points = []
            
            for _, match in away_prev.iterrows():
                if match['HomeTeam'] == away_team:
                    # Away team was playing at home
                    away_goals.append(match['FTHG'])
                    away_conceded.append(match['FTAG'])
                    away_shots.append(match['HS'])
                    away_sot.append(match['HST'])
                    away_corners.append(match['HC'])
                    # Points
                    if match['FTR'] == 'H':
                        away_points.append(3)
                    elif match['FTR'] == 'D':
                        away_points.append(1)
                    else:
                        away_points.append(0)
                else:
                    # Away team was playing away
                    away_goals.append(match['FTAG'])
                    away_conceded.append(match['FTHG'])
                    away_shots.append(match['AS'])
                    away_sot.append(match['AST'])
                    away_corners.append(match['AC'])
                    # Points
                    if match['FTR'] == 'A':
                        away_points.append(3)
                    elif match['FTR'] == 'D':
                        away_points.append(1)
                    else:
                        away_points.append(0)
            
            df.loc[idx, 'away_goals_rolling'] = np.mean(away_goals)
            df.loc[idx, 'away_conceded_rolling'] = np.mean(away_conceded)
            df.loc[idx, 'away_shots_rolling'] = np.mean(away_shots)
            df.loc[idx, 'away_sot_rolling'] = np.mean(away_sot)
            df.loc[idx, 'away_corners_rolling'] = np.mean(away_corners)
            df.loc[idx, 'away_points_rolling'] = np.mean(away_points)
    
    return df


def build_features_advanced(df: pd.DataFrame, include_rolling: bool = True) -> tuple:
    """
    Build advanced feature set with optional rolling statistics.
    
    Args:
        df: DataFrame with match data
        include_rolling: Whether to include rolling average features
    
    Returns:
        Tuple of (X, y) where X is features and y is target (goal_diff)
    """
    df = df.copy()
    
    # Convert date to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    
    # Calculate target variable
    df["goal_diff"] = df["FTHG"] - df["FTAG"]
    
    # Add rolling features if requested
    if include_rolling:
        df = add_rolling_features(df, window=5)
    
    # Define base features (current match stats)
    base_features = [
        "HS",   # Home Shots
        "AS",   # Away Shots
        "HST",  # Home Shots on Target
        "AST",  # Away Shots on Target
        "HC",   # Home Corners
        "AC"    # Away Corners
    ]
    
    # Define rolling features
    rolling_feature_names = [
        'home_goals_rolling', 'home_conceded_rolling',
        'away_goals_rolling', 'away_conceded_rolling',
        'home_shots_rolling', 'away_shots_rolling',
        'home_sot_rolling', 'away_sot_rolling',
        'home_corners_rolling', 'away_corners_rolling',
        'home_points_rolling', 'away_points_rolling'
    ]
    
    # Combine features
    if include_rolling:
        features = base_features + rolling_feature_names
    else:
        features = base_features
    
    X = df[features].copy()
    y = df["goal_diff"].copy()
    
    # Fill NaN values in rolling features with league averages (for early season matches)
    if include_rolling:
        for col in rolling_feature_names:
            if col in X.columns:
                X[col] = X[col].fillna(X[col].mean())
    
    return X, y


def build_features(df: pd.DataFrame) -> tuple:
    """
    Original simple feature builder (for backward compatibility).
    """
    df = df.copy()
    
    # Calculate goal difference using actual CSV column names
    df["goal_diff"] = df["FTHG"] - df["FTAG"]

    # Use available features from the CSV
    features = [
        "HS",   # Home Shots
        "AS",   # Away Shots
        "HST",  # Home Shots on Target
        "AST",  # Away Shots on Target
        "HC",   # Home Corners
        "AC"    # Away Corners
    ]

    X = df[features]
    y = df["goal_diff"]

    return X, y
