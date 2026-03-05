"""SQLAlchemy implementation of TrainingRunRepositoryPort."""

from src.domain.ports import TrainingRunRepositoryPort
from src.infrastructure.database.models import TrainingRun
from src.infrastructure.database.session import get_db


class SqlAlchemyTrainingRunRepository:
    """PostgreSQL-backed training run metadata repository."""

    def save(
        self,
        model_version: str,
        samples_used: int,
        metrics: dict[str, float],
        status: str = "completed",
    ) -> None:
        """Persist training run metadata."""
        with get_db() as session:
            run = TrainingRun(
                model_version=model_version,
                samples_used=samples_used,
                metrics=metrics,
                status=status,
            )
            session.add(run)
