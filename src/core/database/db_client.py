from .base import BaseDatabaseClient

from core.config import settings


db_client = BaseDatabaseClient(
    url=settings.db.url,
)
