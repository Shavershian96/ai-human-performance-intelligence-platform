"""Prediction use case tests, focused on train/serve feature parity.

The model is trained on load-history features derived from an athlete's prior
sessions. If serving cannot rebuild them, every request is scored on a feature
space the model never saw. These tests pin that behaviour down.
"""

from datetime import date

import pytest

from src.application.use_cases.predict import PredictPerformanceUseCase
from src.domain.exceptions import ModelNotReadyError


class SpyModel:
    """Records the feature dict it was asked to score."""

    version = "1.0"

    def __init__(self, loaded: bool = True):
        self._loaded = loaded
        self.seen: dict | None = None

    def is_loaded(self) -> bool:
        return self._loaded

    def predict(self, features: dict) -> float:
        self.seen = dict(features)
        return 77.5


class StubPerfRepo:
    def __init__(self, loads: list[float] | None = None, boom: bool = False):
        self._loads = loads or []
        self._boom = boom
        self.asked_with: tuple | None = None

    def load_recent_loads(self, athlete_id: str, before: date, days: int) -> list[float]:
        self.asked_with = (athlete_id, before, days)
        if self._boom:
            raise RuntimeError("database unavailable")
        return self._loads


def _execute(use_case, **overrides):
    kwargs = {
        "athlete_id": "ath-001",
        "prediction_date": date(2026, 8, 15),
        "sleep_hours": 7.5,
        "sleep_quality": 8.0,
        "training_load": 300.0,
        "stress_level": 4.0,
        "recovery_score": 8.0,
    }
    kwargs.update(overrides)
    return use_case.execute(**kwargs)


def test_refuses_to_predict_without_a_trained_model():
    use_case = PredictPerformanceUseCase(model_registry=SpyModel(loaded=False))

    with pytest.raises(ModelNotReadyError):
        _execute(use_case)


def test_history_is_used_to_build_the_load_features():
    """A steady base plus a recent spike should score with ACWR above 1."""
    model = SpyModel()
    repo = StubPerfRepo(loads=[200.0] * 20 + [600.0] * 5)
    use_case = PredictPerformanceUseCase(model_registry=model, performance_repo=repo)

    _execute(use_case)

    assert model.seen["acwr"] > 1.2
    assert model.seen["acute_load_7d"] > model.seen["chronic_load_28d"]


def test_history_window_ends_before_the_prediction_date():
    """Today's session must not feed its own features, matching training."""
    repo = StubPerfRepo(loads=[250.0] * 10)
    use_case = PredictPerformanceUseCase(model_registry=SpyModel(), performance_repo=repo)

    _execute(use_case, prediction_date=date(2026, 8, 15))

    athlete_id, before, days = repo.asked_with
    assert athlete_id == "ath-001"
    assert before == date(2026, 8, 15)
    assert days == 28


def test_no_repository_falls_back_to_a_neutral_ratio():
    """Without a history source the windows collapse to today's load."""
    model = SpyModel()
    use_case = PredictPerformanceUseCase(model_registry=model)

    _execute(use_case, training_load=300.0)

    assert model.seen["acwr"] == 1.0
    assert model.seen["acute_load_7d"] == 300.0
    assert model.seen["chronic_load_28d"] == 300.0


def test_unknown_athlete_falls_back_to_a_neutral_ratio():
    model = SpyModel()
    use_case = PredictPerformanceUseCase(
        model_registry=model, performance_repo=StubPerfRepo(loads=[])
    )

    _execute(use_case, training_load=180.0)

    assert model.seen["acwr"] == 1.0
    assert model.seen["acute_load_7d"] == 180.0


def test_history_lookup_failure_degrades_instead_of_erroring():
    """A prediction is still served, on neutral features, rather than a 500."""
    model = SpyModel()
    use_case = PredictPerformanceUseCase(
        model_registry=model, performance_repo=StubPerfRepo(boom=True)
    )

    score, version = _execute(use_case)

    assert score == 77.5
    assert version == "1.0"
    assert model.seen["acwr"] == 1.0


def test_every_model_feature_is_supplied():
    """Serving must cover the full feature space the pipeline produces."""
    from src.services.processing.pipeline import DataProcessingPipeline

    model = SpyModel()
    use_case = PredictPerformanceUseCase(
        model_registry=model, performance_repo=StubPerfRepo(loads=[220.0] * 30)
    )

    _execute(use_case)

    engineered = {"resting_heart_rate_filled", "hrv_filled",
                  "sleep_recovery_ratio", "load_stress_ratio"}
    expected = set(DataProcessingPipeline.FEATURE_COLUMNS) - engineered
    assert expected <= set(model.seen)
