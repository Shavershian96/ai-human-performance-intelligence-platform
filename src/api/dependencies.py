"""Dependency injection container - FastAPI Depends()."""

from functools import lru_cache

from fastapi import Depends

from src.application.use_cases import (
    IngestPerformanceDataUseCase,
    PredictPerformanceUseCase,
    TrainModelUseCase,
)
from src.domain.ports import (
    ModelRegistryPort,
    PerformanceRepositoryPort,
    PredictionRepositoryPort,
    TrainingRunRepositoryPort,
)
from src.infrastructure.clients.ml_trainer_client import MLTrainerClient
from src.infrastructure.repositories import (
    SqlAlchemyPerformanceRepository,
    SqlAlchemyPredictionRepository,
    SqlAlchemyTrainingRunRepository,
)
from src.services.ml.model import PerformancePredictor


# --- Repositories (singleton per request) ---


@lru_cache
def get_performance_repository() -> PerformanceRepositoryPort:
    """Performance data repository."""
    return SqlAlchemyPerformanceRepository()


@lru_cache
def get_prediction_repository() -> PredictionRepositoryPort:
    """Prediction repository."""
    return SqlAlchemyPredictionRepository()


@lru_cache
def get_training_run_repository() -> TrainingRunRepositoryPort:
    """Training run metadata repository."""
    return SqlAlchemyTrainingRunRepository()


@lru_cache
def get_model_registry() -> ModelRegistryPort:
    """ML model registry (singleton for in-memory model)."""
    return PerformancePredictor()


# --- Use cases ---


def get_ingest_use_case(
    repo: PerformanceRepositoryPort = Depends(get_performance_repository),
) -> IngestPerformanceDataUseCase:
    """Ingest use case with injected repository."""
    return IngestPerformanceDataUseCase(performance_repo=repo)


def get_predict_use_case(
    model: ModelRegistryPort = Depends(get_model_registry),
    pred_repo: PredictionRepositoryPort = Depends(get_prediction_repository),
) -> PredictPerformanceUseCase:
    """Predict use case with injected model and prediction repo."""
    return PredictPerformanceUseCase(
        model_registry=model,
        prediction_repo=pred_repo,
    )


def get_ml_trainer_client() -> MLTrainerClient:
    """ML Trainer HTTP client."""
    return MLTrainerClient()


def get_train_use_case(
    perf_repo: PerformanceRepositoryPort = Depends(get_performance_repository),
    model: ModelRegistryPort = Depends(get_model_registry),
    training_repo: TrainingRunRepositoryPort = Depends(get_training_run_repository),
) -> TrainModelUseCase:
    """Train use case with injected repositories and model."""
    return TrainModelUseCase(
        performance_repo=perf_repo,
        model_registry=model,
        training_run_repo=training_repo,
    )
