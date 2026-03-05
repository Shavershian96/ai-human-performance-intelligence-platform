"""ML Trainer Service - Standalone microservice for model training.

Scales independently from the predictions API. Triggered via HTTP.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.exception_handlers import domain_exception_handler
from src.api.middleware import PrometheusMiddleware, RequestContextMiddleware
from src.application.use_cases.train import TrainModelUseCase
from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.domain.exceptions import DomainException
from src.infrastructure.database import init_db
from src.infrastructure.repositories import (
    SqlAlchemyPerformanceRepository,
    SqlAlchemyTrainingRunRepository,
)
from src.services.ml.model import PerformancePredictor

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    configure_logging()
    logger.info("ML Trainer service starting")
    try:
        init_db()
    except Exception as e:
        logger.warning("Database init deferred", error=str(e))
    yield
    logger.info("ML Trainer service shutting down")


app = FastAPI(
    title="ML Trainer Service",
    description="Model training microservice",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(DomainException, domain_exception_handler)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RequestContextMiddleware)


@app.get("/health/live")
async def liveness():
    return {"status": "alive", "service": "ml-trainer"}


@app.get("/health/ready")
async def readiness():
    return {"status": "ready", "service": "ml-trainer"}


@app.post("/v1/train")
async def train():
    """Execute model training. Reads from DB, writes to shared storage."""
    perf_repo = SqlAlchemyPerformanceRepository()
    training_repo = SqlAlchemyTrainingRunRepository()
    model = PerformancePredictor(
        model_path=settings.model_path,
        scaler_path=settings.feature_scaler_path,
    )
    use_case = TrainModelUseCase(
        performance_repo=perf_repo,
        model_registry=model,
        training_run_repo=training_repo,
    )
    return use_case.execute()


app.mount("/metrics", make_asgi_app())
