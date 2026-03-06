"""Pydantic schemas for API request/response."""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    model_loaded: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {"status": "healthy", "version": "1.0.0", "model_loaded": True}
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "example": {
                "athlete_id": "athlete-001",
                "prediction_date": "2026-03-06",
                "sleep_hours": 7.8,
                "sleep_quality": 8.4,
                "training_load": 265.0,
                "stress_level": 4.2,
                "recovery_score": 8.1,
                "resting_heart_rate": 56,
                "hrv": 68,
            }
        }
    }


class PredictResponse(BaseModel):
    """Prediction response."""

    athlete_id: str
    prediction_date: date
    performance_score: float
    model_version: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "athlete_id": "athlete-001",
                "prediction_date": "2026-03-06",
                "performance_score": 88.73,
                "model_version": "1.0",
            }
        }
    }


class TrainResponse(BaseModel):
    """Training response."""

    status: str = "completed"
    model_version: str
    samples_used: int
    metrics: Dict[str, float]

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "model_version": "1.0",
                "samples_used": 58420,
                "metrics": {"train_mae": 1.03, "train_rmse": 1.31, "train_r2": 0.93},
            }
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "example": {
                "records": [
                    {
                        "athlete_id": "athlete-001",
                        "record_date": "2026-03-06",
                        "sleep_hours": 7.8,
                        "sleep_quality": 8.4,
                        "training_load": 265.0,
                        "stress_level": 4.2,
                        "recovery_score": 8.1,
                        "resting_heart_rate": 56,
                        "hrv": 68,
                        "performance_score": 87.6,
                    }
                ]
            }
        }
    }


class DashboardPredictionItem(BaseModel):
    id: int
    athlete_id: str
    prediction_date: date
    performance_score: float
    model_version: str
    created_at: str


class DashboardTrainingRunItem(BaseModel):
    run_date: str
    model_version: str
    samples_used: int
    test_mae: Optional[float] = None
    test_rmse: Optional[float] = None
    test_r2: Optional[float] = None
    status: str


class DashboardHistoricalItem(BaseModel):
    athlete_id: str
    record_date: date
    sleep_hours: float
    sleep_quality: float
    training_load: float
    stress_level: float
    recovery_score: float
    resting_heart_rate: Optional[float] = None
    hrv: Optional[float] = None
    performance_score: Optional[float] = None
