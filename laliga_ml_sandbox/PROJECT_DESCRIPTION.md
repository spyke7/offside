# LaLiga ML Sandbox - Project Description

## Overview

A machine learning project for predicting LaLiga football match outcomes using classification and regression models. The project implements team strength estimation via Elo ratings, rolling form features, and match statistics to predict home wins with **75% accuracy**.

---

## Objective

Build, evaluate, and optimize a **Random Forest classification model** to predict:
- **Primary Target**: Home Win (1) vs Not Home Win (0)
- **Secondary Target**: Goal Difference (FTHG − FTAG)

---

## Dataset

- **Source**: LaLiga 2024-25 Season
- **Size**: 380 matches
- **Date Range**: August 2024 - May 2025
- **Features**: Match statistics, Elo ratings, rolling form

---

## Models Used

### Primary Model (Accuracy Focused)
- **RandomForestClassifier**
  - n_estimators: 200
  - max_depth: 10
  - class_weight: balanced
  - Accuracy: **75.00%**

### Secondary Model (Comparison)
- **GradientBoostingClassifier**
  - n_estimators: 150
  - max_depth: 5
  - Accuracy: 67.11%

---

## Features (15 Total)

### Match Statistics (6)
| Feature | Description |
|---------|-------------|
| HS | Home Shots |
| AS | Away Shots |
| HST | Home Shots on Target |
| AST | Away Shots on Target |
| HC | Home Corners |
| AC | Away Corners |

### Elo Rating (1)
| Feature | Description |
|---------|-------------|
| elo_diff | Home Elo − Away Elo (with home advantage) |

### Rolling Form Features (8)
| Feature | Description |
|---------|-------------|
| home_goals_rolling | Home team avg goals (last 5) |
| home_conceded_rolling | Home team avg conceded (last 5) |
| away_goals_rolling | Away team avg goals (last 5) |
| away_conceded_rolling | Away team avg conceded (last 5) |
| home_points_rolling | Home team avg points (last 5) |
| away_points_rolling | Away team avg points (last 5) |
| home_win_rate | Home team win rate (last 5) |
| away_win_rate | Away team win rate (last 5) |

---

## Evaluation Metrics

### Classification (Primary)
- **Accuracy Score**: 75.00%
- **Balanced Accuracy**: 73.37%
- **F1-Score (macro)**: 0.7368

### Regression (Secondary)
- **MAE**: 0.9737
- **MSE**: 1.8421
- **RMSE**: 1.3572

---

## Data Split

| Set | Percentage | Samples |
|-----|------------|---------|
| Training | 70% | 266 |
| Testing | 20% | 76 |
| Validation | 10% | 38 |

- **Shuffle**: True
- **Random State**: 42

---

## Feature Importance (Top 5)

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | **elo_diff** | 15.54% |
| 2 | AST | 9.76% |
| 3 | HST | 7.33% |
| 4 | HS | 7.15% |
| 5 | away_goals_rolling | 6.65% |

---

## Project Structure

```
laliga_ml_sandbox/
├── data/
│   └── LaLiga_24-25.csv          # Match data
├── models/
│   ├── base_model.py             # Abstract base class
│   ├── xgboost_model.py          # XGBoost implementation
│   ├── linear_regression.py      # Linear regression model
│   └── elo_model.py              # Elo rating model
├── notebooks/
│   ├── classification_model.py   # Main classification notebook
│   ├── model_optimization.py     # Regression optimization
│   └── notebook_cells.py         # Jupyter-ready cells
├── scripts/
│   ├── train.py                  # Training script
│   └── predict.py                # Prediction script
├── utils/
│   ├── elo_features.py           # Elo rating system
│   ├── feature_engineering.py    # Basic features
│   ├── feature_engineering_advanced.py  # Rolling features
│   └── evaluation.py             # Evaluation metrics
├── requirements.txt              # Dependencies
├── classification_metrics.csv    # Results
├── classification_predictions.csv # Predictions
└── feature_importance.png        # Feature chart
```

---

## Requirements

```
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost>=2.0.0
matplotlib>=3.7.0
joblib>=1.3.0
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Classification Model
```bash
python notebooks/classification_model.py
```

### 3. Run Regression Optimization
```bash
python notebooks/model_optimization.py
```

---

## Key Results

- **Best Accuracy**: 75.00% (RandomForest)
- **Most Important Feature**: Elo Rating Difference (15.54%)
- **Model Improvement**: +8% over baseline with Elo features

---

## Author

LaLiga ML Sandbox Project

---

## License

For educational and research purposes only.
