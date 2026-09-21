from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config import MAX_USER_IDS

PositiveUserId = Annotated[int, Field(strict=True, gt=0)]
FailureReason = Literal["not_found", "timeout", "provider_error"]


class User(BaseModel):
    model_config = ConfigDict(strict=True)

    id: PositiveUserId
    name: str


class UserFetchRequest(BaseModel):
    user_ids: Annotated[
        list[PositiveUserId], Field(min_length=1, max_length=MAX_USER_IDS)
    ]

    @field_validator("user_ids", mode="after")
    @classmethod
    def deduplicate_user_ids(cls, user_ids: list[int]) -> list[int]:
        return list(dict.fromkeys(user_ids))


class UserFetchError(BaseModel):
    id: PositiveUserId
    reason: FailureReason


class UserFetchResponse(BaseModel):
    users: list[User]
    failed: list[PositiveUserId]
    errors: list[UserFetchError]

    @model_validator(mode="after")
    def failed_ids_match_errors(self) -> "UserFetchResponse":
        if self.failed != [error.id for error in self.errors]:
            raise ValueError(
                "failed must contain the same IDs as errors in the same order"
            )
        return self
