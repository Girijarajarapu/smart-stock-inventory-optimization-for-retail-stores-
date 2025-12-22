# ml_model.py
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
from dateutil.parser import parse
from sqlalchemy.orm import Session
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from models import SalesRecord


class DemandForecaster:
    """
    Handles the full ML pipeline:
    - Load data from SQL
    - Feature engineering
    - Train optimized model (HistGradientBoostingRegressor)
    - Predict for new (store, family, date, onpromotion) inputs
    """

    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self.metrics: Optional[dict] = None

    def _fetch_data(self, db: Session) -> pd.DataFrame:
        """Load data from SQL and convert to pandas DataFrame."""
        q = db.query(SalesRecord)
        rows = q.all()
        data = [
            {
                "date": r.date,
                "store_nbr": r.store_nbr,
                "family": r.family,
                "onpromotion": r.onpromotion,
                "sales": r.sales,
            }
            for r in rows
        ]
        return pd.DataFrame(data)

    def _add_date_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day
        df["dow"] = df["date"].dt.dayofweek  # 0 = Monday
        df = df.drop(columns=["date"])
        return df

    def train(self, db: Session):
        """
        Train the model using data from SQL.
        """
        df = self._fetch_data(db)
        if df.empty:
            raise ValueError("No data in DB. Run data_loader.py first.")

        df = self._add_date_features(df)

        X = df.drop(columns=["sales"])
        y = df["sales"]

        # Feature types
        cat_features = ["family", "store_nbr"]
        num_features = [col for col in X.columns if col not in cat_features]

        # OneHotEncoder must output dense arrays for HistGradientBoosting
        try:
            ohe = OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            )
        except TypeError:
            ohe = OneHotEncoder(
                handle_unknown="ignore",
                sparse=False
            )

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", ohe, cat_features),
                ("num", "passthrough", num_features),
            ],
            sparse_threshold=0.0,  # force dense
        )

        model = HistGradientBoostingRegressor(
            max_depth=7,
            learning_rate=0.05,
            max_iter=300,
            l2_regularization=0.1,
            random_state=42,
        )

        self.pipeline = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", model),
            ]
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.pipeline.fit(X_train, y_train)

        # Evaluate
        preds = self.pipeline.predict(X_test)
        self.metrics = {
            "mae": float(mean_absolute_error(y_test, preds)),
            "rmse": float(np.sqrt(np.mean((y_test - preds) ** 2))),
            "r2": float(r2_score(y_test, preds)),
        }

    def predict(
        self,
        store_nbr: int,
        family: str,
        date_str: str | date,
        onpromotion: int = 0,
    ) -> float:
        """
        Predict sales for given inputs.
        date_str can be a date object or 'YYYY-MM-DD' string.
        """
        if self.pipeline is None:
            raise ValueError("Model not trained yet.")

        if isinstance(date_str, str):
            d = parse(date_str).date()
        else:
            d = date_str

        df = pd.DataFrame(
            [
                {
                    "date": d,
                    "store_nbr": store_nbr,
                    "family": family,
                    "onpromotion": onpromotion,
                }
            ]
        )
        df = self._add_date_features(df)
        pred = self.pipeline.predict(df)[0]
        return float(pred)
