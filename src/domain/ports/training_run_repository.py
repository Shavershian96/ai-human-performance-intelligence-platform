"""Training run repository port - abstract interface."""

from typing import Protocol


class TrainingRunRepositoryPort(Protocol):
    """Abstract interface for training run metadata persistence."""

    def save(
        self,
        model_version: str,
        samples_used: int,
        metrics: dict[str, float],
        status: str = "completed",
    ) -> None:
        """Persist training run metadata."""
        ...
