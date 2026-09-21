import asyncio
import logging

from app.providers.base import (
    ProviderError,
    ProviderTimeout,
    UserNotFound,
    UserProvider,
)
from app.schemas import User, UserFetchError, UserFetchResponse

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, provider: UserProvider, max_concurrency: int) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be greater than zero")

        self._provider = provider
        self._max_concurrency = max_concurrency

    async def fetch_users(self, user_ids: list[int]) -> UserFetchResponse:
        semaphore = asyncio.Semaphore(self._max_concurrency)
        results = await asyncio.gather(
            *(self._fetch_user(user_id, semaphore) for user_id in user_ids)
        )

        users = [result for result in results if isinstance(result, User)]
        errors = [result for result in results if isinstance(result, UserFetchError)]

        return UserFetchResponse(
            users=users,
            failed=[error.id for error in errors],
            errors=errors,
        )

    async def _fetch_user(
        self, user_id: int, semaphore: asyncio.Semaphore
    ) -> User | UserFetchError:
        async with semaphore:
            try:
                return await self._provider.get_user(user_id)
            except UserNotFound:
                return UserFetchError(id=user_id, reason="not_found")
            except ProviderTimeout:
                return UserFetchError(id=user_id, reason="timeout")
            except ProviderError:
                return UserFetchError(id=user_id, reason="provider_error")
            except Exception:
                logger.exception("Unexpected error while fetching user %s", user_id)
                return UserFetchError(id=user_id, reason="provider_error")
