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
