import pandas as pd

def build_features(df: pd.DataFrame):
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
