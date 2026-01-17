# ⚽ Offside - Football Match Simulator & AI Prediction

A comprehensive football analytics platform combining **real-time 2D match simulation** with **AI-powered match outcome prediction**. Built with StatsBomb open data, featuring dynamic player movement, tactical formations, and machine learning models achieving 75% prediction accuracy.

---

## 🎯 Features

### 🎮 2D Match Simulation
- **Real-time visualization** of football matches using StatsBomb event data
- **Dynamic player movement** with tactical positioning based on ball location
- **Smooth interpolation** between tracking data points using Hermite curves
- **Interactive controls**: Play/Pause, Speed (1x-4x), Timeline seeking
- **Live statistics** tracking for individual players
- **Formation-aware positioning** with automatic collision detection
- **High-quality pitch rendering** using mplsoccer

### 🤖 AI Match Prediction (LaLiga ML Sandbox)
- **75% accuracy** in predicting home wins using Random Forest
- **Elo rating system** for dynamic team strength estimation
- **Rolling form features** (last 5 matches) for recent performance
- **XGBoost regression** for goal difference prediction
- **Feature importance analysis** with visualization
- **Multiple model architectures** (Random Forest, XGBoost, Linear Regression)

---

## 📁 Project Structure

```
offside/
├── main.py                      # Application entry point
├── src/                         # Simulation core
│   ├── game_engine.py          # Event processing, interpolation, tactical movement
│   ├── renderer.py             # Pygame UI, pitch rendering, controls
│   ├── data_loader.py          # StatsBomb data integration (kloppy)
│   ├── stats_tracker.py        # Real-time player statistics
│   └── config.py               # Constants, colors, screen layout
├── laliga_ml_sandbox/          # AI prediction system
│   ├── models/
│   │   ├── xgboost_model.py    # XGBoost regressor
│   │   ├── elo_model.py        # Elo rating calculator
│   │   └── base_model.py       # Abstract model interface
│   ├── utils/
│   │   ├── elo_features.py     # Elo rating system
│   │   ├── feature_engineering.py        # Basic features
│   │   ├── feature_engineering_advanced.py # Rolling stats
│   │   └── evaluation.py       # Model metrics
│   ├── notebooks/
│   │   ├── classification_model.py       # 75% accuracy classifier
│   │   └── model_optimization.py         # Hyperparameter tuning
│   └── data/
│       └── LaLiga_24-25.csv    # Match dataset (380 matches)
├── assets/
│   └── pitch_texture.png       # High-quality pitch image
├── data/
│   └── matches/                # Cached StatsBomb JSON data
└── requirements.txt            # Python dependencies
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd offside

# Install dependencies
pip install -r requirements.txt
```

### Running the Simulation

```bash
python main.py
```

**Controls:**
1. Select **Competition** (FIFA World Cup, La Liga, Premier League)
2. Select **Season**
3. Choose **Team A** and **Team B**
4. Click **Start Simulation**

**During Simulation:**
- `SPACE` - Play/Pause
- `←/→` - Seek ±5 seconds
- `Click Player` - View individual stats
- `ESC` - Return to menu

### Running AI Predictions

```bash
# Navigate to ML sandbox
cd laliga_ml_sandbox

# Train classification model (75% accuracy)
python notebooks/classification_model.py

# Train regression model (goal difference)
python notebooks/model_optimization.py

# Make predictions on new data
python scripts/predict.py
```

---

## 🎨 Simulation Architecture

### Game Engine (`game_engine.py`)
The core simulation engine processes StatsBomb events and generates smooth animations:

#### Key Components:
- **Event Timeline**: Chronological processing of passes, shots, tackles
- **Position Interpolation**: Smooth movement between freeze frames
- **Tactical Positioning**: Dynamic formations based on ball location
  - Teams push forward when attacking
  - Teams drop back when defending
  - Players maintain formation shape
- **Hybrid Movement System**:
  - Uses real tracking data when available (freeze frames)
  - Blends to tactical positions during sparse data gaps
  - Adds subtle "idle noise" to prevent static appearance

#### Performance Optimizations:
- **O(1) player metadata cache** (eliminates per-frame lookups)
- **Collision detection** for overlapping default positions
- **Smooth Hermite interpolation** for natural acceleration/deceleration

### Renderer (`renderer.py`)
Pygame-based UI with three main views:

1. **Menu Screen**: Competition/Season/Team selection with scrollable dropdowns
2. **Simulation View**: 
   - Top bar: Score, match time, period
   - Left sidebar: Controls guide, match info
   - Center: Animated pitch with players and ball
   - Right panel: Selected player statistics
   - Bottom: Playback controls and seek bar
3. **Stats Panel**: Real-time tracking of touches, passes, shots, tackles

### Data Loader (`data_loader.py`)
- Fetches StatsBomb open data via HTTP
- Uses **kloppy** for standardized coordinate systems
- Caches match data locally to avoid repeated downloads
- Extracts player metadata (jersey numbers, positions, teams)

---

## 🤖 AI Prediction System

