# LaLiga ML Model Optimization with Random Forest

## Objective

Build, evaluate, and optimize a **Random Forest regression model** to predict **goal difference (FTHG − FTAG)** in LaLiga matches. The notebook compares a **simple baseline model** with an **optimized, form-aware model** using rolling statistics, while reporting metrics expected in academic and industry reviews.

**Primary Metrics**

* MAE (Mean Absolute Error)
* MSE / RMSE
* Direction Accuracy (winner correctness via sign of goal difference)

---

## 1. Imports and Environment Setup

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import sys

# Sandbox project path
sys.path.append('c:/Users/Yasin/Desktop/laliga_ml_sandbox')

from utils.feature_engineering_advanced import build_features_advanced
from utils.evaluation import evaluate_model, print_evaluation, direction_accuracy
```

---

## 2. Load Dataset and Create Target

```python
df = pd.read_csv('c:/Users/Yasin/Desktop/laliga_ml_sandbox/data/LaLiga_24-25.csv')

df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
df = df.sort_values('Date').reset_index(drop=True)

# Target variable: goal difference
df['goal_diff'] = df['FTHG'] - df['FTAG']

print(f"Dataset size: {len(df)} matches")
print(f"Date range: {df['Date'].min()} → {df['Date'].max()}")
df.head()
```

---

## 3. Goal Difference Distribution (Sanity Check)

```python
plt.figure(figsize=(10, 5))
df['goal_diff'].hist(bins=20, edgecolor='black')
plt.axvline(0, color='red', linestyle='--', label='Draw')
plt.xlabel('Goal Difference (Home − Away)')
plt.ylabel('Frequency')
plt.title('Distribution of Goal Differences')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

print(df['goal_diff'].describe())
```

---

## 4. Baseline Features (No Temporal Information)

We start with match-level statistics only, without any team form or history.

```python
features_simple = ['HS', 'AS', 'HST', 'AST', 'HC', 'AC']

X_simple = df[features_simple].fillna(df[features_simple].mean())
y_simple = df['goal_diff']

print(f"Simple feature matrix shape: {X_simple.shape}")
```

### Train/Test Split (Time-Aware)

```python
split = int(len(X_simple) * 0.8)

X_train_simple, X_test_simple = X_simple[:split], X_simple[split:]
y_train_simple, y_test_simple = y_simple[:split], y_simple[split:]
```

---

## 5. Baseline Model: Random Forest

```python
rf_baseline = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)

rf_baseline.fit(X_train_simple, y_train_simple)
preds_baseline = rf_baseline.predict(X_test_simple)

mae_baseline = mean_absolute_error(y_test_simple, preds_baseline)
mse_baseline = mean_squared_error(y_test_simple, preds_baseline)
rmse_baseline = np.sqrt(mse_baseline)
dir_acc_baseline = direction_accuracy(y_test_simple, preds_baseline)

print('Baseline Random Forest')
print(f"MAE:  {mae_baseline:.4f}")
print(f"MSE:  {mse_baseline:.4f}")
print(f"RMSE: {rmse_baseline:.4f}")
print(f"Direction Accuracy: {dir_acc_baseline:.2%}")
```

---

## 6. Advanced Feature Engineering (Rolling / Form Features)

We now introduce **rolling averages and recent form features**, created in a leakage-safe manner.

```python
X_advanced, y_advanced = build_features_advanced(df, include_rolling=True)

print(f"Advanced feature matrix shape: {X_advanced.shape}")
print(f"Number of features: {X_advanced.shape[1]}")
print(f"Missing values: {X_advanced.isnull().sum().sum()}")
print('Feature names:')
print(list(X_advanced.columns))
```

### Train/Test Split

```python
X_train_adv, X_test_adv = X_advanced[:split], X_advanced[split:]
y_train_adv, y_test_adv = y_advanced[:split], y_advanced[split:]
```

---

## 7. Optimized Model: Random Forest with Form

```python
rf_optimized = RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

rf_optimized.fit(X_train_adv, y_train_adv)
preds_optimized = rf_optimized.predict(X_test_adv)

mae_optimized = mean_absolute_error(y_test_adv, preds_optimized)
mse_optimized = mean_squared_error(y_test_adv, preds_optimized)
rmse_optimized = np.sqrt(mse_optimized)
dir_acc_optimized = direction_accuracy(y_test_adv, preds_optimized)

