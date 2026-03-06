"""Dark clean Streamlit dashboard for AI Human Performance Intelligence Platform."""

import asyncio
import os
import time
from typing import Any

import altair as alt
import httpx
import pandas as pd
import streamlit as st

API_URLS = [os.getenv("API_URL", "http://api:8000"), os.getenv("API_URL_LOCAL", "http://127.0.0.1:8000")]
PROM_URLS = [os.getenv("PROMETHEUS_URL", "http://prometheus:9090"), os.getenv("PROMETHEUS_URL_LOCAL", "http://127.0.0.1:9090")]
DASHBOARD_DEMO_MODE = os.getenv("DASHBOARD_DEMO_MODE", "true").lower() == "true"

st.set_page_config(page_title="AI Human Performance Dashboard", page_icon=" ", layout="wide")
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: Inter, "Helvetica Neue", Helvetica, Arial, sans-serif; }
[data-testid="stAppViewContainer"] { background: #0F1115; color: #E5E7EB; }
[data-testid="stSidebar"] { background: #141821; border-right: 1px solid #2A303C; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMetric"] { background:#171C25; border:1px solid #2A303C; border-radius:8px; padding:10px 12px; }
.status-item { display:flex; justify-content:space-between; margin:6px 0; color:#A8B0BE; font-size:12px; }
.status-badge { border:1px solid #3A4353; border-radius:10px; padding:1px 7px; font-size:11px; }
.empty-state { background:#171C25; border:1px solid #2A303C; border-radius:8px; padding:20px; color:#A8B0BE; }
.skeleton { height:12px; margin:8px 0; border-radius:6px; background: linear-gradient(90deg,#1B212D,#232B39,#1B212D); }
</style>
""",
    unsafe_allow_html=True,
)
st.title("AI Human Performance Intelligence Dashboard")
st.caption("Operational analytics and model monitoring")


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


async def _get_json(url: str, params: dict[str, Any] | None = None, retries: int = 4, timeout: float = 3.5) -> dict[str, Any] | list[Any] | None:
    delay = 0.4
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except Exception:
            if attempt < retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
    return None


def _first_result(bases: list[str], path: str, params: dict[str, Any] | None = None):
    for base in bases:
        payload = _run_async(_get_json(f"{base}{path}", params=params))
        if payload is not None:
            return payload
    return None


def _demo_predictions(limit: int) -> pd.DataFrame:
    n = min(limit, 120)
    now = pd.Timestamp.utcnow().floor("s")
    return pd.DataFrame(
        [
            {
                "id": n - i,
                "athlete_id": (i % 12) + 1,
                "prediction_date": (now - pd.Timedelta(hours=i)).date(),
                "performance_score": 82.0 + ((i * 5) % 130) / 10.0,
                "model_version": "v2.1",
                "created_at": (now - pd.Timedelta(hours=i)),
            }
            for i in range(n)
        ]
    )


def _demo_training(limit: int) -> pd.DataFrame:
    n = min(limit, 30)
    now = pd.Timestamp.utcnow()
    return pd.DataFrame(
        [
            {
                "run_date": now - pd.Timedelta(days=i),
                "model_version": "v2.1",
                "samples_used": 6200 + 100 * i,
                "test_mae": 2.9 + (i % 4) * 0.08,
                "test_rmse": 4.5 + (i % 4) * 0.12,
                "test_r2": 0.91 - (i % 3) * 0.01,
                "status": "success",
            }
            for i in range(n)
        ]
    )


def _demo_history(limit: int) -> pd.DataFrame:
    n = min(limit, 800)
    start = pd.Timestamp.utcnow().normalize() - pd.Timedelta(days=n)
    return pd.DataFrame(
        [
            {
                "athlete_id": (i % 20) + 1,
                "record_date": (start + pd.Timedelta(days=i)).date(),
                "sleep_hours": 6.1 + ((i * 3) % 25) / 10.0,
                "sleep_quality": 60 + (i % 30),
                "training_load": 45 + (i % 50),
                "stress_level": 3 + (i % 5),
                "recovery_score": 55 + (i % 35),
                "resting_heart_rate": 52 + (i % 16),
                "hrv": 55 + (i % 35),
                "performance_score": 72 + (i % 25),
            }
            for i in range(n)
        ]
    )


@st.cache_data(ttl=20)
def get_health(_nonce: int) -> dict[str, Any]:
    health = _first_result(API_URLS, "/health")
    ready = _first_result(API_URLS, "/health/ready")
    data: dict[str, Any] = {"api_ok": bool(health), "model_loaded": bool((health or {}).get("model_loaded", False))}
    if isinstance(ready, dict):
        data["db_ready"] = ready.get("status") == "ready"
    else:
        data["db_ready"] = False
    return data


@st.cache_data(ttl=20)
def fetch_predictions(_nonce: int, limit: int = 500) -> tuple[pd.DataFrame, bool]:
    payload = _first_result(API_URLS, "/v1/dashboard/predictions", {"limit": limit})
    if isinstance(payload, list):
        df = pd.DataFrame(payload)
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        return df, True
    return (_demo_predictions(limit), False) if DASHBOARD_DEMO_MODE else (pd.DataFrame(), False)


@st.cache_data(ttl=20)
def fetch_training_runs(_nonce: int, limit: int = 100) -> tuple[pd.DataFrame, bool]:
    payload = _first_result(API_URLS, "/v1/dashboard/training-runs", {"limit": limit})
    if isinstance(payload, list):
        df = pd.DataFrame(payload)
        if "run_date" in df.columns:
            df["run_date"] = pd.to_datetime(df["run_date"], errors="coerce")
        return df, True
    return (_demo_training(limit), False) if DASHBOARD_DEMO_MODE else (pd.DataFrame(), False)


@st.cache_data(ttl=20)
def fetch_historical_data(_nonce: int, limit: int = 5000) -> tuple[pd.DataFrame, bool]:
    payload = _first_result(API_URLS, "/v1/dashboard/historical", {"limit": limit})
    if isinstance(payload, list):
        df = pd.DataFrame(payload)
        if "record_date" in df.columns:
            df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce")
        return df, True
    return (_demo_history(limit), False) if DASHBOARD_DEMO_MODE else (pd.DataFrame(), False)


def _prom_query(expr: str) -> float | None:
    payload = _first_result(PROM_URLS, "/api/v1/query", {"query": expr})
    if not isinstance(payload, dict):
        return None
    result = payload.get("data", {}).get("result", [])
    if not result:
        return None
    try:
        return float(result[0]["value"][1])
    except Exception:
        return None


def _empty(title: str, text: str):
    st.markdown(f'<div class="empty-state"><div style="font-size:18px;font-weight:700;margin-bottom:6px;color:#E5E7EB;">{title}</div><div>{text}</div></div>', unsafe_allow_html=True)


def _skeleton_model_wait():
    st.markdown(
        """
<div class="empty-state">
  <div style="font-size:18px;font-weight:700;margin-bottom:8px;color:#E5E7EB;">Aguardando carregamento do modelo</div>
  <div style="margin-bottom:10px;">O endpoint /health retornou model_loaded=false.</div>
  <div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>
</div>
""",
        unsafe_allow_html=True,
    )


def _line_chart(df: pd.DataFrame, x_col: str, y_cols: list[str]):
    if df.empty:
        return
    src = df[[x_col] + y_cols].copy()
    melted = src.melt(id_vars=[x_col], value_vars=y_cols, var_name="series", value_name="value")
    chart = (
        alt.Chart(melted)
        .mark_line(strokeWidth=1.2)
        .encode(
            x=alt.X(f"{x_col}:T", axis=alt.Axis(grid=True, gridColor="#1D2330", labelColor="#9CA3AF", domainColor="#2A303C")),
            y=alt.Y("value:Q", axis=alt.Axis(grid=True, gridColor="#1D2330", labelColor="#9CA3AF", domainColor="#2A303C")),
            color=alt.Color("series:N", legend=None, scale=alt.Scale(range=["#D1D5DB", "#B6BCC7", "#969EAA"])),
            tooltip=[],
        )
        .properties(height=300)
        .configure_view(strokeOpacity=0, fill="#121722")
        .configure(background="#121722")
    )
    st.altair_chart(chart, use_container_width=True)


if "refresh_nonce" not in st.session_state:
    st.session_state.refresh_nonce = 0
st.sidebar.markdown("### Navigation")
page = st.sidebar.radio("View", ["Model Predictions", "Performance Metrics", "Historical Data", "System Status"])
if st.sidebar.button("Refresh Data"):
    with st.spinner("Refreshing data..."):
        st.cache_data.clear()
        st.session_state.refresh_nonce += 1
        time.sleep(0.25)

health = get_health(st.session_state.refresh_nonce)
api_ok = health.get("api_ok", False)
db_ready = health.get("db_ready", False)
model_loaded = health.get("model_loaded", False)
prom_ok = _prom_query("up") is not None

def _badge(value: str) -> str:
    return f'<span class="status-badge">{value}</span>'

st.sidebar.markdown("### System Status")
st.sidebar.markdown(f'<div class="status-item"><span>API</span>{_badge("ONLINE" if api_ok else "OFFLINE")}</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    f'<div class="status-item"><span>Database</span>{_badge("READY" if db_ready else ("DEMO" if DASHBOARD_DEMO_MODE else "UNAVAILABLE"))}</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f'<div class="status-item"><span>Model</span>{_badge("LOADED" if model_loaded else "WAITING")}</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f'<div class="status-item"><span>Prometheus</span>{_badge("ONLINE" if prom_ok else ("OPTIONAL" if DASHBOARD_DEMO_MODE else "UNAVAILABLE"))}</div>',
    unsafe_allow_html=True,
)

if page != "System Status" and not model_loaded:
    _skeleton_model_wait()
    st.stop()

if page == "Model Predictions":
    st.subheader("Model Predictions")
    df_pred, from_api = fetch_predictions(st.session_state.refresh_nonce)
    if df_pred.empty:
        _empty("Sem previsoes", "Nenhum registro disponivel para o periodo.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Predictions", f"{len(df_pred):,}")
        c2.metric("Latest Score", f"{df_pred['performance_score'].iloc[0]:.2f}")
        c3.metric("Unique Athletes", int(df_pred["athlete_id"].nunique()))
        _line_chart(df_pred.sort_values("created_at"), "created_at", ["performance_score"])
        st.dataframe(df_pred.head(180), use_container_width=True, hide_index=True)
        if not from_api:
            st.caption("Running in demo data mode.")

elif page == "Performance Metrics":
    st.subheader("Performance Metrics")
    df_train, from_api = fetch_training_runs(st.session_state.refresh_nonce)
    if df_train.empty:
        _empty("Sem runs de treinamento", "Execute o endpoint de treino para gerar metricas.")
    else:
        latest = df_train.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Model Version", str(latest.get("model_version", "N/A")))
        c2.metric("Test R²", f"{latest.get('test_r2'):.3f}" if pd.notna(latest.get("test_r2")) else "N/A")
        c3.metric("Test MAE", f"{latest.get('test_mae'):.3f}" if pd.notna(latest.get("test_mae")) else "N/A")
        c4.metric("Test RMSE", f"{latest.get('test_rmse'):.3f}" if pd.notna(latest.get("test_rmse")) else "N/A")
        cols = [c for c in ["test_mae", "test_rmse", "test_r2"] if c in df_train.columns]
        if cols:
            _line_chart(df_train.sort_values("run_date"), "run_date", cols)
        st.dataframe(df_train.head(120), use_container_width=True, hide_index=True)
        if not from_api:
            st.caption("Running in demo data mode.")

    req_rate = _prom_query("sum(rate(http_requests_total[5m]))")
    p95 = _prom_query("histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))")
    p1, p2 = st.columns(2)
    p1.metric("Req/sec (5m)", f"{req_rate:.3f}" if req_rate is not None else "N/A")
    p2.metric("Latency p95 (s)", f"{p95:.3f}" if p95 is not None else "N/A")

elif page == "Historical Data":
    st.subheader("Historical Data")
    df_hist, from_api = fetch_historical_data(st.session_state.refresh_nonce)
    if df_hist.empty:
        _empty("Sem historico", "Nenhum dado historico disponivel.")
    else:
        athletes = sorted(df_hist["athlete_id"].dropna().astype(str).unique().tolist())
        selected = st.multiselect("Athlete Filter", options=athletes, default=athletes[:5] if athletes else [])
        filtered = df_hist[df_hist["athlete_id"].astype(str).isin(selected)] if selected else df_hist
        c1, c2, c3 = st.columns(3)
        c1.metric("Records", f"{len(filtered):,}")
        c2.metric("Athletes", int(filtered["athlete_id"].nunique()))
        c3.metric("Date Range", f"{filtered['record_date'].min().date()} -> {filtered['record_date'].max().date()}")
        perf = (
            filtered.dropna(subset=["performance_score"])
            .sort_values("record_date")
            .groupby("record_date", as_index=False)["performance_score"]
            .mean()
        )
        if not perf.empty:
            _line_chart(perf, "record_date", ["performance_score"])
        st.dataframe(filtered.head(240), use_container_width=True, hide_index=True)
        if not from_api:
            st.caption("Running in demo data mode.")

else:
    st.subheader("System Status")
    st.json(
        {
            "api": "online" if api_ok else "offline",
            "database": "ready" if db_ready else ("demo" if DASHBOARD_DEMO_MODE else "unavailable"),
            "model_loaded": model_loaded,
            "prometheus": "online" if prom_ok else ("optional" if DASHBOARD_DEMO_MODE else "unavailable"),
            "demo_mode": DASHBOARD_DEMO_MODE,
        }
    )
