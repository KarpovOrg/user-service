from typing import TypeVar

from pydantic import BaseModel

from sqlalchemy import (
    insert,
    select,
)

from sqlalchemy.ext.asyncio import AsyncSession


ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository:
    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ):
        self.session = session
        self.model = model

    async def get_all(self) -> list[ModelType]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def get_by_id(self, obj_id: int) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalar()

    async def get_by_uid(self, obj_uid: int) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.uid == obj_uid)
        )
        return result.scalar()

    async def create(self, schema: CreateSchemaType) -> ModelType:
        result = await self.session.execute(
            insert(self.model)
            .values(schema.model_dump())
            .returning(self.model)
        )
        await self.session.commit()
        return result.scalar()