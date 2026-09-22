from app.cache.base import CacheError
from app.schemas import User


class FakeUserProvider:
    def __init__(self, failures: dict[int, Exception] | None = None) -> None:
        self._failures = failures or {}
        self.calls: list[int] = []

    async def get_user(self, user_id: int) -> User:
        self.calls.append(user_id)

        failure = self._failures.get(user_id)
        if failure is not None:
            raise failure

        return User(id=user_id, name=f"User {user_id}")


class FakeUserCache:
    def __init__(self, users: dict[int, User] | None = None) -> None:
        self.users = users or {}
        self.get_calls: list[int] = []
        self.set_calls: list[tuple[User, int]] = []
        self.get_error: CacheError | None = None
        self.set_error: CacheError | None = None

    async def get(self, user_id: int) -> User | None:
        self.get_calls.append(user_id)
        if self.get_error is not None:
            raise self.get_error
        return self.users.get(user_id)

    async def set(self, user: User, ttl_seconds: int) -> None:
        self.set_calls.append((user, ttl_seconds))
        if self.set_error is not None:
            raise self.set_error
        self.users[user.id] = user
