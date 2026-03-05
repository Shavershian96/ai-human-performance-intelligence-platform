"""SQLAlchemy implementation of PredictionRepositoryPort."""

from datetime import date

from src.domain.ports import PredictionRepositoryPort
from src.infrastructure.database.models import Prediction
from src.infrastructure.database.session import get_db


class SqlAlchemyPredictionRepository:
    """PostgreSQL-backed prediction repository."""

    def save(
        self,
        athlete_id: str,
        prediction_date: date,
        performance_score: float,
        features_used: dict,
        model_version: str,
    ) -> None:
        """Persist a prediction."""
        with get_db() as session:
            pred = Prediction(
                athlete_id=athlete_id,
                prediction_date=prediction_date,
                performance_score=performance_score,
                features_used=features_used,
                model_version=model_version,
            )
            session.add(pred)
