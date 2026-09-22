import httpx
from app.api.routes import get_user_service
from app.config import Settings
from app.main import create_app
from app.providers.base import ProviderError, ProviderTimeout, UserNotFound
from app.services.user_service import UserService

from tests.fakes import FakeUserProvider

TEST_SETTINGS = Settings(
    provider_timeout_seconds=1.0,
    max_concurrency=2,
    provider_base_url="https://provider.test",
    frontend_origin="https://frontend.test",
    redis_url="redis://redis.test:6379/0",
    cache_ttl_seconds=300,
    cache_timeout_seconds=0.5,
)


async def post_user_ids(
    user_ids: list[int], provider: FakeUserProvider | None = None
) -> tuple[httpx.Response, FakeUserProvider]:
    fake_provider = provider or FakeUserProvider()
    service = UserService(fake_provider, max_concurrency=2)
    application = create_app(TEST_SETTINGS)

    def override_user_service() -> UserService:
        return service

    application.dependency_overrides[get_user_service] = override_user_service
    transport = httpx.ASGITransport(app=application)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/users/fetch",
            json={"user_ids": user_ids},
        )

    return response, fake_provider


async def test_fetch_users_success() -> None:
    response, provider = await post_user_ids([1, 2, 3])

    assert response.status_code == 200
    assert response.json() == {
        "users": [
            {"id": 1, "name": "User 1"},
            {"id": 2, "name": "User 2"},
            {"id": 3, "name": "User 3"},
        ],
        "failed": [],
        "errors": [],
    }
    assert provider.calls == [1, 2, 3]


async def test_one_failure_does_not_interrupt_other_users() -> None:
    provider = FakeUserProvider({3: ProviderError("provider failed")})

    response, _ = await post_user_ids([1, 3, 2], provider)

    assert response.status_code == 200
    assert response.json() == {
        "users": [
            {"id": 1, "name": "User 1"},
            {"id": 2, "name": "User 2"},
        ],
        "failed": [3],
        "errors": [{"id": 3, "reason": "provider_error"}],
    }


async def test_not_found_is_reported_without_interrupting_others() -> None:
    provider = FakeUserProvider({2: UserNotFound("not found")})

    response, _ = await post_user_ids([1, 2, 3], provider)

    assert response.status_code == 200
    assert [user["id"] for user in response.json()["users"]] == [1, 3]
    assert response.json()["failed"] == [2]
    assert response.json()["errors"] == [{"id": 2, "reason": "not_found"}]


async def test_timeout_is_reported_without_interrupting_others() -> None:
    provider = FakeUserProvider({2: ProviderTimeout("timed out")})

    response, _ = await post_user_ids([1, 2, 3], provider)

    assert response.status_code == 200
    assert [user["id"] for user in response.json()["users"]] == [1, 3]
    assert response.json()["failed"] == [2]
    assert response.json()["errors"] == [{"id": 2, "reason": "timeout"}]


async def test_duplicate_ids_are_removed_while_preserving_order() -> None:
    response, provider = await post_user_ids([3, 1, 3, 2, 1])

    assert response.status_code == 200
    assert [user["id"] for user in response.json()["users"]] == [3, 1, 2]
    assert provider.calls == [3, 1, 2]


async def test_empty_list_returns_422() -> None:
    response, provider = await post_user_ids([])

    assert response.status_code == 422
    assert provider.calls == []


async def test_non_positive_id_returns_422() -> None:
    response, provider = await post_user_ids([1, 0, -1])

    assert response.status_code == 422
    assert provider.calls == []


async def test_more_than_100_positions_returns_422_before_deduplication() -> None:
    response, provider = await post_user_ids([1] * 101)

    assert response.status_code == 422
    assert provider.calls == []


async def test_failed_and_errors_have_the_same_ids_in_the_same_order() -> None:
    provider = FakeUserProvider(
        {
            5: UserNotFound("not found"),
            2: ProviderTimeout("timed out"),
            4: ProviderError("provider failed"),
        }
    )

    response, _ = await post_user_ids([5, 3, 2, 1, 4], provider)

    assert response.status_code == 200
    body = response.json()
    assert [user["id"] for user in body["users"]] == [3, 1]
    assert body["failed"] == [5, 2, 4]
    assert [error["id"] for error in body["errors"]] == body["failed"]
    assert [error["reason"] for error in body["errors"]] == [
        "not_found",
        "timeout",
        "provider_error",
    ]
