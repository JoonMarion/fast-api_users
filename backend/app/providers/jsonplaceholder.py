import asyncio
import random
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from math import isfinite

import httpx
from pydantic import ValidationError

from app.providers.base import ProviderError, ProviderTimeout, UserNotFound
from app.schemas import User

DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_SECONDS = 0.25
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})

Sleep = Callable[[float], Awaitable[None]]
Jitter = Callable[[float, float], float]


class JsonPlaceholderUserProvider:
    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        sleep: Sleep = asyncio.sleep,
        jitter: Jitter = random.uniform,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if backoff_seconds <= 0:
            raise ValueError("backoff_seconds must be greater than zero")

        self._client = client
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep
        self._jitter = jitter

    async def get_user(self, user_id: int) -> User:
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.get(f"{self._base_url}/users/{user_id}")
            except httpx.TimeoutException as exc:
                if attempt < self._max_retries:
                    await self._wait_before_retry(attempt)
                    continue
                raise ProviderTimeout(f"Provider timed out for user {user_id}") from exc
            except httpx.RequestError as exc:
                if attempt < self._max_retries:
                    await self._wait_before_retry(attempt)
                    continue
                raise ProviderError(
                    f"Provider request failed for user {user_id}"
                ) from exc

            if response.status_code == httpx.codes.NOT_FOUND:
                raise UserNotFound(f"User {user_id} was not found")

            if (
                response.status_code in RETRYABLE_STATUS_CODES
                and attempt < self._max_retries
            ):
                await self._wait_before_retry(attempt, response)
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ProviderError(
                    f"Provider returned HTTP {response.status_code} for user {user_id}"
                ) from exc

            try:
                user = User.model_validate(response.json())
            except (ValueError, ValidationError) as exc:
                raise ProviderError(
                    f"Provider returned invalid data for user {user_id}"
                ) from exc

            if user.id != user_id:
                raise ProviderError(
                    f"Provider returned a different user for ID {user_id}"
                )

            return user

        raise RuntimeError("Retry loop ended without a result")

    async def _wait_before_retry(
        self,
        attempt: int,
        response: httpx.Response | None = None,
    ) -> None:
        retry_after = _retry_after_seconds(response)
        if retry_after is not None:
            await self._sleep(retry_after)
            return

        backoff = self._backoff_seconds * (2**attempt)
        await self._sleep(backoff + self._jitter(0, backoff))


def _retry_after_seconds(response: httpx.Response | None) -> float | None:
    if response is None:
        return None

    raw_value = response.headers.get("Retry-After")
    if raw_value is None:
        return None

    try:
        seconds = float(raw_value)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(raw_value)
        except (TypeError, ValueError, OverflowError):
            return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())

    return seconds if isfinite(seconds) and seconds >= 0 else None