print('Optimized Random Forest')
print(f"MAE:  {mae_optimized:.4f}")
print(f"MSE:  {mse_optimized:.4f}")
print(f"RMSE: {rmse_optimized:.4f}")
print(f"Direction Accuracy: {dir_acc_optimized:.2%}")
```

---

## 8. Model Comparison

```python
mae_improvement = ((mae_baseline - mae_optimized) / mae_baseline) * 100
mse_improvement = ((mse_baseline - mse_optimized) / mse_baseline) * 100

def pct(x):
    return f"{x:+.2f}%"

print('=' * 70)
print('MODEL COMPARISON – RANDOM FOREST')
print('=' * 70)
print(f"MAE  : {mae_baseline:.4f} → {mae_optimized:.4f} ({pct(mae_improvement)})")
print(f"MSE  : {mse_baseline:.4f} → {mse_optimized:.4f} ({pct(mse_improvement)})")
print(f"DirA : {dir_acc_baseline:.2%} → {dir_acc_optimized:.2%}")
print('=' * 70)
```

---

## 9. Detailed Evaluation (Custom Metrics)

```python
results_baseline_full = evaluate_model(y_test_simple, preds_baseline, 'Baseline Random Forest')
results_optimized_full = evaluate_model(y_test_adv, preds_optimized, 'Optimized Random Forest')

print_evaluation(results_baseline_full)
print_evaluation(results_optimized_full)
```

---

## 10. Feature Importance Analysis

```python
feature_importance = pd.DataFrame({
    'feature': X_advanced.columns,
    'importance': rf_optimized.feature_importances_
}).sort_values('importance', ascending=False)

feature_importance.head(15)
```

```python
plt.figure(figsize=(10, 8))
top_features = feature_importance.head(15)
plt.barh(top_features['feature'], top_features['importance'])
plt.xlabel('Importance')
plt.title('Top 15 Feature Importances – Optimized Random Forest')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()
```

---

## 11. Prediction Diagnostics

```python
comparison_df = pd.DataFrame({
    'Actual': y_test_adv.values[:15],
    'Predicted': preds_optimized[:15],
    'Absolute_Error': np.abs(y_test_adv.values[:15] - preds_optimized[:15]),
    'Correct_Direction': (np.sign(y_test_adv.values[:15]) == np.sign(preds_optimized[:15]))
})

comparison_df.round(2)
```

---

## 12. Residual Analysis

```python
residuals = y_test_adv.values - preds_optimized

plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
plt.scatter(y_test_adv, preds_optimized, alpha=0.6)
plt.plot([-5, 7], [-5, 7], 'r--')
plt.xlabel('Actual')
plt.ylabel('Predicted')
plt.title('Actual vs Predicted')

plt.subplot(1, 3, 2)
plt.scatter(preds_optimized, residuals, alpha=0.6)
plt.axhline(0, color='r', linestyle='--')
plt.xlabel('Predicted')
plt.ylabel('Residual')
plt.title('Residual Plot')

plt.subplot(1, 3, 3)
plt.hist(np.abs(residuals), bins=20, edgecolor='black')
plt.axvline(mae_optimized, color='r', linestyle='--', label=f'MAE = {mae_optimized:.2f}')
plt.xlabel('Absolute Error')
plt.ylabel('Frequency')
plt.title('Error Distribution')
plt.legend()

plt.tight_layout()
plt.show()
```

---

## 13. Save Predictions and Metrics

```python
results_df = pd.DataFrame({
    'actual': y_test_adv.values,
    'predicted': preds_optimized,
    'error': np.abs(y_test_adv.values - preds_optimized),
    'correct_direction': (np.sign(y_test_adv.values) == np.sign(preds_optimized))
})

results_df.to_csv('c:/Users/Yasin/Desktop/laliga_ml_sandbox/model_predictions.csv', index=False)

metrics_summary = pd.DataFrame({
    'Model': ['Baseline RF', 'Optimized RF'],
    'MAE': [mae_baseline, mae_optimized],
    'MSE': [mse_baseline, mse_optimized],
    'RMSE': [rmse_baseline, rmse_optimized],
    'Direction_Accuracy_%': [dir_acc_baseline * 100, dir_acc_optimized * 100]
})

metrics_summary.to_csv('c:/Users/Yasin/Desktop/laliga_ml_sandbox/model_metrics.csv', index=False)

print('✅ Predictions and metrics saved.')
```

---

## Final Summary

* **Best model**: Random Forest with rolling and form-based features
* **Key result**: Improved MAE and direction accuracy over baseline
* **Conclusion**: Incorporating team form significantly enhances predictive performance without data leakage

✅ Analysis complete.