### Dataset
- **Source**: LaLiga 2024-25 Season
- **Size**: 380 matches
- **Features**: 15 engineered features
- **Split**: 70% train / 20% test / 10% validation

### Features (15 Total)

#### Match Statistics (6)
- `HS`, `AS` - Home/Away Shots
- `HST`, `AST` - Home/Away Shots on Target
- `HC`, `AC` - Home/Away Corners

#### Elo Rating (1)
- `elo_diff` - Home Elo − Away Elo (with home advantage)

#### Rolling Form (8)
- `home_goals_rolling` - Avg goals scored (last 5 matches)
- `home_conceded_rolling` - Avg goals conceded (last 5)
- `away_goals_rolling` - Away team avg goals (last 5)
- `away_conceded_rolling` - Away team avg conceded (last 5)
- `home_points_rolling` - Home team avg points (last 5)
- `away_points_rolling` - Away team avg points (last 5)
- `home_win_rate` - Home win percentage (last 5)
- `away_win_rate` - Away win percentage (last 5)

### Model Performance

#### Classification (Home Win Prediction)
```
Model: Random Forest
Accuracy: 75.00%
Balanced Accuracy: 73.37%
F1-Score (macro): 0.7368
```

#### Regression (Goal Difference)
```
Model: XGBoost
MAE: 0.9737
RMSE: 1.3572
```

### Feature Importance (Top 5)
1. **elo_diff** - 15.54%
2. **AST** (Away Shots on Target) - 9.76%
3. **HST** (Home Shots on Target) - 7.33%
4. **HS** (Home Shots) - 7.15%
5. **away_goals_rolling** - 6.65%

---

## 📊 Technical Details

### Simulation Technology Stack
- **Pygame** - 2D rendering and UI
- **kloppy** - Football data standardization
- **mplsoccer** - Pitch visualization
- **NumPy** - Mathematical operations
- **StatsBomb Open Data** - Match events and tracking

### AI Technology Stack
- **scikit-learn** - Random Forest, model evaluation
- **XGBoost** - Gradient boosting regression
- **pandas** - Data manipulation
- **NumPy** - Numerical computing
- **matplotlib** - Visualization
- **joblib** - Model serialization

### Key Algorithms

#### Elo Rating System
```python
K = 40  # K-factor
Expected = 1 / (1 + 10^((Elo_B - Elo_A) / 400))
New_Elo = Old_Elo + K * (Actual - Expected)
```

#### Hermite Interpolation
```python
t_smooth = 3t² - 2t³  # Ease-in-out curve
position = start + (end - start) * t_smooth
```

#### Tactical Position Calculation
```python
# Teams shift based on ball position
if ball_x > 60:  # Ball in attacking half
    shift_forward = (ball_x - 60) * 0.3
else:  # Ball in defensive half
    shift_back = (60 - ball_x) * 0.2
```

---

## 🎯 Use Cases

### For Analysts
- Visualize tactical patterns from real match data
- Study player positioning and movement
- Analyze team formations dynamically

### For Developers
- Learn event-driven simulation architecture
- Understand sports data processing pipelines
- Explore ML feature engineering for sports

### For Researchers
- Test prediction models on real football data
- Experiment with Elo rating variations
- Develop new tactical metrics

---

## 📈 Future Enhancements

### Simulation
- [ ] 3D visualization with player heights
- [ ] Heatmap overlays for player activity
- [ ] Export match highlights as video
- [ ] Multi-match tournament mode

### AI Prediction
- [ ] Deep learning models (LSTM for sequences)
- [ ] Player-level impact predictions
- [ ] Live match outcome updates
- [ ] Integration with simulation for "what-if" scenarios

---

## 🛠️ Development

### Adding New Competitions
Edit `src/config.py`:
```python
COMPETITIONS = {
    "Your League": {
        "id": <competition_id>,
        "seasons": {
            "2024/2025": <season_id>
        }
    }
}
```

### Training Custom Models
```python
from laliga_ml_sandbox.models.xgboost_model import XGBoostModel

model = XGBoostModel(n_estimators=500, max_depth=5)
model.train(X_train, y_train)
predictions = model.predict(X_test)
model.save("my_model.pkl")
```

---

## 📝 Data Sources

- **StatsBomb Open Data**: [github.com/statsbomb/open-data](https://github.com/statsbomb/open-data)
- **LaLiga 2024-25**: Custom dataset in `laliga_ml_sandbox/data/`

---

## 🤝 Contributing

Contributions are welcome! Areas of interest:
- Performance optimizations
- New ML features
- UI/UX improvements
- Additional data providers (Opta, Wyscout)

---

## 📄 License

For educational and research purposes only. StatsBomb data usage subject to their [license terms](https://github.com/statsbomb/open-data/blob/master/LICENSE.pdf).

---

## 🙏 Acknowledgments

- **StatsBomb** for open football data
- **kloppy** for data standardization
- **mplsoccer** for pitch visualization tools
- **Pygame** community for game development resources

---

## 📧 Contact

For questions or collaboration: [Your Contact Info]

---

**Built with ⚽ and 🤖 for football analytics enthusiasts**
