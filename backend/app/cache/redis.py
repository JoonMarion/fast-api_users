import json
import logging
from typing import Protocol

from pydantic import ValidationError
from redis.exceptions import RedisError

from app.cache.base import CacheError
from app.schemas import User

logger = logging.getLogger(__name__)


class RedisClient(Protocol):
    async def get(self, key: str) -> str | bytes | None: ...

    async def set(self, key: str, value: str, *, ex: int) -> object: ...

    async def delete(self, key: str) -> object: ...


class RedisUserCache:
    def __init__(self, client: RedisClient) -> None:
        self._client = client

    async def get(self, user_id: int) -> User | None:
        key = _user_key(user_id)
        try:
            raw_value = await self._client.get(key)
        except RedisError as exc:
            raise CacheError(f"Could not read cache key {key}") from exc

        if raw_value is None:
            return None

        try:
            if isinstance(raw_value, bytes):
                raw_value = raw_value.decode("utf-8")
            user = User.model_validate(json.loads(raw_value))
            if user.id != user_id:
                raise ValueError("Cached user ID does not match its key")
            return user
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValidationError,
            TypeError,
            ValueError,
        ):
            logger.warning(
                "Discarding invalid cached user",
                extra={"event": "cache_invalid_payload", "user_id": user_id},
            )
            await self._delete_invalid_value(key, user_id)
            return None

    async def set(self, user: User, ttl_seconds: int) -> None:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be greater than zero")

        key = _user_key(user.id)
        payload = json.dumps(
            user.model_dump(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        try:
            await self._client.set(key, payload, ex=ttl_seconds)
        except RedisError as exc:
            raise CacheError(f"Could not write cache key {key}") from exc

    async def _delete_invalid_value(self, key: str, user_id: int) -> None:
        try:
            await self._client.delete(key)
        except RedisError:
            logger.warning(
                "Could not delete invalid cached user",
                extra={"event": "cache_delete_failed", "user_id": user_id},
            )


def _user_key(user_id: int) -> str:
    return f"user:{user_id}"
