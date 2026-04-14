from typing import Annotated

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from services import UserService
from .session import get_db

from repositories import UserRepository


def get_user_repository(
        session: Annotated[
            AsyncSession,
            Depends(get_db),
        ],
) -> UserRepository:
    return UserRepository(session=session)


def get_user_service(
        user_repository: Annotated[
            UserRepository,
            Depends(get_user_repository),
        ],
) -> UserService:
    return UserService(user_repository=user_repository)