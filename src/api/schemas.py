"""Pydantic schemas for API request/response."""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    model_loaded: bool = False


class PredictRequest(BaseModel):
    """Request body for prediction endpoint."""

    athlete_id: str = Field(..., description="Athlete identifier")
    prediction_date: date = Field(..., description="Date for prediction")
    sleep_hours: float = Field(..., ge=0, le=24, description="Hours of sleep")
    sleep_quality: float = Field(..., ge=1, le=10, description="Sleep quality 1-10")
    training_load: float = Field(..., ge=0, description="Training load")
    stress_level: float = Field(..., ge=1, le=10, description="Stress level 1-10")
    recovery_score: float = Field(..., ge=1, le=10, description="Recovery score 1-10")
    resting_heart_rate: Optional[float] = Field(None, ge=30, le=120)
    hrv: Optional[float] = Field(None, ge=0, description="Heart rate variability")


class PredictResponse(BaseModel):
    """Prediction response."""

    athlete_id: str
    prediction_date: date
    performance_score: float
    model_version: str


class TrainResponse(BaseModel):
    """Training response."""

    status: str = "completed"
    model_version: str
    samples_used: int
    metrics: Dict[str, float]


class PerformanceRecordSchema(BaseModel):
    """Schema for performance data ingestion."""

    athlete_id: str
    record_date: date
    sleep_hours: float = Field(..., ge=0, le=24)
    sleep_quality: float = Field(..., ge=1, le=10)
    training_load: float = Field(..., ge=0)
    stress_level: float = Field(..., ge=1, le=10)
    recovery_score: float = Field(..., ge=1, le=10)
    resting_heart_rate: Optional[float] = Field(None, ge=30, le=120)
    hrv: Optional[float] = Field(None, ge=0)
    performance_score: Optional[float] = Field(None, ge=0, le=100)


class BulkIngestRequest(BaseModel):
    """Bulk ingestion request."""

    records: List[PerformanceRecordSchema]
