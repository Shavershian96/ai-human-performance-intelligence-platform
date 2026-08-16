"""Data processing pipeline - cleaning, feature engineering, ML dataset preparation."""

from typing import TYPE_CHECKING

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
        "acute_load_7d",
        "chronic_load_28d",
        "acwr",
    ]
    TARGET_COLUMN = "performance_score"

    # Spans for the exponentially weighted training loads, in days. 7/28 is the
    # convention in the training-load literature the acute:chronic ratio comes
    # from.
    ACUTE_SPAN = 7
    CHRONIC_SPAN = 28

    # Below this many distinct athletes, holding whole athletes out would leave
    # a test set too small to read, so the split falls back to row-wise.
    MIN_GROUPS_FOR_GROUP_SPLIT = 5

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
        critical = [
            "sleep_hours",
            "sleep_quality",
            "training_load",
            "stress_level",
            "recovery_score",
        ]
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

        df = self.add_load_history_features(df)

        return df

    @classmethod
    def add_load_history_features(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Add acute load, chronic load and their ratio, per athlete over time.

        The windows cover the days *before* each row: the load a session imposes
        has not yet accumulated into the athlete's rolling state when that
        session's performance is recorded, and including it would leak the row's
        own value into its features.

        Rows without a usable history - the first day for an athlete, or a frame
        that carries no athlete_id/record_date at all - fall back to the row's
        own load for both windows, which yields a neutral ratio of 1.0. That is
        the same fallback the prediction path uses when an athlete has no
        recorded history, so training and serving agree.
        """
        df = df.copy()
        own_load = df["training_load"].astype(float)

        if "athlete_id" not in df.columns or "record_date" not in df.columns:
            df["acute_load_7d"] = own_load
            df["chronic_load_28d"] = own_load
            df["acwr"] = 1.0
            return df

        order = df.sort_values(["athlete_id", "record_date"]).index
        ordered = df.loc[order]
        prior = ordered.groupby("athlete_id")["training_load"].shift(1)

        acute = prior.groupby(ordered["athlete_id"]).transform(
            lambda s: s.ewm(span=cls.ACUTE_SPAN, min_periods=1).mean()
        )
        chronic = prior.groupby(ordered["athlete_id"]).transform(
            lambda s: s.ewm(span=cls.CHRONIC_SPAN, min_periods=1).mean()
        )

        df["acute_load_7d"] = acute.reindex(df.index).fillna(own_load)
        df["chronic_load_28d"] = chronic.reindex(df.index).fillna(own_load)
        df["acwr"] = cls.compute_acwr(df["acute_load_7d"], df["chronic_load_28d"])
        return df

    @staticmethod
    def compute_acwr(acute: pd.Series, chronic: pd.Series) -> pd.Series:
        """Acute:chronic workload ratio, guarded against a negligible divisor.

        Clipped to [0.4, 2.0]: outside that band the ratio is dominated by a
        near-zero chronic load rather than by a real training pattern.
        """
        ratio = acute / chronic.where(chronic > 20.0)
        return ratio.fillna(1.0).clip(0.4, 2.0)

    def prepare_ml_dataset(
        self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
    ) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
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

        from sklearn.model_selection import GroupShuffleSplit, train_test_split

        # Split by athlete when we can. Consecutive days for one athlete are
        # highly correlated, and the load-history features are built from that
        # athlete's own past, so a plain row-wise split puts near-duplicate rows
        # on both sides and reports a score that flatters the model. Holding out
        # whole athletes answers the question that matters: does this work for
        # someone the model has never seen?
        groups = df_labeled["athlete_id"] if "athlete_id" in df_labeled.columns else None
        distinct = groups.nunique() if groups is not None else 0

        if groups is not None and distinct >= self.MIN_GROUPS_FOR_GROUP_SPLIT:
            splitter = GroupShuffleSplit(
                n_splits=1, test_size=test_size, random_state=random_state
            )
            train_idx, test_idx = next(splitter.split(X, y, groups=groups))
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            split_kind = "grouped-by-athlete"
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            split_kind = "row-wise"

        logger.info(
            "Prepared ML dataset",
            train_samples=len(X_train),
            test_samples=len(X_test),
            split=split_kind,
            athletes=distinct,
        )
        return X_train, y_train, X_test, y_test

    def run(
        self, test_size: float = 0.2, random_state: int = 42
    ) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """
        Run full pipeline: load -> clean -> features -> split.
        """
        df = self.load_raw_data()
        if df.empty:
            raise ValueError("No data found in database")

        df = self.clean_data(df)
        df = self.feature_engineering(df)
        return self.prepare_ml_dataset(df, test_size=test_size, random_state=random_state)
