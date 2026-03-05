"""Model registry port - abstract interface for ML model access."""

from typing import Protocol

import pandas as pd


class ModelRegistryPort(Protocol):
    """Abstract interface for ML model inference and training."""

    def predict(self, features: dict[str, float]) -> float:
        """Predict performance score from features."""
        ...

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame | None = None,
        y_test: pd.Series | None = None,
    ) -> dict[str, float]:
        """Train model, return metrics."""
        ...

    def is_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        ...

    def ensure_loaded(self) -> None:
        """Load model from disk if not already in memory."""
        ...

    def load(self) -> None:
        """Force reload model from disk (e.g. after training)."""
        ...
