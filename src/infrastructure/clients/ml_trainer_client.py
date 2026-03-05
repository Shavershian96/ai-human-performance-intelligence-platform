"""HTTP client for ML Trainer service with resilience patterns.

Implements retry with exponential backoff and a lightweight circuit breaker
to reduce cascading failures when the trainer is unavailable.
"""

import asyncio
import time

import httpx

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class MLTrainerClient:
    """Client to trigger training on the ML Trainer microservice."""

    _consecutive_failures: int = 0
    _circuit_open_until: float = 0.0

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = (base_url or settings.ml_trainer_url).rstrip("/")
        self.timeout = timeout or settings.ml_trainer_timeout_seconds

    def _is_circuit_open(self) -> bool:
        return time.time() < self._circuit_open_until

    @classmethod
    def _record_failure(cls) -> None:
        cls._consecutive_failures += 1
        if cls._consecutive_failures >= settings.ml_trainer_circuit_breaker_failures:
            cls._circuit_open_until = (
                time.time() + settings.ml_trainer_circuit_breaker_reset_seconds
            )

    @classmethod
    def _record_success(cls) -> None:
        cls._consecutive_failures = 0
        cls._circuit_open_until = 0.0

    async def trigger_training(self) -> dict:
        """POST /v1/train with retries and circuit breaker."""
        if self._is_circuit_open():
            raise RuntimeError(
                "ML trainer circuit breaker is open. "
                "Service is temporarily unavailable."
            )

        url = f"{self.base_url}/v1/train"
        last_error: Exception | None = None
        attempts = settings.ml_trainer_retry_attempts
        base_delay = settings.ml_trainer_retry_base_delay_seconds

        for attempt in range(1, attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url)
                    resp.raise_for_status()
                    payload = resp.json()
                    self._record_success()
                    return payload
            except Exception as exc:
                last_error = exc
                self._record_failure()
                if attempt < attempts:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "ML trainer call failed, retrying",
                        attempt=attempt,
                        max_attempts=attempts,
                        delay_seconds=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)

        raise RuntimeError(f"ML trainer request failed after {attempts} attempts: {last_error}")

    async def health(self) -> bool:
        """Check if ML Trainer is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/health/live")
                return r.status_code == 200
        except Exception:
            return False
