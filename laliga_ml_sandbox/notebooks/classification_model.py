# =============================================================================
# LaLiga Classification Model - ACCURACY MAXIMIZATION RECIPE
# =============================================================================
# Target: Home Win (1) vs Not Home Win (0)
# Split: 70% Train / 20% Test / 10% Validation (Shuffled)
# Model: RandomForestClassifier with Elo ratings
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    classification_report, confusion_matrix,
    mean_absolute_error, mean_squared_error
)
import sys
sys.path.append('c:/Users/Yasin/Desktop/laliga_ml_sandbox')

from utils.elo_features import build_classification_features

# =============================================================================
# 1. LOAD DATA
# =============================================================================
print("=" * 70)
print("1. LOADING DATA")
print("=" * 70)

df = pd.read_csv('c:/Users/Yasin/Desktop/laliga_ml_sandbox/data/LaLiga_24-25.csv')
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
df = df.sort_values('Date').reset_index(drop=True)

print(f"Dataset: {len(df)} matches")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")

# Check class distribution
df['home_win'] = (df['FTHG'] > df['FTAG']).astype(int)
print(f"\nClass Distribution:")
print(df['home_win'].value_counts())
print(f"Home Win Rate: {df['home_win'].mean():.2%}")

# =============================================================================
# 2. BUILD FEATURES (Elo + Rolling + Match Stats)
# =============================================================================
print("\n" + "=" * 70)
print("2. BUILDING FEATURES")
print("=" * 70)

X, y_class, y_reg = build_classification_features(df, include_elo=True, include_rolling=True)

print(f"Feature matrix shape: {X.shape}")
print(f"Features ({len(X.columns)}):")
for i, col in enumerate(X.columns):
    print(f"  {i+1}. {col}")

print(f"\nMissing values: {X.isnull().sum().sum()}")

# =============================================================================
# 3. DATA SPLIT (70% Train / 20% Test / 10% Validation)
# =============================================================================
print("\n" + "=" * 70)
print("3. DATA SPLIT (70/20/10 with Shuffle)")
print("=" * 70)

# First split: 70% train, 30% temp
X_train, X_temp, y_train_class, y_temp_class, y_train_reg, y_temp_reg = train_test_split(
    X, y_class, y_reg,
    test_size=0.30,
    random_state=42,
    shuffle=True
)

# Second split: From 30%, get 20% test + 10% validation (2:1 ratio = 0.333)
X_test, X_val, y_test_class, y_val_class, y_test_reg, y_val_reg = train_test_split(
    X_temp, y_temp_class, y_temp_reg,
    test_size=0.333,  # 10% of total = 1/3 of 30%
    random_state=42,
    shuffle=True
)

print(f"Training set:   {len(X_train)} samples ({len(X_train)/len(X):.1%})")
print(f"Test set:       {len(X_test)} samples ({len(X_test)/len(X):.1%})")
print(f"Validation set: {len(X_val)} samples ({len(X_val)/len(X):.1%})")

# =============================================================================
# 4. TRAIN MODELS
# =============================================================================
print("\n" + "=" * 70)
print("4. TRAINING MODELS")
print("=" * 70)

# Model 1: RandomForestClassifier (PRIMARY)
print("\n🥇 Training RandomForestClassifier (Primary Model)...")
rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced',  # Handle class imbalance
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train, y_train_class)
rf_preds_test = rf_model.predict(X_test)
rf_preds_val = rf_model.predict(X_val)
rf_proba_test = rf_model.predict_proba(X_test)[:, 1]

# Model 2: GradientBoostingClassifier (SECONDARY)
print("🥈 Training GradientBoostingClassifier (Secondary Model)...")
gb_model = GradientBoostingClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    min_samples_split=5,
    random_state=42
)
gb_model.fit(X_train, y_train_class)
gb_preds_test = gb_model.predict(X_test)
gb_preds_val = gb_model.predict(X_val)

print("✅ Models trained successfully!")

# =============================================================================
# 5. CLASSIFICATION METRICS (MAIN EVALUATION)
# =============================================================================
print("\n" + "=" * 70)
print("5. CLASSIFICATION METRICS (PRIMARY)")
print("=" * 70)

