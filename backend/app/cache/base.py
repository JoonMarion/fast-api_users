from typing import Protocol

from app.schemas import User


class CacheError(Exception):
    """Raised when the cache cannot complete an operation."""


class UserCache(Protocol):
    async def get(self, user_id: int) -> User | None: ...

    async def set(self, user: User, ttl_seconds: int) -> None: ...
