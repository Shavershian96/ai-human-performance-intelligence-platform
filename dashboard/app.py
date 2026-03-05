"""Streamlit dashboard for AI Human Performance Intelligence Platform.

Views:
- Model predictions (from PostgreSQL)
- Performance metrics (from PostgreSQL + Prometheus)
- Historical data trends (from PostgreSQL)
"""

import os
import sys
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import streamlit as st

# Add project root to import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrastructure.database.models import PerformanceData, Prediction, TrainingRun
from src.infrastructure.database.session import get_db

API_URL = os.getenv("API_URL", "http://api:8000")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

st.set_page_config(page_title="AI Human Performance Dashboard", page_icon="📊", layout="wide")
st.title("📊 AI Human Performance Intelligence Dashboard")
st.caption("Data from PostgreSQL and Prometheus")

st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select view",
    ["Model Predictions", "Performance Metrics", "Historical Data", "System Status"],
)
refresh = st.sidebar.button("Refresh Data")
if refresh:
    st.cache_data.clear()


@st.cache_data(ttl=30)
def fetch_predictions(limit: int = 500) -> pd.DataFrame:
    """Fetch prediction history from PostgreSQL."""
    with get_db() as session:
        rows = (
            session.query(Prediction)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
            .all()
        )
    return pd.DataFrame(
        [
            {
                "id": row.id,
                "athlete_id": row.athlete_id,
                "prediction_date": row.prediction_date,
                "performance_score": float(row.performance_score),
                "model_version": row.model_version,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    )


@st.cache_data(ttl=30)
def fetch_training_runs(limit: int = 100) -> pd.DataFrame:
    """Fetch training run metadata from PostgreSQL."""
    with get_db() as session:
        rows = (
            session.query(TrainingRun)
            .order_by(TrainingRun.run_date.desc())
            .limit(limit)
            .all()
        )
    return pd.DataFrame(
        [
            {
                "run_date": row.run_date,
                "model_version": row.model_version,
                "samples_used": row.samples_used,
                "test_mae": row.metrics.get("test_mae") if row.metrics else None,
                "test_rmse": row.metrics.get("test_rmse") if row.metrics else None,
                "test_r2": row.metrics.get("test_r2") if row.metrics else None,
                "status": row.status,
            }
            for row in rows
        ]
    )


@st.cache_data(ttl=30)
def fetch_historical_data(limit: int = 5000) -> pd.DataFrame:
    """Fetch historical performance data from PostgreSQL."""
    with get_db() as session:
        rows = (
            session.query(PerformanceData)
            .order_by(PerformanceData.record_date.desc())
            .limit(limit)
            .all()
        )
    return pd.DataFrame(
        [
            {
                "athlete_id": row.athlete_id,
                "record_date": row.record_date,
                "sleep_hours": row.sleep_hours,
                "sleep_quality": row.sleep_quality,
                "training_load": row.training_load,
                "stress_level": row.stress_level,
                "recovery_score": row.recovery_score,
                "resting_heart_rate": row.resting_heart_rate,
                "hrv": row.hrv,
                "performance_score": row.performance_score,
            }
            for row in rows
        ]
    )


def query_prometheus(expr: str) -> float | None:
    """Run an instant Prometheus query and return float result."""
    try:
        response = httpx.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": expr},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("data", {}).get("result", [])
        if not result:
            return None
        return float(result[0]["value"][1])
    except Exception:
        return None


def check_api_health() -> dict[str, Any] | None:
    """Fetch API health endpoint."""
    try:
        response = httpx.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


if page == "Model Predictions":
    st.subheader("Model Predictions")
    df_pred = fetch_predictions()
    if df_pred.empty:
        st.info("No predictions found in PostgreSQL.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Predictions", f"{len(df_pred):,}")
        c2.metric("Latest Score", f"{df_pred['performance_score'].iloc[0]:.2f}")
        c3.metric("Unique Athletes", int(df_pred["athlete_id"].nunique()))

        st.markdown("**Predictions Over Time**")
        chart_df = (
            df_pred.sort_values("created_at")
            .set_index("created_at")[["performance_score"]]
        )
        st.line_chart(chart_df, use_container_width=True)

        st.markdown("**Recent Predictions**")
        st.dataframe(df_pred.head(200), use_container_width=True)

elif page == "Performance Metrics":
    st.subheader("Performance Metrics")

    df_train = fetch_training_runs()
    if not df_train.empty:
        latest = df_train.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Latest Model Version", str(latest["model_version"]))
        c2.metric("Latest Test R²", f"{latest['test_r2']:.3f}" if pd.notna(latest["test_r2"]) else "N/A")
        c3.metric("Latest Test MAE", f"{latest['test_mae']:.3f}" if pd.notna(latest["test_mae"]) else "N/A")
        c4.metric("Latest Test RMSE", f"{latest['test_rmse']:.3f}" if pd.notna(latest["test_rmse"]) else "N/A")

        st.markdown("**Training Metrics History**")
        metric_cols = [c for c in ["test_mae", "test_rmse", "test_r2"] if c in df_train.columns]
        if metric_cols:
            hist = df_train.sort_values("run_date").set_index("run_date")[metric_cols]
            st.line_chart(hist, use_container_width=True)
        st.dataframe(df_train.head(100), use_container_width=True)
    else:
        st.info("No training runs available.")

    st.markdown("---")
    st.markdown("**Runtime Metrics (Prometheus)**")

    req_rate = query_prometheus('sum(rate(http_requests_total[5m]))')
    p95 = query_prometheus('histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))')
    up_api = query_prometheus('up{job="api"}')
    up_ing = query_prometheus('up{job="data-ingestion"}')
    up_trainer = query_prometheus('up{job="ml-trainer"}')

    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Req/sec (5m)", f"{req_rate:.3f}" if req_rate is not None else "N/A")
    p2.metric("Latency p95 (s)", f"{p95:.3f}" if p95 is not None else "N/A")
    p3.metric("API Up", "Yes" if up_api == 1.0 else "No")
    p4.metric("Ingestion Up", "Yes" if up_ing == 1.0 else "No")
    p5.metric("Trainer Up", "Yes" if up_trainer == 1.0 else "No")

elif page == "Historical Data":
    st.subheader("Historical Data")
    df_hist = fetch_historical_data()
    if df_hist.empty:
        st.info("No historical records found in PostgreSQL.")
    else:
        athletes = sorted(df_hist["athlete_id"].dropna().unique().tolist())
        selected = st.multiselect("Athlete Filter", options=athletes, default=athletes[:5])
        filtered = df_hist[df_hist["athlete_id"].isin(selected)] if selected else df_hist

        c1, c2, c3 = st.columns(3)
        c1.metric("Records", f"{len(filtered):,}")
        c2.metric("Athletes", int(filtered["athlete_id"].nunique()))
        c3.metric(
            "Date Range",
            f"{filtered['record_date'].min()} → {filtered['record_date'].max()}",
        )

        st.markdown("**Historical Performance Score**")
        if filtered["performance_score"].notna().any():
            perf_chart = (
                filtered.dropna(subset=["performance_score"])
                .sort_values("record_date")
                .groupby("record_date", as_index=True)["performance_score"]
                .mean()
                .to_frame(name="avg_performance_score")
            )
            st.line_chart(perf_chart, use_container_width=True)

        st.markdown("**Key Feature Trends**")
        trend_cols = ["sleep_hours", "training_load", "stress_level", "recovery_score"]
        trend_df = (
            filtered.sort_values("record_date")
            .groupby("record_date", as_index=True)[trend_cols]
            .mean()
        )
        st.line_chart(trend_df, use_container_width=True)

        st.markdown("**Recent Historical Records**")
        st.dataframe(filtered.head(300), use_container_width=True)

else:
    st.subheader("System Status")

    health = check_api_health()
    if health:
        st.success("API reachable")
        st.json(health)
    else:
        st.error("API unreachable")

    prom_up = query_prometheus("up")
    if prom_up is None:
        st.warning("Prometheus unreachable or no metrics yet.")
    else:
        st.success("Prometheus reachable")
        st.caption(f"Prometheus up query result: {prom_up}")
