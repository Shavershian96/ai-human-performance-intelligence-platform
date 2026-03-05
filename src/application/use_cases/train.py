"""Train model use case."""

from src.domain.exceptions import InsufficientDataError
from src.domain.ports import (
    ModelRegistryPort,
    PerformanceRepositoryPort,
    TrainingRunRepositoryPort,
)
from src.services.processing.pipeline import DataProcessingPipeline
from src.core.logging import get_logger

logger = get_logger(__name__)


class TrainModelUseCase:
    """Orchestrates model training end-to-end."""

    def __init__(
        self,
        performance_repo: PerformanceRepositoryPort,
        model_registry: ModelRegistryPort,
        training_run_repo: TrainingRunRepositoryPort,
    ):
        self._perf_repo = performance_repo
        self._model = model_registry
        self._training_run_repo = training_run_repo

    def execute(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> dict:
        """
        Load data, process, train, persist run metadata.
        Returns dict with status, model_version, samples_used, metrics.
        """
        pipeline = DataProcessingPipeline(self._perf_repo)
        try:
            X_train, y_train, X_test, y_test = pipeline.run(
                test_size=test_size,
                random_state=random_state,
            )
        except ValueError as e:
            raise InsufficientDataError(str(e))

        metrics = self._model.train(X_train, y_train, X_test, y_test)
        samples = len(X_train) + len(X_test)
        version = getattr(self._model, "version", "1.0")

        try:
            self._training_run_repo.save(
                model_version=version,
                samples_used=samples,
                metrics=metrics,
                status="completed",
            )
        except Exception as e:
            logger.warning("Failed to persist training run", error=str(e))

        return {
            "status": "completed",
            "model_version": version,
            "samples_used": samples,
            "metrics": metrics,
        }
