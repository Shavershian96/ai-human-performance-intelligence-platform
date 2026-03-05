"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use in-memory SQLite for tests to avoid PostgreSQL dependency
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "test_db")


@pytest.fixture
def sample_features():
    """Sample feature dict for prediction."""
    return {
        "sleep_hours": 7.5,
        "sleep_quality": 8,
        "training_load": 250,
        "stress_level": 4,
        "recovery_score": 8,
        "resting_heart_rate": 55,
        "hrv": 65,
    }
