"""ML model for performance score prediction."""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

from src.core.config import settings
from src.core.logging import get_logger
from src.domain.exceptions import ModelNotReadyError

logger = get_logger(__name__)

MODEL_VERSION = "1.0"
FEATURE_NAMES = [
    "sleep_hours",
    "sleep_quality",
    "training_load",
    "stress_level",
    "recovery_score",
    "resting_heart_rate_filled",
    "hrv_filled",
    "sleep_recovery_ratio",
    "load_stress_ratio",
]


class PerformancePredictor:
    """
    Scikit-learn based predictor for human performance score.
    Uses RandomForestRegressor with StandardScaler preprocessing.
    """

    def __init__(self, model_path: Optional[str] = None, scaler_path: Optional[str] = None):
        self.model_path = Path(model_path or settings.model_path)
        self.scaler_path = Path(scaler_path or settings.feature_scaler_path)
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names = FEATURE_NAMES
        self.version = MODEL_VERSION

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
    ) -> Dict[str, float]:
        """
        Train the model and optionally evaluate on test set.
        Returns metrics dict.
        """
        # Align columns
        X_train = X_train[self.feature_names].copy()

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)

        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
        )
        self.model.fit(X_train_scaled, y_train)

        metrics: Dict[str, float] = {}
        pred_train = self.model.predict(X_train_scaled)
        metrics["train_mae"] = float(mean_absolute_error(y_train, pred_train))
        metrics["train_rmse"] = float(np.sqrt(mean_squared_error(y_train, pred_train)))
        metrics["train_r2"] = float(r2_score(y_train, pred_train))

        if X_test is not None and y_test is not None:
            X_test = X_test[self.feature_names].copy()
            X_test_scaled = self.scaler.transform(X_test)
            pred_test = self.model.predict(X_test_scaled)
            metrics["test_mae"] = float(mean_absolute_error(y_test, pred_test))
            metrics["test_rmse"] = float(np.sqrt(mean_squared_error(y_test, pred_test)))
            metrics["test_r2"] = float(r2_score(y_test, pred_test))

        self._save()
        logger.info("Model trained", metrics=metrics, version=self.version)
        return metrics

    def predict(self, features: Dict[str, float]) -> float:
        """Predict performance score from feature dict."""
        self._load_if_needed()
        if self.model is None or self.scaler is None:
            raise ModelNotReadyError()

        # Build feature vector
        df = self._features_dict_to_dataframe(features)
        X = self.scaler.transform(df)
        return float(self.model.predict(X)[0])

    def predict_batch(self, df: pd.DataFrame) -> np.ndarray:
        """Predict for multiple rows."""
        self._load_if_needed()
        if self.model is None or self.scaler is None:
            raise ModelNotReadyError()

        df = df[self.feature_names].copy()
        X = self.scaler.transform(df)
        return self.model.predict(X)

    def _features_dict_to_dataframe(self, features: Dict[str, float]) -> pd.DataFrame:
        """Convert prediction input dict to DataFrame with engineered features."""
        sleep_hours = features.get("sleep_hours", 7.0)
        sleep_quality = features.get("sleep_quality", 7.0)
        training_load = features.get("training_load", 200.0)
        stress_level = features.get("stress_level", 5.0)
        recovery_score = features.get("recovery_score", 7.0)
        resting_hr = features.get("resting_heart_rate", 60.0)
        hrv = features.get("hrv", 50.0)

        sleep_recovery_ratio = (sleep_hours * sleep_quality) / (recovery_score + 1e-6)
        load_stress_ratio = training_load / (stress_level + 1e-6)

        return pd.DataFrame(
            [
                {
                    "sleep_hours": sleep_hours,
                    "sleep_quality": sleep_quality,
                    "training_load": training_load,
                    "stress_level": stress_level,
                    "recovery_score": recovery_score,
                    "resting_heart_rate_filled": resting_hr,
                    "hrv_filled": hrv,
                    "sleep_recovery_ratio": sleep_recovery_ratio,
                    "load_stress_ratio": load_stress_ratio,
                }
            ]
        )

    def _save(self) -> None:
        """Persist model and scaler to disk."""
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.scaler_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)
        with open(self.scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info("Model saved", path=str(self.model_path))

    def load(self) -> None:
        """Load model and scaler from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        if not self.scaler_path.exists():
            raise FileNotFoundError(f"Scaler file not found: {self.scaler_path}")
        with open(self.model_path, "rb") as f:
            self.model = pickle.load(f)
        with open(self.scaler_path, "rb") as f:
            self.scaler = pickle.load(f)
        logger.info("Model loaded", path=str(self.model_path))

    def _load_if_needed(self) -> None:
        """Load model if not already in memory."""
        if self.model is None and Path(self.model_path).exists():
            self.load()

    def ensure_loaded(self) -> None:
        """Public method for protocol - load model if needed."""
        self._load_if_needed()

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None and self.scaler is not None
