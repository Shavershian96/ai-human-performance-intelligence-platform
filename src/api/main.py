"""FastAPI application entry point - production-grade setup."""

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and graceful shutdown."""
    configure_logging()
    logger.info("Starting AI Human Performance Intelligence Platform")

    try:
        init_db()
    except Exception as e:
        logger.warning("Database init deferred", error=str(e))

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="AI Human Performance Intelligence Platform",
    description="End-to-end ML system for human performance prediction",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception handling - register domain exceptions
app.add_exception_handler(DomainException, domain_exception_handler)

# Middleware order: last added = first executed (outermost)
# RequestContext (correlation ID) -> Prometheus (metrics)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RequestContextMiddleware)

# API v1 - versioned routes
app.include_router(api_router, prefix="/v1", tags=["api-v1"])
app.include_router(health_router, prefix="/v1/health", tags=["health"])
# Legacy unversioned (backwards compatibility)
app.include_router(api_router, tags=["api-legacy"])
app.include_router(health_router, prefix="/health", tags=["health"])

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
