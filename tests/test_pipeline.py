"""Data processing pipeline tests: cleaning, feature engineering, dataset prep.

The pipeline talks to a repository port, so these use a stub implementation
rather than a database.
"""

import pandas as pd
import pytest

from src.services.processing.pipeline import DataProcessingPipeline


class StubRepo:
    """Minimal PerformanceRepositoryPort implementation backed by a DataFrame."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def load_all(self) -> pd.DataFrame:
        return self._df.copy()


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


def _frame(n: int = 12, **overrides) -> pd.DataFrame:
    return pd.DataFrame([_row(**overrides) for _ in range(n)])


@pytest.fixture
def pipeline() -> DataProcessingPipeline:
    return DataProcessingPipeline(StubRepo(_frame()))


# --- cleaning ---------------------------------------------------------------


def test_clean_drops_rows_missing_critical_fields(pipeline):
    """A row without a critical measurement cannot be used and is dropped."""
    df = _frame(3)
    df.loc[1, "recovery_score"] = None

    cleaned = pipeline.clean_data(df)

    assert len(cleaned) == 2
    assert cleaned["recovery_score"].notna().all()


def test_clean_keeps_rows_missing_only_optional_fields(pipeline):
    """hrv and resting_heart_rate are optional, so their absence is tolerated."""
    df = _frame(3)
    df.loc[0, "hrv"] = None
    df.loc[1, "resting_heart_rate"] = None

    assert len(pipeline.clean_data(df)) == 3


@pytest.mark.parametrize(
    ("column", "raw", "expected"),
    [
        ("sleep_hours", 99.0, 24.0),
        ("sleep_hours", -5.0, 0.0),
        ("sleep_quality", 50.0, 10.0),
        ("sleep_quality", 0.0, 1.0),
        ("stress_level", 42.0, 10.0),
        ("recovery_score", 78.0, 10.0),
        ("training_load", 5000.0, 1000.0),
        ("resting_heart_rate", 300.0, 120.0),
        ("hrv", 900.0, 200.0),
    ],
)
def test_clean_clips_out_of_range_values(pipeline, column, raw, expected):
    """Implausible readings are clamped to the documented bounds, not dropped."""
    df = _frame(2)
    df.loc[0, column] = raw

    cleaned = pipeline.clean_data(df)

    assert cleaned.loc[0, column] == expected


def test_clean_does_not_mutate_input(pipeline):
    """Cleaning returns a copy; the caller's frame is left intact."""
    df = _frame(2)
    df.loc[0, "sleep_hours"] = 99.0

    pipeline.clean_data(df)

    assert df.loc[0, "sleep_hours"] == 99.0


# --- feature engineering ----------------------------------------------------


def test_feature_engineering_adds_every_model_feature(pipeline):
    """The engineered frame carries exactly the columns the model expects."""
    engineered = pipeline.feature_engineering(_frame(5))

    for column in DataProcessingPipeline.FEATURE_COLUMNS:
        assert column in engineered.columns


def test_derived_ratios_are_computed_correctly(pipeline):
    """sleep_recovery_ratio and load_stress_ratio follow their definitions."""
    df = _frame(1, sleep_hours=8.0, sleep_quality=9.0, recovery_score=6.0,
                training_load=300.0, stress_level=5.0)

    engineered = pipeline.feature_engineering(df)

    assert engineered.loc[0, "sleep_recovery_ratio"] == pytest.approx(8.0 * 9.0 / 6.0, rel=1e-4)
    assert engineered.loc[0, "load_stress_ratio"] == pytest.approx(300.0 / 5.0, rel=1e-4)


def test_missing_optional_features_filled_with_median(pipeline):
    """A missing hrv takes the column median rather than propagating NaN."""
    df = _frame(3)
    df["hrv"] = [40.0, None, 60.0]

    engineered = pipeline.feature_engineering(df)

    assert engineered["hrv_filled"].notna().all()
    assert engineered.loc[1, "hrv_filled"] == pytest.approx(50.0)


def test_absent_optional_columns_get_defaults(pipeline):
    """A source without hrv/resting_heart_rate at all still yields features."""
    df = _frame(3).drop(columns=["hrv", "resting_heart_rate"])

    engineered = pipeline.feature_engineering(df)

    assert engineered["hrv_filled"].eq(50.0).all()
    assert engineered["resting_heart_rate_filled"].eq(60.0).all()


def test_ratios_survive_zero_recovery_and_stress(pipeline):
    """The epsilon guard keeps the ratios finite instead of dividing by zero."""
    df = _frame(1, recovery_score=0.0, stress_level=0.0)

    engineered = pipeline.feature_engineering(df)

    assert pd.notna(engineered.loc[0, "sleep_recovery_ratio"])
    assert pd.notna(engineered.loc[0, "load_stress_ratio"])


# --- dataset preparation ----------------------------------------------------


def test_prepare_rejects_too_few_labelled_rows(pipeline):
    """Below the documented minimum, training is refused with a clear message."""
    df = pipeline.feature_engineering(_frame(9))

    with pytest.raises(ValueError, match="at least 10"):
        pipeline.prepare_ml_dataset(df)


def test_prepare_ignores_unlabelled_rows(pipeline):
    """Rows without a performance_score cannot train and are excluded."""
    df = _frame(12)
    df.loc[:1, "performance_score"] = None
    df = pipeline.feature_engineering(df)

    X_train, y_train, X_test, y_test = pipeline.prepare_ml_dataset(df)

    assert len(X_train) + len(X_test) == 10


def test_prepare_splits_and_selects_feature_columns(pipeline):
    """The split honours test_size and exposes only the model's features."""
    df = pipeline.feature_engineering(_frame(20))

    X_train, y_train, X_test, y_test = pipeline.prepare_ml_dataset(df, test_size=0.25)

    assert len(X_test) == 5
    assert len(X_train) == 15
    assert len(y_train) == len(X_train)
    assert list(X_train.columns) == DataProcessingPipeline.FEATURE_COLUMNS


def test_split_is_deterministic_for_a_given_seed(pipeline):
    """Same random_state produces the same split, so runs are reproducible."""
    df = pipeline.feature_engineering(_frame(20))

    first, _, _, _ = pipeline.prepare_ml_dataset(df, random_state=7)
    second, _, _, _ = pipeline.prepare_ml_dataset(df, random_state=7)

    assert list(first.index) == list(second.index)


def test_run_executes_the_full_pipeline():
    """run() loads, cleans, engineers and splits in one pass."""
    df = _frame(20)
    df.loc[0, "sleep_hours"] = 99.0  # gets clipped on the way through
    pipeline = DataProcessingPipeline(StubRepo(df))

    X_train, y_train, X_test, y_test = pipeline.run()

    assert len(X_train) + len(X_test) == 20
    assert list(X_train.columns) == DataProcessingPipeline.FEATURE_COLUMNS
    assert X_train.notna().all().all()
