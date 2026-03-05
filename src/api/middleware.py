"""Custom middleware - request context, metrics."""

import time
import uuid
from typing import Callable

from fastapi import Request
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

import structlog

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to request context for distributed tracing."""

    async def dispatch(self, request: Request, call_next: Callable):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record request count and latency for Prometheus."""

    async def dispatch(self, request: Request, call_next: Callable):
        method = request.method
        path = request.url.path
        if path.startswith("/metrics") or path.startswith("/health"):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        status_code = response.status_code

        REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)

        return response
