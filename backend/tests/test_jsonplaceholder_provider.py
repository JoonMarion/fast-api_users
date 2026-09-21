import httpx
import pytest

from app.providers.base import ProviderError, ProviderTimeout, UserNotFound
from app.providers.jsonplaceholder import JsonPlaceholderUserProvider
from app.schemas import User


async def get_user_with_transport(transport: httpx.MockTransport) -> User:
    async with httpx.AsyncClient(transport=transport) as client:
        provider = JsonPlaceholderUserProvider(client, "https://provider.test/")
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
