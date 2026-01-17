import joblib
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from .base_model import BaseModel


class LinearRegressionModel(BaseModel):

    def __init__(self):
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LinearRegression())
        ])

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def save(self, path: str):
        joblib.dump(self.model, path)

    def load(self, path: str):
        self.model = joblib.load(path)
