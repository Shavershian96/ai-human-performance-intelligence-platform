"""Environment-based configuration with validation.

12-Factor App: Config via environment variables.
Validates required settings per environment (dev, staging, prod).
"""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings - validated from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_user: str = Field(default="perf_user")
    postgres_password: str = Field(default="perf_password")
    postgres_db: str = Field(default="performance_db")

    # --- API ---
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)

    # --- ML Trainer (microservices mode: predictions-api delegates to ml-trainer) ---
    use_ml_trainer_service: bool = Field(
        default=False,
        description="If True, POST /train delegates to ML Trainer service",
    )
    ml_trainer_url: str = Field(
        default="http://ml-trainer:8080",
        description="ML Trainer service URL when use_ml_trainer_service=True",
    )
    ml_trainer_timeout_seconds: int = Field(default=300, ge=10)
    ml_trainer_retry_attempts: int = Field(default=3, ge=1, le=10)
    ml_trainer_retry_base_delay_seconds: float = Field(default=0.5, ge=0.1, le=10.0)
    ml_trainer_circuit_breaker_failures: int = Field(default=5, ge=1, le=50)
    ml_trainer_circuit_breaker_reset_seconds: int = Field(default=60, ge=5, le=3600)

    # --- Application ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment: development|staging|production",
    )

    # --- Model storage (shared across API and Trainer) ---
    model_path: str = Field(
        default="models/performance_model.pkl",
        description="Path to trained ML model",
    )
    feature_scaler_path: str = Field(
        default="models/feature_scaler.pkl",
        description="Path to feature scaler",
    )

    # --- Observability ---
    otel_enabled: bool = Field(default=False, description="Enable OpenTelemetry")
    otel_service_name: str = Field(default="predictions-api")
    otel_endpoint: str = Field(default="http://localhost:4317")

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment(cls, v):
        if isinstance(v, str):
            try:
                return Environment(v.lower())
            except ValueError:
                return Environment.DEVELOPMENT
        return v or Environment.DEVELOPMENT

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.environment.value == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
