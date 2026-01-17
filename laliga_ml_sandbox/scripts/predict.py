from models.xgboost_model import XGBoostModel
import pandas as pd

model = XGBoostModel()
model.load("xgb_model.pkl")

match = pd.DataFrame([{
    "HS": 12,      # Home Shots
    "AS": 8,       # Away Shots
    "HST": 5,      # Home Shots on Target
    "AST": 3,      # Away Shots on Target
    "HC": 6,       # Home Corners
    "AC": 4        # Away Corners
}])

print("Predicted goal diff:", model.predict(match))
