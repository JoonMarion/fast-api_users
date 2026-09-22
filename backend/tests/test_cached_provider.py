import logging

import pytest
from app.cache.base import CacheError
from app.providers.base import ProviderError
from app.providers.cached import CachedUserProvider
from app.schemas import User

from tests.fakes import FakeUserCache, FakeUserProvider


async def test_cache_hit_does_not_call_provider() -> None:
    cached_user = User(id=1, name="Cached User")
    cache = FakeUserCache({1: cached_user})
    provider = FakeUserProvider()
    cached_provider = CachedUserProvider(provider, cache, ttl_seconds=300)

    result = await cached_provider.get_user(1)

    assert result == cached_user
    assert cache.get_calls == [1]
    assert cache.set_calls == []
    assert provider.calls == []


async def test_cache_miss_calls_provider_and_sets_cache() -> None:
    cache = FakeUserCache()
    provider = FakeUserProvider()
    cached_provider = CachedUserProvider(provider, cache, ttl_seconds=120)

    result = await cached_provider.get_user(1)

    assert result == User(id=1, name="User 1")
    assert provider.calls == [1]
    assert cache.set_calls == [(result, 120)]


async def test_cache_read_error_falls_back_to_provider(
    caplog: pytest.LogCaptureFixture,
) -> None:
    cache = FakeUserCache()
    cache.get_error = CacheError("unavailable")
    provider = FakeUserProvider()
    cached_provider = CachedUserProvider(provider, cache, ttl_seconds=300)

    with caplog.at_level(logging.WARNING, logger="app.providers.cached"):
        result = await cached_provider.get_user(1)

    assert result == User(id=1, name="User 1")
    assert provider.calls == [1]
    assert any(
        getattr(record, "event", None) == "cache_read_failed"
        for record in caplog.records
    )


async def test_cache_write_error_does_not_discard_provider_result(
    caplog: pytest.LogCaptureFixture,
) -> None:
    cache = FakeUserCache()
    cache.set_error = CacheError("unavailable")
    provider = FakeUserProvider()
    cached_provider = CachedUserProvider(provider, cache, ttl_seconds=300)

    with caplog.at_level(logging.WARNING, logger="app.providers.cached"):
        result = await cached_provider.get_user(1)

    assert result == User(id=1, name="User 1")
    assert any(
        getattr(record, "event", None) == "cache_write_failed"
        for record in caplog.records
    )


async def test_provider_error_is_not_cached() -> None:
    cache = FakeUserCache()
    provider = FakeUserProvider({1: ProviderError("provider failed")})
    cached_provider = CachedUserProvider(provider, cache, ttl_seconds=300)

    with pytest.raises(ProviderError):
        await cached_provider.get_user(1)

    assert cache.set_calls == []
