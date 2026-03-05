"""Predict performance use case."""

from datetime import date

from src.domain.exceptions import ModelNotReadyError
from src.domain.ports import ModelRegistryPort, PredictionRepositoryPort
from src.core.logging import get_logger

logger = get_logger(__name__)


class PredictPerformanceUseCase:
    """Orchestrates prediction and optional persistence."""

    def __init__(
        self,
        model_registry: ModelRegistryPort,
        prediction_repo: PredictionRepositoryPort | None = None,
    ):
        self._model = model_registry
        self._prediction_repo = prediction_repo

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

    def _get_model_version(self) -> str:
        """Get model version from registry."""
        return getattr(self._model, "version", "1.0")
