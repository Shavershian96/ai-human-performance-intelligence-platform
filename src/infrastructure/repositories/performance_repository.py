"""SQLAlchemy implementation of PerformanceRepositoryPort."""

from typing import TYPE_CHECKING

import pandas as pd

from src.domain.entities import PerformanceRecord
from src.domain.ports import PerformanceRepositoryPort
from src.infrastructure.database.models import PerformanceData
from src.infrastructure.database.session import get_db

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SqlAlchemyPerformanceRepository:
    """PostgreSQL-backed performance data repository."""

    def save_many(self, records: list[PerformanceRecord]) -> int:
        """Persist performance records."""
        if not records:
            return 0

        with get_db() as session:
            for rec in records:
                db_rec = PerformanceData(
                    athlete_id=rec.athlete_id,
                    record_date=rec.record_date,
                    sleep_hours=rec.sleep_hours,
                    sleep_quality=rec.sleep_quality,
                    training_load=rec.training_load,
                    stress_level=rec.stress_level,
                    recovery_score=rec.recovery_score,
                    resting_heart_rate=rec.resting_heart_rate,
                    hrv=rec.hrv,
                )
                if rec.performance_score is not None:
                    db_rec.performance_score = rec.performance_score
                session.add(db_rec)
            session.flush()
            return len(records)

    def load_all(self) -> pd.DataFrame:
        """Load all performance data as DataFrame."""
        with get_db() as session:
            rows = session.query(PerformanceData).all()
            return pd.DataFrame(
                [
                    {
                        "athlete_id": r.athlete_id,
                        "record_date": r.record_date,
                        "sleep_hours": r.sleep_hours,
                        "sleep_quality": r.sleep_quality,
                        "training_load": r.training_load,
                        "stress_level": r.stress_level,
                        "recovery_score": r.recovery_score,
                        "resting_heart_rate": r.resting_heart_rate,
                        "hrv": r.hrv,
                        "performance_score": r.performance_score,
                    }
                    for r in rows
                ]
            )
