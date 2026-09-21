import httpx
from pydantic import ValidationError

from app.providers.base import ProviderError, ProviderTimeout, UserNotFound
from app.schemas import User


class JsonPlaceholderUserProvider:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def get_user(self, user_id: int) -> User:
        try:
            response = await self._client.get(f"{self._base_url}/users/{user_id}")
        except httpx.TimeoutException as exc:
            raise ProviderTimeout(f"Provider timed out for user {user_id}") from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Provider request failed for user {user_id}") from exc

        if response.status_code == httpx.codes.NOT_FOUND:
            raise UserNotFound(f"User {user_id} was not found")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Provider returned HTTP {response.status_code} for user {user_id}"
            ) from exc

        try:
            user = User.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise ProviderError(
                f"Provider returned invalid data for user {user_id}"
            ) from exc

        if user.id != user_id:
            raise ProviderError(f"Provider returned a different user for ID {user_id}")

        return user
