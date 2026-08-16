"""ML model tests."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.domain.exceptions import ModelNotReadyError
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
        "acute_load_7d": [240, 290, 210, 265, 275],
        "chronic_load_28d": [250, 255, 245, 250, 252],
        "acwr": [0.96, 1.14, 0.86, 1.06, 1.09],
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


@pytest.fixture
def larger_dataset():
    """Enough rows to trigger cross-validation, with real signal in them."""
    rng = np.random.default_rng(7)
    n = 200
    recovery = rng.uniform(1, 10, n)
    sleep_h = rng.uniform(5, 9, n)
    stress = rng.uniform(1, 10, n)
    target = 60 + 2.5 * recovery + 1.5 * sleep_h - 1.2 * stress + rng.normal(0, 2, n)
    X = pd.DataFrame({
        "sleep_hours": sleep_h,
        "sleep_quality": rng.uniform(1, 10, n),
        "training_load": rng.uniform(100, 400, n),
        "stress_level": stress,
        "recovery_score": recovery,
        "resting_heart_rate_filled": rng.uniform(45, 75, n),
        "hrv_filled": rng.uniform(30, 100, n),
        "sleep_recovery_ratio": sleep_h / recovery,
        "load_stress_ratio": rng.uniform(20, 120, n),
        "acute_load_7d": rng.uniform(100, 400, n),
        "chronic_load_28d": rng.uniform(150, 350, n),
        "acwr": rng.uniform(0.6, 1.5, n),
    })
    return X.iloc[:160], pd.Series(target[:160]), X.iloc[160:], pd.Series(target[160:])


def _fit(tmp, data):
    X_tr, y_tr, X_te, y_te = data
    predictor = PerformancePredictor(
        model_path=str(Path(tmp) / "model.pkl"),
        scaler_path=str(Path(tmp) / "scaler.pkl"),
    )
    return predictor, predictor.train(X_tr, y_tr, X_te, y_te)


def test_reports_a_mean_baseline_to_compare_against(larger_dataset):
    """Without a baseline an R2 is not interpretable, so training emits one."""
    with tempfile.TemporaryDirectory() as tmp:
        _, metrics = _fit(tmp, larger_dataset)

    assert "baseline_test_mae" in metrics
    assert "baseline_test_r2" in metrics
    # Predicting the mean explains ~none of the variance.
    assert metrics["baseline_test_r2"] < 0.1


def test_model_beats_the_mean_baseline(larger_dataset):
    """The point of serving a model at all: it must improve on the baseline."""
    with tempfile.TemporaryDirectory() as tmp:
        _, metrics = _fit(tmp, larger_dataset)

    assert metrics["test_mae"] < metrics["baseline_test_mae"]
    assert metrics["mae_improvement_pct"] > 0


def test_cross_validation_runs_on_a_large_enough_split(larger_dataset):
    """A single hold-out number is fragile, so folds are reported too."""
    with tempfile.TemporaryDirectory() as tmp:
        _, metrics = _fit(tmp, larger_dataset)

    assert metrics["cv_folds"] == 5
    assert -1.0 <= metrics["cv_r2_mean"] <= 1.0
    assert metrics["cv_r2_std"] >= 0.0


def test_cross_validation_skipped_when_data_is_thin(sample_train_data):
    """Fold scores on a handful of rows would be noise presented as evidence."""
    X, y = sample_train_data
    with tempfile.TemporaryDirectory() as tmp:
        _, metrics = _fit(tmp, (X, y, None, None))

    assert "cv_r2_mean" not in metrics


def test_feature_importances_cover_every_feature(larger_dataset):
    """Importances are reported per feature and ordered strongest first."""
    with tempfile.TemporaryDirectory() as tmp:
        predictor, _ = _fit(tmp, larger_dataset)
        importances = predictor.feature_importances()

    assert set(importances) == set(predictor.feature_names)
    assert list(importances.values()) == sorted(importances.values(), reverse=True)
    assert abs(sum(importances.values()) - 1.0) < 1e-6


def test_feature_importances_require_a_trained_model():
    with tempfile.TemporaryDirectory() as tmp:
        predictor = PerformancePredictor(
            model_path=str(Path(tmp) / "missing.pkl"),
            scaler_path=str(Path(tmp) / "missing_scaler.pkl"),
        )
        with pytest.raises(ModelNotReadyError):
            predictor.feature_importances()
