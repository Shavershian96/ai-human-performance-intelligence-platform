"""Health check endpoints - liveness and readiness probes.

Production standard: Kubernetes/orchestrators use:
- /health/live  - process is alive (no dependencies)
- /health/ready - ready to serve traffic (DB, model, etc.)
"""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_model_registry
from src.api.schemas import HealthResponse
from sqlalchemy import text

from src.domain.ports import ModelRegistryPort
from src.infrastructure.database.session import engine

router = APIRouter()


@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse)
async def health(
    model: ModelRegistryPort = Depends(get_model_registry),
) -> HealthResponse:
    """Legacy /health - same as readiness, returns HealthResponse."""
    try:
        model.ensure_loaded()
        model_loaded = model.is_loaded()
    except Exception:
        model_loaded = False
    return HealthResponse(status="healthy", version="1.0.0", model_loaded=model_loaded)


@router.get("/live")
async def liveness() -> dict:
    """Liveness probe - process is running. No external checks."""
    return {"status": "alive"}


@router.get("/ready", response_model=HealthResponse)
async def readiness(
    model: ModelRegistryPort = Depends(get_model_registry),
) -> HealthResponse:
    """Readiness probe - DB connected, model loaded (if applicable)."""
    model_loaded = False
    try:
        model.ensure_loaded()
        model_loaded = model.is_loaded()
    except Exception:
        pass

    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    ready = db_ok
    status = "ready" if ready else "not_ready"
    return HealthResponse(
        status=status,
        version="1.0.0",
        model_loaded=model_loaded,
    )
