"""Predict performance use case."""

from datetime import date

import pandas as pd

from src.core.logging import get_logger
from src.domain.exceptions import ModelNotReadyError
from src.domain.ports import (
    ModelRegistryPort,
    PerformanceRepositoryPort,
    PredictionRepositoryPort,
)
from src.services.processing.pipeline import DataProcessingPipeline

logger = get_logger(__name__)


class PredictPerformanceUseCase:
    """Orchestrates prediction and optional persistence."""

    def __init__(
        self,
        model_registry: ModelRegistryPort,
        prediction_repo: PredictionRepositoryPort | None = None,
        performance_repo: PerformanceRepositoryPort | None = None,
    ):
        self._model = model_registry
        self._prediction_repo = prediction_repo
        # Optional: when wired, the athlete's recent sessions are read so the
        # request is scored with the same load-history features the model was
        # trained on. Without it, those features fall back to a neutral ratio.
        self._performance_repo = performance_repo

    def execute(
        self,
        athlete_id: str,
        prediction_date: date,
        sleep_hours: float,
        sleep_quality: float,
        training_load: float,
        stress_level: float,
        recovery_score: float,
        resting_heart_rate: float = 60.0,
        hrv: float = 50.0,
    ) -> tuple[float, str]:
        """
        Run prediction. Returns (score, model_version).
        Persists to repo if configured.
        """
        if not self._model.is_loaded():
            raise ModelNotReadyError()

        features = {
            "sleep_hours": sleep_hours,
            "sleep_quality": sleep_quality,
            "training_load": training_load,
            "stress_level": stress_level,
            "recovery_score": recovery_score,
            "resting_heart_rate": resting_heart_rate,
            "hrv": hrv,
        }
        features.update(
            self._load_history_features(athlete_id, prediction_date, training_load)
        )

        score = self._model.predict(features)

        if self._prediction_repo:
            try:
                self._prediction_repo.save(
                    athlete_id=athlete_id,
                    prediction_date=prediction_date,
                    performance_score=score,
                    features_used=features,
                    model_version=self._get_model_version(),
                )
            except Exception as e:
                logger.warning("Failed to persist prediction", error=str(e))

        return round(score, 2), self._get_model_version()

    def _load_history_features(
        self, athlete_id: str, prediction_date: date, training_load: float
    ) -> dict[str, float]:
        """Rebuild the acute/chronic load features for a single request.

        Mirrors DataProcessingPipeline.add_load_history_features: the windows
        cover the days before the prediction date, so today's load is excluded
        exactly as it is during training. With no repository wired, or no
        recorded history for this athlete, both windows collapse to today's
        load and the ratio is a neutral 1.0.
        """
        neutral = {
            "acute_load_7d": training_load,
            "chronic_load_28d": training_load,
            "acwr": 1.0,
        }
        if self._performance_repo is None:
            return neutral

        try:
            history = self._performance_repo.load_recent_loads(
                athlete_id, prediction_date, DataProcessingPipeline.CHRONIC_SPAN
            )
        except Exception as exc:
            # A degraded feature is better than a failed prediction, but it
            # must not pass silently - the served value is not what the model
            # would have produced with history.
            logger.warning(
                "Load history unavailable, scoring with neutral ratio",
                athlete_id=athlete_id,
                error=str(exc),
            )
            return neutral

        if not history:
            return neutral

        prior = pd.Series(history, dtype="float64")
        acute = float(prior.ewm(span=DataProcessingPipeline.ACUTE_SPAN).mean().iloc[-1])
        chronic = float(prior.ewm(span=DataProcessingPipeline.CHRONIC_SPAN).mean().iloc[-1])
        acwr = float(
            DataProcessingPipeline.compute_acwr(
                pd.Series([acute]), pd.Series([chronic])
            ).iloc[0]
        )
        return {"acute_load_7d": acute, "chronic_load_28d": chronic, "acwr": acwr}

    def _get_model_version(self) -> str:
        """Get model version from registry."""
        return getattr(self._model, "version", "1.0")
