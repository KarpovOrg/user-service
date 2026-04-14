import uuid

from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UidMixin:
    uid: Mapped[uuid.UUID] = mapped_column(
        UUID,
        unique=True,
        index=True,
        default=uuid.uuid4,
    )