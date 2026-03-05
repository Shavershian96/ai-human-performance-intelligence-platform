"""Ingest performance data use case."""

from pathlib import Path
from typing import Union

import pandas as pd

from src.domain.entities import PerformanceRecord
from src.domain.exceptions import ValidationError
from src.domain.ports import PerformanceRepositoryPort
from src.core.logging import get_logger

logger = get_logger(__name__)


class IngestPerformanceDataUseCase:
    """Orchestrates ingestion of performance data from various sources."""

    def __init__(self, performance_repo: PerformanceRepositoryPort):
        self._repo = performance_repo

    def execute_from_dataframe(self, df: pd.DataFrame) -> int:
        """Ingest from DataFrame."""
        records = self._df_to_records(df)
        return self._repo.save_many(records)

    def execute_from_csv(self, path: Union[str, Path]) -> int:
        """Ingest from CSV file."""
        path = Path(path)
        if not path.exists():
            raise ValidationError(f"File not found: {path}")
        df = pd.read_csv(path)
        logger.info("Loaded CSV", path=str(path), rows=len(df))
        return self.execute_from_dataframe(df)

    def execute_from_records(self, records: list[PerformanceRecord]) -> int:
        """Ingest from domain records."""
        return self._repo.save_many(records)

    def _df_to_records(self, df: pd.DataFrame) -> list[PerformanceRecord]:
        """Convert DataFrame to domain records."""
        required = {
            "athlete_id", "record_date", "sleep_hours", "sleep_quality",
            "training_load", "stress_level", "recovery_score",
        }
        if not required.issubset(df.columns):
            missing = required - set(df.columns)
            raise ValidationError(f"Missing required columns: {list(missing)}")

        df = df.copy()
        if "record_date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["record_date"]):
            df["record_date"] = pd.to_datetime(df["record_date"]).dt.date

        records = []
        for _, row in df.iterrows():
            record = PerformanceRecord(
                athlete_id=str(row["athlete_id"]),
                record_date=row["record_date"] if hasattr(row["record_date"], "year") else pd.Timestamp(row["record_date"]).date(),
                sleep_hours=float(row["sleep_hours"]),
                sleep_quality=float(row["sleep_quality"]),
                training_load=float(row["training_load"]),
                stress_level=float(row["stress_level"]),
                recovery_score=float(row["recovery_score"]),
                resting_heart_rate=float(row["resting_heart_rate"]) if pd.notna(row.get("resting_heart_rate")) else None,
                hrv=float(row["hrv"]) if pd.notna(row.get("hrv")) else None,
                performance_score=float(row["performance_score"]) if pd.notna(row.get("performance_score")) else None,
            )
            records.append(record)
        return records
