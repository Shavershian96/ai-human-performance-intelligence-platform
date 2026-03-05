"""API v1 route handlers."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import (
    get_ingest_use_case,
    get_ml_trainer_client,
    get_model_registry,
    get_predict_use_case,
    get_train_use_case,
)
from src.api.schemas import (
    BulkIngestRequest,
    HealthResponse,
    PredictRequest,
    PredictResponse,
    TrainResponse,
)
from src.application.use_cases import (
    IngestPerformanceDataUseCase,
    PredictPerformanceUseCase,
    TrainModelUseCase,
)
from src.core.config import settings
from src.domain.entities import PerformanceRecord
from src.domain.ports import ModelRegistryPort
from src.infrastructure.clients.ml_trainer_client import MLTrainerClient

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    model: ModelRegistryPort = Depends(get_model_registry),
):
    """Health check - basic liveness."""
    try:
        model.ensure_loaded()
        model_loaded = model.is_loaded()
    except Exception:
        model_loaded = False
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_loaded=model_loaded,
    )


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    use_case: PredictPerformanceUseCase = Depends(get_predict_use_case),
):
    """Predict performance score from input features."""
    score, version = use_case.execute(
        athlete_id=request.athlete_id,
        prediction_date=request.prediction_date,
        sleep_hours=request.sleep_hours,
        sleep_quality=request.sleep_quality,
        training_load=request.training_load,
        stress_level=request.stress_level,
        recovery_score=request.recovery_score,
        resting_heart_rate=request.resting_heart_rate or 60.0,
        hrv=request.hrv or 50.0,
    )
    return PredictResponse(
        athlete_id=request.athlete_id,
        prediction_date=request.prediction_date,
        performance_score=score,
        model_version=version,
    )


@router.post("/train", response_model=TrainResponse)
async def train(
    use_case: TrainModelUseCase = Depends(get_train_use_case),
    model: ModelRegistryPort = Depends(get_model_registry),
    ml_trainer: MLTrainerClient = Depends(get_ml_trainer_client),
):
    """
    Trigger model training.

    If USE_ML_TRAINER_SERVICE=true (microservices mode), delegates to ML Trainer.
    Otherwise runs in-process (monolith/development).
    """
    if settings.use_ml_trainer_service:
        try:
            result = await ml_trainer.trigger_training()
            # Reload model in API after trainer writes to shared storage
            model.load()
            return TrainResponse(**result)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"ML Trainer service unavailable: {e}",
            )

    # In-process training (monolith)
    result = use_case.execute()
    model.load()
    return TrainResponse(**result)


@router.post("/ingest")
async def ingest_data(
    request: BulkIngestRequest,
    use_case: IngestPerformanceDataUseCase = Depends(get_ingest_use_case),
):
    """Bulk ingest performance records."""
    records = [
        PerformanceRecord(
            athlete_id=r.athlete_id,
            record_date=r.record_date,
            sleep_hours=r.sleep_hours,
            sleep_quality=r.sleep_quality,
            training_load=r.training_load,
            stress_level=r.stress_level,
            recovery_score=r.recovery_score,
            resting_heart_rate=r.resting_heart_rate,
            hrv=r.hrv,
            performance_score=r.performance_score,
        )
        for r in request.records
    ]
    count = use_case.execute_from_records(records)
    return {"status": "ok", "records_ingested": count}
