"""Training use case and ML Trainer service tests."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.application.use_cases.train import TrainModelUseCase
from src.domain.exceptions import InsufficientDataError
from src.ml_trainer.main import app


def _row(**overrides) -> dict:
    base = {
        "sleep_hours": 7.5,
        "sleep_quality": 8.0,
        "training_load": 250.0,
        "stress_level": 4.0,
        "recovery_score": 8.0,
        "resting_heart_rate": 55.0,
        "hrv": 65.0,
        "performance_score": 80.0,
    }
    base.update(overrides)
    return base


class StubPerfRepo:
    def __init__(self, rows: int):
        self._df = pd.DataFrame([_row() for _ in range(rows)])

    def load_all(self) -> pd.DataFrame:
        return self._df.copy()


class StubModel:
    version = "2.1"

    def __init__(self):
        self.trained_with = None
        self.groups_seen = None

    def train(self, X_train, y_train, X_test=None, y_test=None, groups=None) -> dict:
        self.trained_with = (len(X_train), len(X_test) if X_test is not None else 0)
        self.groups_seen = groups
        return {"test_mae": 1.78, "test_r2": 0.65}


class StubRunRepo:
    def __init__(self, fail: bool = False):
        self.saved: list[dict] = []
        self._fail = fail

    def save(self, **kwargs) -> None:
        if self._fail:
            raise RuntimeError("database unavailable")
        self.saved.append(kwargs)


# --- use case ---------------------------------------------------------------


def test_training_returns_metrics_and_sample_count():
    model = StubModel()
    runs = StubRunRepo()
    use_case = TrainModelUseCase(StubPerfRepo(20), model, runs)

    result = use_case.execute()

    assert result["status"] == "completed"
    assert result["samples_used"] == 20
    assert result["metrics"]["test_r2"] == 0.65
    assert result["model_version"] == "2.1"


def test_training_persists_run_metadata():
    runs = StubRunRepo()
    TrainModelUseCase(StubPerfRepo(20), StubModel(), runs).execute()

    assert len(runs.saved) == 1
    assert runs.saved[0]["status"] == "completed"
    assert runs.saved[0]["samples_used"] == 20


def test_training_survives_metadata_write_failure():
    """Losing the audit row must not discard a model that trained fine."""
    use_case = TrainModelUseCase(StubPerfRepo(20), StubModel(), StubRunRepo(fail=True))

    result = use_case.execute()

    assert result["status"] == "completed"


def test_insufficient_data_raises_domain_error():
    """A thin dataset surfaces as a domain error, not a bare ValueError."""
    use_case = TrainModelUseCase(StubPerfRepo(4), StubModel(), StubRunRepo())

    with pytest.raises(InsufficientDataError):
        use_case.execute()


def test_test_size_is_honoured():
    model = StubModel()
    TrainModelUseCase(StubPerfRepo(20), model, StubRunRepo()).execute(test_size=0.25)

    train_count, test_count = model.trained_with
    assert (train_count, test_count) == (15, 5)


# --- service surface --------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_liveness_identifies_the_service(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive", "service": "ml-trainer"}


def test_readiness_derives_status_from_dependencies(client):
    """The probe reports each dependency and only claims ready when all are.

    Asserted as an invariant rather than a fixed verdict: CI runs this against
    a live PostgreSQL service container while a developer machine usually has
    none, so pinning the expected status would make the test environmental.
    """
    response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["database_connected"], bool)
    assert isinstance(body["storage_writable"], bool)

    all_healthy = body["database_connected"] and body["storage_writable"]
    assert body["status"] == ("ready" if all_healthy else "not_ready")


def test_metrics_are_exposed(client):
    response = client.get("/metrics/")

    assert response.status_code == 200
    assert "python_" in response.text or "http_requests_total" in response.text


def test_athlete_labels_reach_the_model_for_grouped_cv():
    """Cross-validation must fold by athlete to corroborate a grouped hold-out.

    The use case therefore has to hand the labels down rather than discarding
    them when it builds the split.
    """
    rows = [
        _row(athlete_id=f"ath-{a:03d}", record_date=f"2026-01-{d + 1:02d}")
        for a in range(8)
        for d in range(15)
    ]

    class Repo:
        def load_all(self):
            return pd.DataFrame(rows)

    model = StubModel()
    TrainModelUseCase(Repo(), model, StubRunRepo()).execute()

    assert model.groups_seen is not None
    assert len(model.groups_seen) == model.trained_with[0]
    assert model.groups_seen.nunique() > 1
