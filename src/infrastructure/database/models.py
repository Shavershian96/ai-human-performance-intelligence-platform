"""SQLAlchemy database models."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PerformanceData(Base):
    """Human performance metrics storage."""

    __tablename__ = "performance_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    athlete_id = Column(String(100), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    sleep_hours = Column(Float, nullable=False)
    sleep_quality = Column(Float, nullable=False)
    training_load = Column(Float, nullable=False)
    stress_level = Column(Float, nullable=False)
    recovery_score = Column(Float, nullable=False)
    resting_heart_rate = Column(Float, nullable=True)
    hrv = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)  # Target/label
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PerformanceData(athlete_id={self.athlete_id}, date={self.record_date})>"


class Prediction(Base):
    """Stored prediction results."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    athlete_id = Column(String(100), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    performance_score = Column(Float, nullable=False)
    features_used = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=False, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Prediction(athlete_id={self.athlete_id}, score={self.performance_score})>"


class TrainingRun(Base):
    """ML training run metadata."""

    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_date = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50), nullable=False)
    samples_used = Column(Integer, nullable=False)
    metrics = Column(JSON, nullable=True)  # {"mae": ..., "r2": ..., "rmse": ...}
    status = Column(String(20), default="completed")  # completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
