"""Domain ports - abstract interfaces (dependency inversion)."""

from src.domain.ports.model_registry import ModelRegistryPort
from src.domain.ports.performance_repository import PerformanceRepositoryPort
from src.domain.ports.prediction_repository import PredictionRepositoryPort
from src.domain.ports.training_run_repository import TrainingRunRepositoryPort

__all__ = [
    "ModelRegistryPort",
    "PerformanceRepositoryPort",
    "PredictionRepositoryPort",
    "TrainingRunRepositoryPort",
]
