"""Data Ingestion microservice - FastAPI application.

Handles performance data intake via REST API:
- POST /v1/ingest - bulk JSON
- POST /v1/ingest/csv - CSV file upload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app
from sqlalchemy import text

from src.core.logging import configure_logging, get_logger
from src.data_ingestion.routes import router
from src.data_ingestion.schemas import HealthResponse
from src.domain.exceptions import DomainException
from src.api.exception_handlers import domain_exception_handler
from src.api.middleware import PrometheusMiddleware, RequestContextMiddleware
from src.infrastructure.database import init_db
from src.infrastructure.database.session import engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    configure_logging()
    logger.info("Data Ingestion service starting", port=8081)
    try:
        init_db()
    except Exception as e:
        logger.warning("Database init deferred", error=str(e))
    yield
    logger.info("Data Ingestion service shutting down")


app = FastAPI(
    title="Data Ingestion Service",
    description="Performance data intake microservice",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(DomainException, domain_exception_handler)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RequestContextMiddleware)

app.include_router(router)


@app.get("/health/live")
async def liveness() -> dict:
    """Liveness probe - process is running."""
    return {"status": "alive", "service": "data-ingestion"}


@app.get("/health/ready", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    """Readiness probe - database connectivity."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    return HealthResponse(
        status="ready" if db_ok else "not_ready",
        service="data-ingestion",
        version="1.0.0",
        database_connected=db_ok,
    )


app.mount("/metrics", make_asgi_app())
