"""Performance data repository port - abstract interface."""

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
