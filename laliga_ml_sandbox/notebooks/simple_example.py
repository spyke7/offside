"""
Simple example showing how to use the optimized model without index issues.
This can be run as a script or copied into a Jupyter notebook.
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('c:/Users/Yasin/Desktop/laliga_ml_sandbox')

from utils.feature_engineering_advanced import build_features_advanced
from utils.evaluation import evaluate_model, print_evaluation
from sklearn.linear_model import LinearRegression

# Load data
print("Loading data...")
df = pd.read_csv("c:/Users/Yasin/Desktop/laliga_ml_sandbox/data/LaLiga_24-25.csv")
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

print(f"Dataset: {len(df)} matches")
print(f"\nFirst few rows:")
print(df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].head())

# Build features with rolling averages
print("\nBuilding features with rolling averages...")
X, y = build_features_advanced(df, include_rolling=True)

print(f"\nFeatures shape: {X.shape}")
print(f"Features: {list(X.columns)}")

# Check for missing values
print(f"\nMissing values: {X.isnull().sum().sum()}")

# Train/test split
split = int(len(X) * 0.8)
X_train = X[:split]
X_test = X[split:]
y_train = y[:split]
y_test = y[split:]

print(f"\nTrain size: {len(X_train)}, Test size: {len(X_test)}")

# Train model
print("\nTraining Linear Regression model...")
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)

# Evaluate
print("\nEvaluating model...")
results = evaluate_model(y_test, predictions, "Optimized Linear Regression")
print_evaluation(results)

# Show some example predictions
print("\nExample predictions:")
comparison = pd.DataFrame({
    'Actual': y_test.values[:10],
    'Predicted': predictions[:10],
    'Difference': np.abs(y_test.values[:10] - predictions[:10])
})
print(comparison.round(2))

print("\n✅ Done! Model is working correctly.")
