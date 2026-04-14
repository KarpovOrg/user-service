from sqlalchemy import String
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

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    surname: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

