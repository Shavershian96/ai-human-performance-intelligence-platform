"""Prediction repository port - abstract interface."""

from datetime import date
from typing import Protocol

from src.domain.entities import PredictionRecord


class PredictionRepositoryPort(Protocol):
    """Abstract interface for prediction persistence."""

    def save(
        self,
        athlete_id: str,
        prediction_date: date,
        performance_score: float,
        features_used: dict,
        model_version: str,
    ) -> None:
        """Persist a prediction."""
        ...
