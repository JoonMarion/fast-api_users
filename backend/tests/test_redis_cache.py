import pytest
from app.cache.base import CacheError
from app.cache.redis import RedisUserCache
from app.schemas import User
from redis.exceptions import RedisError


class FakeRedisClient:
    def __init__(self) -> None:
        self.values: dict[str, str | bytes] = {}
        self.set_calls: list[tuple[str, str, int]] = []
        self.deleted: list[str] = []
        self.get_error: RedisError | None = None
        self.set_error: RedisError | None = None
        self.delete_error: RedisError | None = None

    async def get(self, key: str) -> str | bytes | None:
        if self.get_error is not None:
            raise self.get_error
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ex: int) -> None:
        if self.set_error is not None:
            raise self.set_error
        self.set_calls.append((key, value, ex))
        self.values[key] = value

    async def delete(self, key: str) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.deleted.append(key)
        self.values.pop(key, None)


def create_cache(client: FakeRedisClient) -> RedisUserCache:
    return RedisUserCache(client)


async def test_cache_returns_none_on_miss() -> None:
    cache = create_cache(FakeRedisClient())

    assert await cache.get(1) is None


async def test_cache_returns_valid_user() -> None:
    client = FakeRedisClient()
    client.values["user:1"] = b'{"id":1,"name":"User One"}'
    cache = create_cache(client)

    assert await cache.get(1) == User(id=1, name="User One")


async def test_cache_sets_minimal_payload_with_ttl() -> None:
    client = FakeRedisClient()
    cache = create_cache(client)

    await cache.set(User(id=1, name="User One"), ttl_seconds=300)

    assert client.set_calls == [("user:1", '{"id":1,"name":"User One"}', 300)]


@pytest.mark.parametrize(
    "payload",
    [b"not-json", '{"id":1}', b"\xff"],
)
async def test_invalid_payload_is_deleted_and_treated_as_miss(
    payload: str | bytes,
) -> None:
    client = FakeRedisClient()
    client.values["user:1"] = payload
    cache = create_cache(client)

    assert await cache.get(1) is None
    assert client.deleted == ["user:1"]


async def test_payload_with_different_user_id_is_treated_as_miss() -> None:
    client = FakeRedisClient()
    client.values["user:1"] = '{"id":2,"name":"Wrong User"}'
    cache = create_cache(client)

    assert await cache.get(1) is None
    assert client.deleted == ["user:1"]


async def test_cache_read_error_is_translated() -> None:
    client = FakeRedisClient()
    client.get_error = RedisError("unavailable")
    cache = create_cache(client)

    with pytest.raises(CacheError):
        await cache.get(1)


async def test_cache_write_error_is_translated() -> None:
    client = FakeRedisClient()
    client.set_error = RedisError("unavailable")
    cache = create_cache(client)

    with pytest.raises(CacheError):
        await cache.set(User(id=1, name="User One"), ttl_seconds=300)