def evaluate_classifier(y_true, y_pred, model_name, dataset_name):
    """Evaluate classification model with all required metrics."""
    acc = accuracy_score(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='macro')
    
    print(f"\n{model_name} on {dataset_name}:")
    print(f"  Accuracy:          {acc:.4f} ({acc*100:.2f}%)")
    print(f"  Balanced Accuracy: {bal_acc:.4f} ({bal_acc*100:.2f}%)")
    print(f"  F1-Score (macro):  {f1:.4f}")
    
    return {'accuracy': acc, 'balanced_accuracy': bal_acc, 'f1_macro': f1}

# Random Forest Metrics
rf_metrics_test = evaluate_classifier(y_test_class, rf_preds_test, "RandomForest", "Test Set")
rf_metrics_val = evaluate_classifier(y_val_class, rf_preds_val, "RandomForest", "Validation Set")

# Gradient Boosting Metrics
gb_metrics_test = evaluate_classifier(y_test_class, gb_preds_test, "GradientBoosting", "Test Set")
gb_metrics_val = evaluate_classifier(y_val_class, gb_preds_val, "GradientBoosting", "Validation Set")

# =============================================================================
# 6. REGRESSION METRICS (SECONDARY EVALUATION)
# =============================================================================
print("\n" + "=" * 70)
print("6. REGRESSION METRICS (SECONDARY)")
print("=" * 70)

# For regression, we use the predicted probability to estimate goal difference
# This is a rough proxy - actual regression would use a separate model

