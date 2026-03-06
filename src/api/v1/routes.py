"""API v1 route handlers."""

import asyncio
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import (
    get_ingest_use_case,
    get_ml_trainer_client,
    get_model_registry,
    get_predict_use_case,
    get_train_use_case,
)
from src.api.schemas import (
    BulkIngestRequest,
    DashboardHistoricalItem,
    DashboardPredictionItem,
    DashboardTrainingRunItem,
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
from src.infrastructure.database.models import PerformanceData, Prediction, TrainingRun
from src.infrastructure.database.session import get_db

router = APIRouter()


async def _with_db_retry(operation, retries: int = 4, base_delay: float = 0.35):
    delay = base_delay
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                await asyncio.sleep(delay)
                delay *= 2
    raise HTTPException(status_code=503, detail=f"Database temporarily unavailable: {last_error}")


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


@router.post(
    "/predict",
    response_model=PredictResponse,
    tags=["predictions"],
    summary="Generate performance prediction",
    responses={200: {"description": "Prediction generated successfully"}},
)
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


@router.post(
    "/train",
    response_model=TrainResponse,
    tags=["training"],
    summary="Trigger model training",
    responses={
        200: {"description": "Training completed successfully"},
        503: {"description": "ML Trainer service unavailable"},
    },
)
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


@router.post(
    "/ingest",
    tags=["ingestion"],
    summary="Bulk ingest performance records",
    responses={200: {"description": "Records ingested successfully"}},
)
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


@router.get(
    "/dashboard/predictions",
    response_model=list[DashboardPredictionItem],
    tags=["dashboard"],
    summary="List latest predictions for dashboard",
)
async def dashboard_predictions(limit: int = Query(default=500, ge=1, le=5000)):
    def _query():
        with get_db() as session:
            return (
                session.query(Prediction)
                .order_by(Prediction.created_at.desc())
                .limit(limit)
                .all()
            )

    rows = await _with_db_retry(_query)
    return [
        DashboardPredictionItem(
            id=r.id,
            athlete_id=r.athlete_id,
            prediction_date=r.prediction_date,
            performance_score=float(r.performance_score),
            model_version=r.model_version,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in rows
    ]


@router.get(
    "/dashboard/training-runs",
    response_model=list[DashboardTrainingRunItem],
    tags=["dashboard"],
    summary="List latest training runs for dashboard",
)
async def dashboard_training_runs(limit: int = Query(default=100, ge=1, le=2000)):
    def _query():
        with get_db() as session:
            return (
                session.query(TrainingRun)
                .order_by(TrainingRun.run_date.desc())
                .limit(limit)
                .all()
            )

    rows = await _with_db_retry(_query)
    return [
        DashboardTrainingRunItem(
            run_date=r.run_date.isoformat() if r.run_date else "",
            model_version=r.model_version,
            samples_used=r.samples_used,
            test_mae=(r.metrics or {}).get("test_mae"),
            test_rmse=(r.metrics or {}).get("test_rmse"),
            test_r2=(r.metrics or {}).get("test_r2"),
            status=r.status,
        )
        for r in rows
    ]


@router.get(
    "/dashboard/historical",
    response_model=list[DashboardHistoricalItem],
    tags=["dashboard"],
    summary="List latest historical records for dashboard",
)
async def dashboard_historical(limit: int = Query(default=5000, ge=1, le=20000)):
    def _query():
        with get_db() as session:
            return (
                session.query(PerformanceData)
                .order_by(PerformanceData.record_date.desc())
                .limit(limit)
                .all()
            )

    rows = await _with_db_retry(_query)
    return [
        DashboardHistoricalItem(
            athlete_id=r.athlete_id,
            record_date=r.record_date,
            sleep_hours=float(r.sleep_hours),
            sleep_quality=float(r.sleep_quality),
            training_load=float(r.training_load),
            stress_level=float(r.stress_level),
            recovery_score=float(r.recovery_score),
            resting_heart_rate=float(r.resting_heart_rate) if r.resting_heart_rate is not None else None,
            hrv=float(r.hrv) if r.hrv is not None else None,
            performance_score=float(r.performance_score) if r.performance_score is not None else None,
        )
        for r in rows
    ]
