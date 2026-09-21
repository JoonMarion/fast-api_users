from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request

from app.schemas import UserFetchRequest, UserFetchResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api")


def get_user_service(request: Request) -> UserService:
    return cast(UserService, request.app.state.user_service)


@router.post("/users/fetch", response_model=UserFetchResponse)
async def fetch_users(
    request_data: UserFetchRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserFetchResponse:
    return await service.fetch_users(request_data.user_ids)
