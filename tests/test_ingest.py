"""Ingestion use-case tests: schema validation, type coercion, CSV loading."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.application.use_cases.ingest import IngestPerformanceDataUseCase
from src.domain.exceptions import ValidationError


class StubRepo:
    """Captures what the use case would have persisted."""

    def __init__(self):
        self.saved: list = []

    def save_many(self, records) -> int:
        self.saved.extend(records)
        return len(records)

    def load_all(self) -> pd.DataFrame:
        return pd.DataFrame()


def _row(**overrides) -> dict:
    base = {
        "athlete_id": "ath-001",
        "record_date": "2026-08-15",
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


@pytest.fixture
def repo() -> StubRepo:
    return StubRepo()


@pytest.fixture
def use_case(repo) -> IngestPerformanceDataUseCase:
    return IngestPerformanceDataUseCase(repo)


def test_ingests_a_valid_frame(use_case, repo):
    """Every row becomes a domain record and the count is reported back."""
    count = use_case.execute_from_dataframe(pd.DataFrame([_row(), _row()]))

    assert count == 2
    assert len(repo.saved) == 2
    assert repo.saved[0].athlete_id == "ath-001"


def test_missing_required_column_is_rejected(use_case):
    """A frame without a required measurement fails with a named column."""
    df = pd.DataFrame([_row()]).drop(columns=["recovery_score"])

    with pytest.raises(ValidationError, match="recovery_score"):
        use_case.execute_from_dataframe(df)


def test_optional_columns_may_be_absent(use_case, repo):
    """hrv, resting_heart_rate and performance_score are optional."""
    df = pd.DataFrame([_row()]).drop(
        columns=["hrv", "resting_heart_rate", "performance_score"]
    )

    assert use_case.execute_from_dataframe(df) == 1
    assert repo.saved[0].hrv is None
    assert repo.saved[0].performance_score is None


def test_nan_optionals_become_none(use_case, repo):
    """A NaN cell maps to None rather than float('nan') on the entity."""
    df = pd.DataFrame([_row(hrv=float("nan"), resting_heart_rate=float("nan"))])

    use_case.execute_from_dataframe(df)

    assert repo.saved[0].hrv is None
    assert repo.saved[0].resting_heart_rate is None


@pytest.mark.parametrize(
    "raw_date",
    ["2026-08-15", pd.Timestamp("2026-08-15"), date(2026, 8, 15)],
)
def test_record_date_accepts_multiple_representations(use_case, repo, raw_date):
    """Strings, timestamps and dates all coerce to a plain date."""
    use_case.execute_from_dataframe(pd.DataFrame([_row(record_date=raw_date)]))

    assert repo.saved[0].record_date == date(2026, 8, 15)


def test_numeric_strings_are_coerced(use_case, repo):
    """CSV columns arriving as text are converted, not passed through."""
    use_case.execute_from_dataframe(pd.DataFrame([_row(sleep_hours="7.5")]))

    assert repo.saved[0].sleep_hours == 7.5
    assert isinstance(repo.saved[0].sleep_hours, float)


def test_athlete_id_is_stringified(use_case, repo):
    """A numeric athlete id keeps its identity as a string."""
    use_case.execute_from_dataframe(pd.DataFrame([_row(athlete_id=1001)]))

    assert repo.saved[0].athlete_id == "1001"


def test_ingest_from_csv_round_trip(use_case, repo, tmp_path: Path):
    """execute_from_csv reads the file and ingests its rows."""
    csv = tmp_path / "sample.csv"
    pd.DataFrame([_row(), _row(athlete_id="ath-002")]).to_csv(csv, index=False)

    assert use_case.execute_from_csv(csv) == 2
    assert {r.athlete_id for r in repo.saved} == {"ath-001", "ath-002"}


def test_missing_csv_is_reported_clearly(use_case, tmp_path: Path):
    """A bad path fails as a validation error, not a bare OSError."""
    with pytest.raises(ValidationError, match="File not found"):
        use_case.execute_from_csv(tmp_path / "nope.csv")


def test_execute_from_records_passes_through(use_case, repo):
    """Domain records skip parsing and go straight to the repository."""
    use_case.execute_from_dataframe(pd.DataFrame([_row()]))
    already_built = list(repo.saved)
    repo.saved.clear()

    assert use_case.execute_from_records(already_built) == 1
