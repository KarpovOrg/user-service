from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)
from starlette import status

from api.depends import get_user_service

from core.config import settings

from schemas import (
    UserResponse,
    UserCreateResponse,
    UserCreateRequest,
)

from services import UserService


router = APIRouter(
    prefix=settings.api.v1.users,
    tags=["Users"],
)


@router.get(
    path="/all",
    summary="Получить всех пользователей",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_users(
        service: Annotated[
            UserService,
            Depends(get_user_service)
        ]
):
    users = await service.get_all_users()
    return [
        UserResponse.model_validate(user)
        for user in users
    ]


@router.post(
    path="/create",
    summary="Получить всех пользователей",
    response_model=UserCreateResponse,
    status_code=status.HTTP_200_OK,
)
async def get_all_users(
        service: Annotated[
            UserService,
            Depends(get_user_service)
        ],
        schema: UserCreateRequest,
):
    user = await service.create_user(schema=schema)
    return UserCreateResponse(
        message=f"Пользователь успешно создан",
        name=user.name,
        surname=user.surname,
    )
