import asyncio
import logging

import pytest

from app.schemas import User
from app.services.user_service import UserService
from tests.fakes import FakeUserProvider


class ConcurrencyTrackingProvider:
    def __init__(self, expected_concurrency: int) -> None:
        self._expected_concurrency = expected_concurrency
        self._release = asyncio.Event()
        self.active = 0
        self.max_active = 0

    async def get_user(self, user_id: int) -> User:
        self.active += 1
        self.max_active = max(self.max_active, self.active)

        if self.active == self._expected_concurrency:
            self._release.set()

        try:
            await self._release.wait()
            return User(id=user_id, name=f"User {user_id}")
        finally:
            self.active -= 1


async def test_service_limits_concurrency() -> None:
    provider = ConcurrencyTrackingProvider(expected_concurrency=2)
    service = UserService(provider, max_concurrency=2)

    result = await service.fetch_users([1, 2, 3, 4])

    assert provider.max_active == 2
    assert [user.id for user in result.users] == [1, 2, 3, 4]


async def test_service_logs_fetch_summary(caplog: pytest.LogCaptureFixture) -> None:
    provider = FakeUserProvider({2: RuntimeError("unexpected failure")})
    service = UserService(provider, max_concurrency=2)

    with caplog.at_level(logging.INFO, logger="app.services.user_service"):
        await service.fetch_users([1, 2, 3])

    summary = next(
        record
        for record in caplog.records
        if getattr(record, "event", None) == "users_fetch_completed"
    )
    assert summary.requested_count == 3
    assert summary.succeeded_count == 2
    assert summary.failed_count == 1


async def test_unexpected_error_is_logged_and_mapped_to_provider_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    provider = FakeUserProvider({2: RuntimeError("unexpected failure")})
    service = UserService(provider, max_concurrency=2)

    with caplog.at_level(logging.ERROR, logger="app.services.user_service"):
        result = await service.fetch_users([1, 2, 3])

    assert [user.id for user in result.users] == [1, 3]
    assert result.failed == [2]
    assert result.errors[0].reason == "provider_error"
    error_record = next(
        record
        for record in caplog.records
        if getattr(record, "event", None) == "unexpected_provider_error"
    )
    assert error_record.user_id == 2
