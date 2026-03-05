"""OpenTelemetry instrumentation - optional distributed tracing.

Enable with OTEL_ENABLED=true. Integrates with Jaeger, Zipkin, OTLP collectors.
"""

from typing import Any

from src.core.config import settings


def setup_telemetry() -> None:
    """Initialize OpenTelemetry if enabled."""
    if not settings.otel_enabled:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_endpoint))
        )
        trace.set_tracer_provider(provider)
        # FastAPIInstrumentor.instrument_app(app) called from main
    except ImportError:
        pass  # opentelemetry packages not installed


def get_tracer(name: str) -> Any:
    """Get tracer for manual spans."""
    if not settings.otel_enabled:
        return None
    try:
        from opentelemetry import trace
        return trace.get_tracer(settings.otel_service_name, "1.0.0")
    except ImportError:
        return None
