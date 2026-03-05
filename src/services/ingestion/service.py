"""Data ingestion service - loads and stores human performance data."""

from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from src.core.logging import get_logger
from src.domain.entities import PerformanceRecord
from src.infrastructure.database.models import PerformanceData
from src.infrastructure.database.session import get_db

logger = get_logger(__name__)


class IngestionService:
    """Service for ingesting and persisting human performance data."""

    def ingest_from_dataframe(self, df: pd.DataFrame) -> int:
        """
        Ingest performance data from a pandas DataFrame.

        Expected columns: athlete_id, record_date, sleep_hours, sleep_quality,
        training_load, stress_level, recovery_score, resting_heart_rate (opt),
        hrv (opt), performance_score (opt)
        """
        required_cols = {
            "athlete_id",
            "record_date",
            "sleep_hours",
            "sleep_quality",
            "training_load",
            "stress_level",
            "recovery_score",
        }
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        df = df.copy()
        if "record_date" in df.columns and not pd.api.types.is_datetime64_any_dtype(
            df["record_date"]
        ):
            df["record_date"] = pd.to_datetime(df["record_date"]).dt.date

        records = self._df_to_records(df)
        return self._persist_records(records)

    def ingest_from_csv(self, path: Union[str, Path]) -> int:
        """Ingest performance data from a CSV file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        df = pd.read_csv(path)
        logger.info("Loaded CSV", path=str(path), rows=len(df))
        return self.ingest_from_dataframe(df)

    def ingest_records(self, records: List[PerformanceRecord]) -> int:
        """Ingest a list of PerformanceRecord entities."""
        return self._persist_records(records)

    def _df_to_records(self, df: pd.DataFrame) -> List[PerformanceRecord]:
        """Convert DataFrame to PerformanceRecord list."""
        records = []
        for _, row in df.iterrows():
            record = PerformanceRecord(
                athlete_id=str(row["athlete_id"]),
                record_date=(
                    row["record_date"]
                    if isinstance(row["record_date"], date)
                    else pd.Timestamp(row["record_date"]).date()
                ),
                sleep_hours=float(row["sleep_hours"]),
                sleep_quality=float(row["sleep_quality"]),
                training_load=float(row["training_load"]),
                stress_level=float(row["stress_level"]),
                recovery_score=float(row["recovery_score"]),
                resting_heart_rate=(
                    float(row["resting_heart_rate"])
                    if pd.notna(row.get("resting_heart_rate"))
                    else None
                ),
                hrv=float(row["hrv"]) if pd.notna(row.get("hrv")) else None,
                performance_score=(
                    float(row["performance_score"])
                    if pd.notna(row.get("performance_score"))
                    else None
                ),
            )
            records.append(record)
        return records

    def _persist_records(
        self, records: List[PerformanceRecord]
    ) -> int:
        """Persist records to database."""
        if not records:
            return 0

        with get_db() as session:
            count = 0
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
                count += 1
            session.flush()

        logger.info("Persisted performance records", count=count)
        return count