# Calculate MAE/MSE using sign-based regression proxy
def regression_metrics(y_true_reg, y_pred_class, model_name):
    """Calculate regression metrics based on classification predictions."""
    # Convert class predictions to estimated goal diff: 1 -> +1, 0 -> -0.5
    y_pred_reg = np.where(y_pred_class == 1, 1.0, -0.5)
    
    mae = mean_absolute_error(y_true_reg, y_pred_reg)
    mse = mean_squared_error(y_true_reg, y_pred_reg)
    rmse = np.sqrt(mse)
    
    print(f"\n{model_name} (proxy regression):")
    print(f"  MAE:  {mae:.4f}")
    print(f"  MSE:  {mse:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    
    return {'mae': mae, 'mse': mse, 'rmse': rmse}

rf_reg_metrics = regression_metrics(y_test_reg, rf_preds_test, "RandomForest")
gb_reg_metrics = regression_metrics(y_test_reg, gb_preds_test, "GradientBoosting")

# =============================================================================
# 7. DETAILED CLASSIFICATION REPORT
# =============================================================================
print("\n" + "=" * 70)
print("7. CLASSIFICATION REPORT - RANDOM FOREST")
print("=" * 70)

print("\nTest Set:")
print(classification_report(y_test_class, rf_preds_test, target_names=['Not Home Win', 'Home Win']))

# Confusion Matrix
cm = confusion_matrix(y_test_class, rf_preds_test)
print("Confusion Matrix:")
print(f"              Predicted")
print(f"              Not HW  Home Win")
print(f"Actual Not HW   {cm[0,0]:3d}     {cm[0,1]:3d}")
print(f"Actual Home Win {cm[1,0]:3d}     {cm[1,1]:3d}")

# =============================================================================
# 8. FEATURE IMPORTANCE
# =============================================================================
print("\n" + "=" * 70)
print("8. FEATURE IMPORTANCE")
print("=" * 70)

feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 15 Most Important Features:")
print(feature_importance.head(15).to_string(index=False))

# Visualize
plt.figure(figsize=(10, 8))
top_feat = feature_importance.head(15)
colors = ['red' if 'elo' in f.lower() else 'steelblue' for f in top_feat['feature']]
plt.barh(top_feat['feature'], top_feat['importance'], color=colors)
plt.xlabel('Importance')
plt.title('Feature Importance - RandomForest Classifier\n(Red = Elo Features)')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('c:/Users/Yasin/Desktop/laliga_ml_sandbox/feature_importance.png', dpi=150)
plt.show()

# =============================================================================
# 9. MODEL COMPARISON SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("9. MODEL COMPARISON SUMMARY")
print("=" * 70)

comparison = pd.DataFrame({
    'Metric': ['Accuracy', 'Balanced Accuracy', 'F1-Score (macro)', 'MAE', 'MSE'],
    'RandomForest (Test)': [
        f"{rf_metrics_test['accuracy']*100:.2f}%",
        f"{rf_metrics_test['balanced_accuracy']*100:.2f}%",
        f"{rf_metrics_test['f1_macro']:.4f}",
        f"{rf_reg_metrics['mae']:.4f}",
        f"{rf_reg_metrics['mse']:.4f}"
    ],
    'GradientBoosting (Test)': [
        f"{gb_metrics_test['accuracy']*100:.2f}%",
        f"{gb_metrics_test['balanced_accuracy']*100:.2f}%",
        f"{gb_metrics_test['f1_macro']:.4f}",
        f"{gb_reg_metrics['mae']:.4f}",
        f"{gb_reg_metrics['mse']:.4f}"
    ]
})

print("\n" + comparison.to_string(index=False))

# =============================================================================
# 10. STORE RESULTS
# =============================================================================
print("\n" + "=" * 70)
print("10. STORING RESULTS")
print("=" * 70)

# Store all metrics
results_storage = {
    'RandomForest': {
        'accuracy_pct': rf_metrics_test['accuracy'] * 100,
        'balanced_accuracy_pct': rf_metrics_test['balanced_accuracy'] * 100,
        'f1_macro': rf_metrics_test['f1_macro'],
        'mae': rf_reg_metrics['mae'],
        'mse': rf_reg_metrics['mse'],
        'rmse': rf_reg_metrics['rmse']
    },
    'GradientBoosting': {
        'accuracy_pct': gb_metrics_test['accuracy'] * 100,
        'balanced_accuracy_pct': gb_metrics_test['balanced_accuracy'] * 100,
        'f1_macro': gb_metrics_test['f1_macro'],
        'mae': gb_reg_metrics['mae'],
        'mse': gb_reg_metrics['mse'],
        'rmse': gb_reg_metrics['rmse']
    }
}

results_df = pd.DataFrame(results_storage).T
results_df.to_csv('c:/Users/Yasin/Desktop/laliga_ml_sandbox/classification_metrics.csv')

# Save predictions
predictions_df = pd.DataFrame({
    'actual': y_test_class.values,
    'rf_predicted': rf_preds_test,
    'rf_probability': rf_proba_test,
    'gb_predicted': gb_preds_test,
    'actual_goal_diff': y_test_reg.values
})
predictions_df.to_csv('c:/Users/Yasin/Desktop/laliga_ml_sandbox/classification_predictions.csv', index=False)

print("✅ Results saved to:")
print("   - classification_metrics.csv")
print("   - classification_predictions.csv")
print("   - feature_importance.png")

# =============================================================================
# 11. FINAL SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("📊 FINAL SUMMARY")
print("=" * 70)

best_model = "RandomForest" if rf_metrics_test['accuracy'] >= gb_metrics_test['accuracy'] else "GradientBoosting"
best_acc = max(rf_metrics_test['accuracy'], gb_metrics_test['accuracy'])

print(f"""
🎯 RESULTS ACHIEVED:

Best Model: {best_model}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Accuracy:           {best_acc*100:.2f}%
Balanced Accuracy:  {rf_metrics_test['balanced_accuracy']*100:.2f}%
F1-Score (macro):   {rf_metrics_test['f1_macro']:.4f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 TARGET CHECK:
  Expected with Elo + Classification: 58-62%
  Your Result: {best_acc*100:.2f}%
  Status: {"✅ ON TARGET" if 0.54 <= best_acc <= 0.65 else "⚠️ CHECK DATA" if best_acc > 0.65 else "📈 NEEDS IMPROVEMENT"}

📋 FEATURES USED:
  ✓ Match Stats (HS, AS, HST, AST, HC, AC)
  ✓ Elo Rating Difference (home - away) 🔥
  ✓ Rolling Form Features (last 5 matches)
  ✓ Win Rate in last 5 matches

🔧 CONFIG:
  Split: 70% Train / 20% Test / 10% Validation
  Shuffle: True
  Random State: 42
  Class Weighting: Balanced

✅ Analysis Complete!
""")
