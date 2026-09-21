from typing import Protocol

from app.schemas import User


class ProviderError(Exception):
    """Base error raised when the external provider cannot return a valid user."""


class UserNotFound(ProviderError):
    """Raised when the requested user does not exist in the provider."""


class ProviderTimeout(ProviderError):
    """Raised when the provider does not respond within the configured timeout."""


class UserProvider(Protocol):
    async def get_user(self, user_id: int) -> User: ...
