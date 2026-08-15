"""Ingest performance data use case."""

from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd

from src.core.logging import get_logger
from src.domain.entities import PerformanceRecord
from src.domain.exceptions import ValidationError
from src.domain.ports import PerformanceRepositoryPort

logger = get_logger(__name__)


def _as_date(value: Any) -> date:
    """Coerce a DataFrame cell to a plain date.

    Timestamps and datetimes are narrowed rather than passed through: a
    datetime64 column would otherwise yield pd.Timestamp here while an object
    column yields date, making the entity's type depend on the source dtype.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    # pandas types .date() as Any.
    return cast(date, pd.Timestamp(value).date())


def _optional_float(row: pd.Series, column: str) -> float | None:
    """Read an optional numeric column, mapping missing/NaN to None."""
    value = row.get(column)
    return float(value) if pd.notna(value) else None


class IngestPerformanceDataUseCase:
    """Orchestrates ingestion of performance data from various sources."""

    def __init__(self, performance_repo: PerformanceRepositoryPort):
        self._repo = performance_repo

    def execute_from_dataframe(self, df: pd.DataFrame) -> int:
        """Ingest from DataFrame."""
        records = self._df_to_records(df)
        return self._repo.save_many(records)

    def execute_from_csv(self, path: str | Path) -> int:
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
        has_raw_dates = "record_date" in df.columns and not pd.api.types.is_datetime64_any_dtype(
            df["record_date"]
        )
        if has_raw_dates:
            df["record_date"] = pd.to_datetime(df["record_date"]).dt.date

        records = []
        for _, row in df.iterrows():
            record = PerformanceRecord(
                athlete_id=str(row["athlete_id"]),
                record_date=_as_date(row["record_date"]),
                sleep_hours=float(row["sleep_hours"]),
                sleep_quality=float(row["sleep_quality"]),
                training_load=float(row["training_load"]),
                stress_level=float(row["stress_level"]),
                recovery_score=float(row["recovery_score"]),
                resting_heart_rate=_optional_float(row, "resting_heart_rate"),
                hrv=_optional_float(row, "hrv"),
                performance_score=_optional_float(row, "performance_score"),
            )
            records.append(record)
        return records
