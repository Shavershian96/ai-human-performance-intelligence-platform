"""Performance data repository port - abstract interface."""

from datetime import date
from typing import Protocol

import pandas as pd

from src.domain.entities import PerformanceRecord


class PerformanceRepositoryPort(Protocol):
    """Abstract interface for performance data persistence and retrieval."""

    def save_many(self, records: list[PerformanceRecord]) -> int:
        """Persist performance records. Returns count saved."""
        ...

    def load_all(self) -> pd.DataFrame:
        """Load all performance data as DataFrame."""
        ...

    def load_recent_loads(self, athlete_id: str, before: date, days: int) -> list[float]:
        """Training loads for one athlete in the `days` before `before`.

        Oldest first. Used at prediction time to rebuild the same load-history
        features the training pipeline computes, so a served request is scored
        on the same feature space it was trained on.
        """
        ...
