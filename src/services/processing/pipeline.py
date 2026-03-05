"""Data processing pipeline - cleaning, feature engineering, ML dataset preparation."""

from typing import TYPE_CHECKING, Tuple

import pandas as pd

from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.domain.ports import PerformanceRepositoryPort

logger = get_logger(__name__)


class DataProcessingPipeline:
    """
    Pipeline that:
    1. Loads raw performance data
    2. Cleans and validates
    3. Performs feature engineering
    4. Prepares train/test datasets for ML
    """

    FEATURE_COLUMNS = [
        "sleep_hours",
        "sleep_quality",
        "training_load",
        "stress_level",
        "recovery_score",
        "resting_heart_rate_filled",
        "hrv_filled",
        "sleep_recovery_ratio",
        "load_stress_ratio",
    ]
    TARGET_COLUMN = "performance_score"

    def __init__(self, performance_repo: "PerformanceRepositoryPort"):
        self._repo = performance_repo

    def load_raw_data(self) -> pd.DataFrame:
        """Load raw performance data from repository."""
        df = self._repo.load_all()
        logger.info("Loaded raw data", rows=len(df))
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate data."""
        df = df.copy()

        # Drop rows with missing critical fields
        critical = ["sleep_hours", "sleep_quality", "training_load", "stress_level", "recovery_score"]
        df = df.dropna(subset=critical)

        # Clip numeric ranges to plausible values
        df["sleep_hours"] = df["sleep_hours"].clip(0, 24)
        df["sleep_quality"] = df["sleep_quality"].clip(1, 10)
        df["stress_level"] = df["stress_level"].clip(1, 10)
        df["recovery_score"] = df["recovery_score"].clip(1, 10)
        df["training_load"] = df["training_load"].clip(0, 1000)

        if "resting_heart_rate" in df.columns:
            df["resting_heart_rate"] = df["resting_heart_rate"].clip(30, 120)
        if "hrv" in df.columns:
            df["hrv"] = df["hrv"].clip(0, 200)

        logger.info("Cleaned data", rows=len(df))
        return df

    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived features for ML."""
        df = df.copy()

        # Fill missing optional features with median
        if "resting_heart_rate" in df.columns:
            median_hr = df["resting_heart_rate"].median()
            df["resting_heart_rate_filled"] = df["resting_heart_rate"].fillna(median_hr)
        else:
            df["resting_heart_rate_filled"] = 60.0  # default

        if "hrv" in df.columns:
            median_hrv = df["hrv"].median()
            df["hrv_filled"] = df["hrv"].fillna(median_hrv)
        else:
            df["hrv_filled"] = 50.0  # default

        # Derived features
        df["sleep_recovery_ratio"] = (df["sleep_hours"] * df["sleep_quality"]) / (
            df["recovery_score"] + 1e-6
        )
        df["load_stress_ratio"] = df["training_load"] / (df["stress_level"] + 1e-6)

        return df

    def prepare_ml_dataset(
        self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """
        Split into train/test with features and target.

        Returns: X_train, y_train, X_test, y_test
        """
        # Filter rows that have performance_score (required for training)
        df_labeled = df.dropna(subset=[self.TARGET_COLUMN])
        if len(df_labeled) < 10:
            raise ValueError(
                f"Insufficient labeled data for ML: {len(df_labeled)} rows. Need at least 10."
            )

        X = df_labeled[self.FEATURE_COLUMNS].copy()
        y = df_labeled[self.TARGET_COLUMN]

        from sklearn.model_selection import train_test_split

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        logger.info(
            "Prepared ML dataset",
            train_samples=len(X_train),
            test_samples=len(X_test),
        )
        return X_train, y_train, X_test, y_test

    def run(
        self, test_size: float = 0.2, random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """
        Run full pipeline: load -> clean -> features -> split.
        """
        df = self.load_raw_data()
        if df.empty:
            raise ValueError("No data found in database")

        df = self.clean_data(df)
        df = self.feature_engineering(df)
        return self.prepare_ml_dataset(df, test_size=test_size, random_state=random_state)
