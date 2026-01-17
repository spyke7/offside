import pandas as pd
from models.xgboost_model import XGBoostModel
from utils.feature_engineering import build_features

df = pd.read_csv("data/LaLiga_24-25.csv")

X, y = build_features(df)

split = int(len(df) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

model = XGBoostModel()
model.train(X_train, y_train)

# Save the trained model
model.save("xgb_model.pkl")
print("Model saved to xgb_model.pkl")

preds = model.predict(X_test)
print("Sample predictions:", preds[:5])
