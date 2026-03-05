"""Pydantic schemas for Data Ingestion API - request/response validation."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PerformanceRecordSchema(BaseModel):
    """Single performance record for ingestion."""

    athlete_id: str = Field(..., min_length=1, max_length=100, description="Athlete identifier")
    record_date: date = Field(..., description="Date of record")
    sleep_hours: float = Field(..., ge=0, le=24, description="Hours of sleep")
    sleep_quality: float = Field(..., ge=1, le=10, description="Sleep quality 1-10")
    training_load: float = Field(..., ge=0, le=2000, description="Training load")
    stress_level: float = Field(..., ge=1, le=10, description="Stress level 1-10")
    recovery_score: float = Field(..., ge=1, le=10, description="Recovery score 1-10")
    resting_heart_rate: Optional[float] = Field(None, ge=30, le=120)
    hrv: Optional[float] = Field(None, ge=0, le=200, description="Heart rate variability (ms)")
    performance_score: Optional[float] = Field(None, ge=0, le=100, description="Target/label for ML")


class BulkIngestRequest(BaseModel):
    """Bulk ingestion request body."""

    records: list[PerformanceRecordSchema] = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Up to 10000 records per request",
    )


class IngestResponse(BaseModel):
    """Response after successful ingestion."""

    status: str = "ok"
    records_ingested: int
    message: str = ""


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    service: str = "data-ingestion"
    version: str = "1.0.0"
    database_connected: bool = False
