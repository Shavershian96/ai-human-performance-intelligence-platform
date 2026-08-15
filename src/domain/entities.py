"""Domain entities for human performance data."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class PerformanceRecord:
    """Raw human performance data record."""

    athlete_id: str
    record_date: date
    sleep_hours: float
    sleep_quality: float  # 1-10 scale
    training_load: float  # Arbitrary units (e.g., TSS, RPE-based)
    stress_level: float  # 1-10 scale
    recovery_score: float  # 1-10 scale
    resting_heart_rate: float | None = None
    hrv: float | None = None  # Heart rate variability in ms
    performance_score: float | None = None  # Target/label for ML
    created_at: datetime | None = None


@dataclass
class PredictionRecord:
    """Stored prediction result."""

    id: int | None
    athlete_id: str
    prediction_date: date
    performance_score: float
    features_used: dict
    model_version: str
    created_at: datetime | None = None
