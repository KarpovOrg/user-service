import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


class UserBase(BaseModel):
    name: str
    surname: str


class UserCreateRequest(UserBase):
    pass


class UserCreateResponse(UserBase):
    message: str = "User created successfully"
    name: str
    surname: str


class UserResponse(UserBase):
    id: int
    uid: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )