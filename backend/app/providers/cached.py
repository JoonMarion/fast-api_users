import logging

from app.cache.base import CacheError, UserCache
from app.providers.base import UserProvider
from app.schemas import User

logger = logging.getLogger(__name__)


class CachedUserProvider:
    def __init__(
        self,
        provider: UserProvider,
        cache: UserCache,
        ttl_seconds: int,
    ) -> None:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be greater than zero")

        self._provider = provider
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    async def get_user(self, user_id: int) -> User:
        try:
            cached_user = await self._cache.get(user_id)
        except CacheError:
            logger.warning(
                "Cache read failed; falling back to provider",
                extra={"event": "cache_read_failed", "user_id": user_id},
                exc_info=True,
            )
        else:
            if cached_user is not None:
                logger.info(
                    "User cache hit",
                    extra={"event": "cache_hit", "user_id": user_id},
                )
                return cached_user

            logger.info(
                "User cache miss",
                extra={"event": "cache_miss", "user_id": user_id},
            )

        user = await self._provider.get_user(user_id)

        try:
            await self._cache.set(user, self._ttl_seconds)
        except CacheError:
            logger.warning(
                "Cache write failed; returning provider result",
                extra={"event": "cache_write_failed", "user_id": user_id},
                exc_info=True,
            )

        return user
