"""Data Ingestion microservice tests.

The repository is overridden via FastAPI's dependency graph, so these exercise
routing, validation and error mapping without a database.
"""

import io

import pytest
from fastapi.testclient import TestClient

from src.data_ingestion.main import app
from src.data_ingestion.routes import get_ingest_use_case


class StubRepo:
    def __init__(self):
        self.saved: list = []

    def save_many(self, records) -> int:
        self.saved.extend(records)
        return len(records)


class RecordingUseCase:
    """Stands in for IngestPerformanceDataUseCase, recording what it received."""

    def __init__(self):
        self.repo = StubRepo()
        self.frames: list = []

    def execute_from_records(self, records) -> int:
        return self.repo.save_many(records)

    def execute_from_dataframe(self, df) -> int:
        self.frames.append(df)
        return len(df)


# Starting the app runs the DB-init backoff, which costs seconds with no
# database present. One client for the module keeps the suite fast; the use
# case is swapped per test through a holder the override reads.
_current: dict[str, RecordingUseCase] = {}


@pytest.fixture(scope="module")
def client() -> TestClient:
    app.dependency_overrides[get_ingest_use_case] = lambda: _current["use_case"]
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def use_case() -> RecordingUseCase:
    _current["use_case"] = RecordingUseCase()
    return _current["use_case"]


@pytest.fixture(autouse=True)
def _default_use_case(use_case):
    """Every test gets a fresh recording use case, even if it never asks."""
    return use_case


def _payload(**overrides) -> dict:
    base = {
        "athlete_id": "ath-001",
        "record_date": "2026-08-15",
        "sleep_hours": 7.5,
        "sleep_quality": 8.0,
        "training_load": 250.0,
        "stress_level": 4.0,
        "recovery_score": 8.0,
    }
    base.update(overrides)
    return base


CSV_HEADER = (
    "athlete_id,record_date,sleep_hours,sleep_quality,"
    "training_load,stress_level,recovery_score\n"
)


# --- service surface --------------------------------------------------------


def test_liveness_probe(client):
    assert client.get("/health/live").status_code == 200


def test_metrics_are_exposed(client):
    """The service is scrapeable, which is what Prometheus targets rely on."""
    response = client.get("/metrics/")
    assert response.status_code == 200
    assert "python_" in response.text or "http_requests_total" in response.text


# --- JSON ingestion ---------------------------------------------------------


def test_bulk_ingest_persists_records(client, use_case):
    response = client.post("/v1/ingest", json={"records": [_payload(), _payload()]})

    assert response.status_code == 200
    assert response.json()["records_ingested"] == 2
    assert len(use_case.repo.saved) == 2


def test_bulk_ingest_rejects_out_of_range_values(client):
    """Schema bounds are enforced at the edge, before anything is persisted."""
    response = client.post("/v1/ingest", json={"records": [_payload(recovery_score=78)]})

    assert response.status_code == 422


def test_bulk_ingest_rejects_missing_field(client):
    incomplete = _payload()
    del incomplete["sleep_hours"]

    assert client.post("/v1/ingest", json={"records": [incomplete]}).status_code == 422


# --- CSV ingestion ----------------------------------------------------------


def test_csv_upload_is_ingested(client, use_case):
    csv = CSV_HEADER + "ath-001,2026-08-15,7.5,8,250,4,8\n"
    response = client.post(
        "/v1/ingest/csv",
        files={"file": ("data.csv", io.BytesIO(csv.encode()), "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["records_ingested"] == 1
    assert len(use_case.frames) == 1


def test_non_csv_extension_is_refused(client):
    """The filename guard rejects the upload before it is parsed."""
    response = client.post(
        "/v1/ingest/csv",
        files={"file": ("data.txt", io.BytesIO(b"nope"), "text/plain")},
    )

    assert response.status_code == 400
    assert "must be a CSV" in response.json()["detail"]


def test_oversized_csv_is_refused(client):
    """The 10k-row cap is enforced, so one upload cannot exhaust the service."""
    rows = "".join(f"ath-{i:05d},2026-08-15,7.5,8,250,4,8\n" for i in range(10001))
    response = client.post(
        "/v1/ingest/csv",
        files={"file": ("big.csv", io.BytesIO((CSV_HEADER + rows).encode()), "text/csv")},
    )

    assert response.status_code == 400
    assert "10000" in response.json()["detail"]


def test_unparseable_csv_returns_400(client, monkeypatch):
    """A body that pandas cannot read is a client error, not a 500."""
    response = client.post(
        "/v1/ingest/csv",
        files={"file": ("data.csv", io.BytesIO(b"\xff\xfe\x00binary"), "text/csv")},
    )

    assert response.status_code == 400


def test_csv_failing_domain_validation_returns_422(client, use_case):
    """A well-formed CSV missing a required column surfaces as 422, not 500."""

    def explode(df):
        raise ValueError("Missing required columns: ['recovery_score']")

    use_case.execute_from_dataframe = explode
    csv = "athlete_id,record_date\nath-001,2026-08-15\n"

    response = client.post(
        "/v1/ingest/csv",
        files={"file": ("data.csv", io.BytesIO(csv.encode()), "text/csv")},
    )

    assert response.status_code == 422
    assert "recovery_score" in response.json()["detail"]
