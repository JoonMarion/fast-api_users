import logging
from collections.abc import Awaitable, Callable

import httpx
import pytest
from app.providers.base import ProviderError, ProviderTimeout, UserNotFound
from app.providers.jsonplaceholder import JsonPlaceholderUserProvider
from app.schemas import User

Sleep = Callable[[float], Awaitable[None]]
Jitter = Callable[[float, float], float]


async def no_sleep(delay: float) -> None:
    return None


def no_jitter(lower: float, upper: float) -> float:
    return 0.0


async def get_user_with_transport(
    transport: httpx.MockTransport,
    *,
    max_retries: int = 0,
    sleep: Sleep = no_sleep,
    jitter: Jitter = no_jitter,
) -> User:
    async with httpx.AsyncClient(transport=transport) as client:
        provider = JsonPlaceholderUserProvider(
            client,
            "https://provider.test/",
            max_retries=max_retries,
            sleep=sleep,
            jitter=jitter,
        )
        return await provider.get_user(1)


async def test_provider_returns_only_public_user_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://provider.test/users/1"
        return httpx.Response(
            200,
            json={
                "id": 1,
                "name": "User One",
                "email": "private@example.test",
            },
        )

    user = await get_user_with_transport(httpx.MockTransport(handler))

    assert user.model_dump() == {"id": 1, "name": "User One"}


async def test_provider_maps_404_to_user_not_found() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(404))

    with pytest.raises(UserNotFound):
        await get_user_with_transport(transport)


async def test_provider_maps_other_http_errors_to_provider_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(500))

    with pytest.raises(ProviderError):
        await get_user_with_transport(transport)


@pytest.mark.parametrize(
    ("payload", "content"),
    [
        ({"id": 1}, None),
        ({"id": 2, "name": "Wrong user"}, None),
        (None, b"not-json"),
    ],
)
async def test_provider_maps_invalid_payload_to_provider_error(
    payload: dict[str, object] | None, content: bytes | None
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if content is not None:
            return httpx.Response(200, content=content)
        return httpx.Response(200, json=payload)

    with pytest.raises(ProviderError):
        await get_user_with_transport(httpx.MockTransport(handler))


@pytest.mark.parametrize(
    ("httpx_error", "expected_error"),
    [
        (httpx.ReadTimeout, ProviderTimeout),
        (httpx.ConnectError, ProviderError),
    ],
)
async def test_provider_maps_transport_errors(
    httpx_error: type[httpx.RequestError], expected_error: type[ProviderError]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx_error("request failed", request=request)

    with pytest.raises(expected_error):
        await get_user_with_transport(httpx.MockTransport(handler))


async def test_provider_retries_429_using_retry_after(
    caplog: pytest.LogCaptureFixture,
) -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"id": 1, "name": "User One"})

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    with caplog.at_level(logging.WARNING, logger="app.providers.jsonplaceholder"):
        user = await get_user_with_transport(
            httpx.MockTransport(handler),
            max_retries=2,
            sleep=record_sleep,
        )

    assert user == User(id=1, name="User One")
    assert attempts == 2
    assert delays == [2.0]
    retry_record = next(
        record
        for record in caplog.records
        if getattr(record, "event", None) == "provider_retry"
    )
    assert retry_record.user_id == 1
    assert retry_record.attempt == 2
    assert retry_record.max_attempts == 3
    assert retry_record.delay_seconds == 2.0
    assert retry_record.retry_reason == "http_429"
    assert retry_record.retry_after_used is True


async def test_provider_retries_transient_http_errors_with_backoff_and_jitter() -> None:
    attempts = 0
    delays: list[float] = []
    jitter_limits: list[tuple[float, float]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503)
        return httpx.Response(200, json={"id": 1, "name": "User One"})

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    def fixed_jitter(lower: float, upper: float) -> float:
        jitter_limits.append((lower, upper))
        return 0.1

    user = await get_user_with_transport(
        httpx.MockTransport(handler),
        max_retries=2,
        sleep=record_sleep,
        jitter=fixed_jitter,
    )

    assert user == User(id=1, name="User One")
    assert attempts == 3
    assert jitter_limits == [(0, 0.25), (0, 0.5)]
    assert delays == [0.35, 0.6]


async def test_provider_retries_timeout_before_succeeding() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout("request timed out", request=request)
        return httpx.Response(200, json={"id": 1, "name": "User One"})

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    user = await get_user_with_transport(
        httpx.MockTransport(handler),
        max_retries=1,
        sleep=record_sleep,
    )

    assert user == User(id=1, name="User One")
    assert attempts == 2
    assert delays == [0.25]


async def test_provider_stops_after_max_retries() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    with pytest.raises(ProviderError):
        await get_user_with_transport(
            httpx.MockTransport(handler),
            max_retries=2,
            sleep=record_sleep,
        )

    assert attempts == 3
    assert delays == [0.25, 0.5]
