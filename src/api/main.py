"""FastAPI application entry point - production-grade setup."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.api.exception_handlers import domain_exception_handler
from src.api.middleware import PrometheusMiddleware, RequestContextMiddleware
from src.api.v1.health import router as health_router
from src.api.v1.routes import router as api_router
from src.core.logging import configure_logging, get_logger
from src.domain.exceptions import DomainException
from src.infrastructure.database import init_db

logger = get_logger(__name__)


async def _init_db_with_backoff(max_attempts: int = 5, base_delay_seconds: float = 0.5) -> None:
    """Initialize DB tables with exponential backoff."""
    delay = base_delay_seconds
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            init_db()
            logger.info("Database initialization succeeded", attempt=attempt)
            return
        except Exception as exc:
            last_error = exc
            logger.warning("Database init attempt failed", attempt=attempt, max_attempts=max_attempts, error=str(exc))
            if attempt < max_attempts:
                await asyncio.sleep(delay)
                delay *= 2
    logger.warning("Database init deferred after retries", error=str(last_error) if last_error else "unknown")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and graceful shutdown."""
    configure_logging()
    logger.info("Starting AI Human Performance Intelligence Platform")

    await _init_db_with_backoff()

    yield

    logger.info("Shutting down")


OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness/readiness and platform health endpoints."},
    {"name": "predictions", "description": "Online inference endpoints for performance scoring."},
    {"name": "training", "description": "Model training endpoints and orchestration hooks."},
    {"name": "ingestion", "description": "Bulk ingestion endpoints for performance records."},
    {"name": "dashboard", "description": "Read-only analytics endpoints for dashboard consumption."},
]

app = FastAPI(
    title="AI Human Performance Intelligence Platform",
    summary="Production-oriented platform for human performance intelligence.",
    description=(
        "Enterprise-grade FastAPI service for human performance prediction, training orchestration, "
        "and data ingestion workflows with observability-first architecture."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=OPENAPI_TAGS,
    contact={"name": "Platform Engineering", "email": "daniel.eric@hotmail.com"},
    license_info={"name": "MIT"},
)

# Exception handling - register domain exceptions
app.add_exception_handler(DomainException, domain_exception_handler)

# Middleware order: last added = first executed (outermost)
# RequestContext (correlation ID) -> Prometheus (metrics)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RequestContextMiddleware)

# API v1 - versioned routes
app.include_router(api_router, prefix="/v1")
app.include_router(health_router, prefix="/v1/health", tags=["health"])
# Legacy unversioned (backwards compatibility)
app.include_router(api_router)
app.include_router(health_router, prefix="/health", tags=["health"])

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
