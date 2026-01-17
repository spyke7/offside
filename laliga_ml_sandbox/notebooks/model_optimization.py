import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
import sys
sys.path.append('..')

from utils.feature_engineering_advanced import build_features, build_features_advanced
from utils.evaluation import evaluate_model, print_evaluation, compare_models, outcome_confusion_matrix

# Load data
df = pd.read_csv("c:/Users/Yasin/Desktop/laliga_ml_sandbox/data/LaLiga_24-25.csv")

# Convert date
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

print(f"Dataset: {len(df)} matches")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"\nFirst few matches:")
print(df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].head())

# Calculate goal difference
df["goal_diff"] = df["FTHG"] - df["FTAG"]

print(f"\nGoal Difference Distribution:")
print(df["goal_diff"].describe())

# Visualize goal difference distribution
plt.figure(figsize=(10, 5))
df["goal_diff"].hist(bins=20, edgecolor='black')
plt.xlabel('Goal Difference (Home - Away)')
plt.ylabel('Frequency')
plt.title('Distribution of Goal Differences')
plt.axvline(x=0, color='red', linestyle='--', label='Draw')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# Check for missing values
print(f"\nMissing values in features:")
feature_cols = ["HS", "AS", "HST", "AST", "HC", "AC"]
print(df[feature_cols].isnull().sum())

# ============================================================================
# BASELINE MODEL (Simple Features Only)
# ============================================================================

print("\n" + "="*80)
print("BASELINE MODEL - Simple Features Only")
print("="*80)

# Build simple features
X_baseline, y_baseline = build_features(df)

# Train/test split (80/20)
split = int(len(df) * 0.8)
X_train_base = X_baseline[:split]
X_test_base = X_baseline[split:]
y_train_base = y_baseline[:split]
y_test_base = y_baseline[split:]

print(f"\nTrain size: {len(X_train_base)}, Test size: {len(X_test_base)}")

# Train Linear Regression
lr_baseline = LinearRegression()
lr_baseline.fit(X_train_base, y_train_base)
preds_lr_base = lr_baseline.predict(X_test_base)

# Train XGBoost
xgb_baseline = XGBRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    random_state=42,
    objective="reg:squarederror"
)
xgb_baseline.fit(X_train_base, y_train_base)
preds_xgb_base = xgb_baseline.predict(X_test_base)

# Evaluate
results_lr_base = evaluate_model(y_test_base, preds_lr_base, "Baseline - Linear Regression")
results_xgb_base = evaluate_model(y_test_base, preds_xgb_base, "Baseline - XGBoost")

print_evaluation(results_lr_base)
print_evaluation(results_xgb_base)

# ============================================================================
# OPTIMIZED MODEL (With Rolling Features)
# ============================================================================

print("\n" + "="*80)
print("OPTIMIZED MODEL - With Rolling Averages (Last 5 Matches)")
print("="*80)

# Build advanced features
X_advanced, y_advanced = build_features_advanced(df, include_rolling=True)

print(f"\nFeatures in optimized model: {X_advanced.shape[1]}")
print(f"Feature names: {list(X_advanced.columns)}")

# Check for NaN values after feature engineering
print(f"\nNaN values after rolling feature creation:")
print(X_advanced.isnull().sum().sum())

# Train/test split (same split point for fair comparison)
X_train_adv = X_advanced[:split]
X_test_adv = X_advanced[split:]
y_train_adv = y_advanced[:split]
y_test_adv = y_advanced[split:]

# Train Linear Regression
lr_advanced = LinearRegression()
lr_advanced.fit(X_train_adv, y_train_adv)
preds_lr_adv = lr_advanced.predict(X_test_adv)

# Train XGBoost
xgb_advanced = XGBRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    random_state=42,
    objective="reg:squarederror"
)
xgb_advanced.fit(X_train_adv, y_train_adv)
preds_xgb_adv = xgb_advanced.predict(X_test_adv)

# Evaluate
results_lr_adv = evaluate_model(y_test_adv, preds_lr_adv, "Optimized - Linear Regression")
results_xgb_adv = evaluate_model(y_test_adv, preds_xgb_adv, "Optimized - XGBoost")

print_evaluation(results_lr_adv)
print_evaluation(results_xgb_adv)

# ============================================================================
# MODEL COMPARISON
# ============================================================================

print("\n" + "="*80)
print("MODEL COMPARISON")
print("="*80)

comparison = compare_models([
    results_lr_base,
    results_xgb_base,
    results_lr_adv,
    results_xgb_adv
])

print("\n", comparison.round(4))

# Highlight improvements
print("\n" + "="*80)
print("IMPROVEMENTS FROM BASELINE TO OPTIMIZED")
print("="*80)

mae_improvement_lr = ((results_lr_base['mae'] - results_lr_adv['mae']) / results_lr_base['mae']) * 100
mae_improvement_xgb = ((results_xgb_base['mae'] - results_xgb_adv['mae']) / results_xgb_base['mae']) * 100

dir_improvement_lr = (results_lr_adv['direction_accuracy'] - results_lr_base['direction_accuracy']) * 100
dir_improvement_xgb = (results_xgb_adv['direction_accuracy'] - results_xgb_base['direction_accuracy']) * 100

print(f"\nLinear Regression:")
print(f"  MAE improvement: {mae_improvement_lr:+.2f}%")
print(f"  Direction accuracy improvement: {dir_improvement_lr:+.2f} percentage points")

print(f"\nXGBoost:")
print(f"  MAE improvement: {mae_improvement_xgb:+.2f}%")
print(f"  Direction accuracy improvement: {dir_improvement_xgb:+.2f} percentage points")

# ============================================================================
# FEATURE IMPORTANCE (XGBoost)
# ============================================================================

print("\n" + "="*80)
print("FEATURE IMPORTANCE - XGBoost Optimized Model")
print("="*80)

importance = pd.DataFrame({
    'feature': X_advanced.columns,
    'importance': xgb_advanced.feature_importances_
}).sort_values('importance', ascending=False)

print("\n", importance)

# Visualize feature importance
plt.figure(figsize=(10, 8))
plt.barh(importance['feature'], importance['importance'])
plt.xlabel('Importance')
plt.title('Feature Importance - XGBoost Optimized Model')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

# ============================================================================
# CONFUSION MATRIX - Best Model
# ============================================================================

print("\n" + "="*80)
print("OUTCOME CONFUSION MATRIX - XGBoost Optimized Model")
print("="*80)

conf_matrix = outcome_confusion_matrix(y_test_adv, preds_xgb_adv)
print("\n", conf_matrix)
print("\nRows = Actual, Columns = Predicted")
print("H = Home Win, D = Draw, A = Away Win")

# ============================================================================
# NEXT STEPS
# ============================================================================

print("\n" + "="*80)
print("NEXT STEPS TO REACH MAE < 0.90")
print("="*80)

print("""
Current best MAE: {:.4f}
Target: 0.90 - 1.00

Recommended improvements:
1. Add more historical data (multiple seasons)
2. Implement Elo ratings for teams
3. Add home/away specific rolling features
4. Include head-to-head statistics
5. Add rest days between matches
6. Consider league position/momentum

Remember: Improvements should be gradual!
Sudden jumps in performance may indicate data leakage.
""".format(min(results_xgb_adv['mae'], results_lr_adv['mae'])))
