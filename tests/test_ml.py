"""ML model tests."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.services.ml.model import PerformancePredictor


@pytest.fixture
def sample_train_data():
    """Sample training data."""
    return pd.DataFrame({
        "sleep_hours": [7, 6, 8, 7.5, 6.5],
        "sleep_quality": [8, 6, 9, 7, 7],
        "training_load": [250, 300, 200, 270, 280],
        "stress_level": [4, 6, 3, 5, 5],
        "recovery_score": [8, 6, 9, 7, 7],
        "resting_heart_rate_filled": [55, 62, 52, 58, 60],
        "hrv_filled": [65, 50, 72, 58, 55],
        "sleep_recovery_ratio": [7, 6, 8, 7.5, 6.5],
        "load_stress_ratio": [62.5, 50, 66.7, 54, 56],
    }), pd.Series([82, 71, 88, 76, 75])


def test_predictor_train_and_predict(sample_train_data):
    """Model can train and predict."""
    X, y = sample_train_data
    with tempfile.TemporaryDirectory() as tmp:
        model_path = Path(tmp) / "model.pkl"
        scaler_path = Path(tmp) / "scaler.pkl"
        predictor = PerformancePredictor(
            model_path=str(model_path),
            scaler_path=str(scaler_path),
        )
        metrics = predictor.train(X, y)
        assert "train_mae" in metrics
        assert "train_r2" in metrics

        features = {
            "sleep_hours": 7.5,
            "sleep_quality": 8,
            "training_load": 250,
            "stress_level": 4,
            "recovery_score": 8,
            "resting_heart_rate": 55,
            "hrv": 65,
        }
        score = predictor.predict(features)
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100 or -100 <= score <= 200  # Reasonable range
