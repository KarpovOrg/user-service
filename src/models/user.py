from sqlalchemy import (
    String,
    Boolean,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from .base import Base

from .mixins import (
    IdMixin,
    UidMixin,
    CreatedAtMixin,
)


class User(Base, IdMixin, UidMixin, CreatedAtMixin):
    __tablename__ = "users"
    __table_args__ = {"schema": "users_schema"}

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    surname: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

