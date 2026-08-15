"""Resilience tests for the ML Trainer HTTP client.

These cover the retry/backoff and circuit-breaker behaviour the README claims,
without standing up the trainer: httpx is driven through a MockTransport and
asyncio.sleep is stubbed so the exponential delays are asserted rather than
waited on.
"""

import httpx
import pytest

from src.core.config import settings
from src.infrastructure.clients.ml_trainer_client import MLTrainerClient


@pytest.fixture(autouse=True)
def reset_breaker():
    """The breaker is class-level state, so isolate every test from the last."""
    MLTrainerClient._consecutive_failures = 0
    MLTrainerClient._circuit_open_until = 0.0
    yield
    MLTrainerClient._consecutive_failures = 0
    MLTrainerClient._circuit_open_until = 0.0


@pytest.fixture
def captured_sleeps(monkeypatch):
    """Record backoff delays instead of sleeping through them."""
    delays: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr(
        "src.infrastructure.clients.ml_trainer_client.asyncio.sleep", fake_sleep
    )
    return delays


def _client_with(monkeypatch, handler) -> MLTrainerClient:
    """Route the client's httpx calls into `handler`."""
    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(
        "src.infrastructure.clients.ml_trainer_client.httpx.AsyncClient", factory
    )
    return MLTrainerClient(base_url="http://ml-trainer:8080")


@pytest.mark.asyncio
async def test_returns_payload_on_success(monkeypatch, captured_sleeps):
    """A healthy trainer is called once and its JSON body returned as-is."""
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json={"status": "completed", "samples_used": 15})

    client = _client_with(monkeypatch, handler)
    result = await client.trigger_training()

    assert result == {"status": "completed", "samples_used": 15}
    assert calls == ["/v1/train"]
    assert captured_sleeps == []  # no retries on the happy path


@pytest.mark.asyncio
async def test_retries_then_succeeds(monkeypatch, captured_sleeps):
    """A transient failure is retried rather than surfaced to the caller."""
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"status": "completed"})

    client = _client_with(monkeypatch, handler)
    result = await client.trigger_training()

    assert result["status"] == "completed"
    assert attempts["n"] == 2
    assert len(captured_sleeps) == 1


@pytest.mark.asyncio
async def test_backoff_is_exponential(monkeypatch, captured_sleeps):
    """Delays double per attempt: base, 2x base, 4x base, ..."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = _client_with(monkeypatch, handler)
    with pytest.raises(RuntimeError):
        await client.trigger_training()

    base = settings.ml_trainer_retry_base_delay_seconds
    expected = [base * (2**i) for i in range(settings.ml_trainer_retry_attempts - 1)]
    assert captured_sleeps == expected


@pytest.mark.asyncio
async def test_exhausted_retries_raise(monkeypatch, captured_sleeps):
    """After the configured attempts the client gives up with a clear error."""
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return httpx.Response(500)

    client = _client_with(monkeypatch, handler)
    with pytest.raises(RuntimeError, match="failed after"):
        await client.trigger_training()

    assert attempts["n"] == settings.ml_trainer_retry_attempts


@pytest.mark.asyncio
async def test_circuit_opens_and_short_circuits(monkeypatch, captured_sleeps):
    """Once the breaker trips, callers fail fast without touching the network."""
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return httpx.Response(500)

    client = _client_with(monkeypatch, handler)

    # Drive enough failures to reach the threshold.
    while MLTrainerClient._consecutive_failures < settings.ml_trainer_circuit_breaker_failures:
        with pytest.raises(RuntimeError):
            await client.trigger_training()

    calls_before = attempts["n"]
    with pytest.raises(RuntimeError, match="circuit breaker is open"):
        await client.trigger_training()

    assert attempts["n"] == calls_before  # no request was issued


@pytest.mark.asyncio
async def test_success_resets_failure_count(monkeypatch, captured_sleeps):
    """A success clears the accumulated failures so the breaker stays closed."""
    state = {"fail": True}

    def handler(request: httpx.Request) -> httpx.Response:
        if state["fail"]:
            return httpx.Response(500)
        return httpx.Response(200, json={"status": "completed"})

    client = _client_with(monkeypatch, handler)

    with pytest.raises(RuntimeError):
        await client.trigger_training()
    assert MLTrainerClient._consecutive_failures > 0

    state["fail"] = False
    await client.trigger_training()
    assert MLTrainerClient._consecutive_failures == 0


@pytest.mark.asyncio
async def test_health_is_false_when_unreachable(monkeypatch):
    """health() reports status rather than propagating transport errors."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    client = _client_with(monkeypatch, handler)
    assert await client.health() is False
