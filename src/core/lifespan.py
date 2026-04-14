from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.logging import logger
from core.database import db_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения")
    yield
    logger.info("Закрытие соединений с БД...")
    await db_client.dispose()
    logger.info("Остановка приложения")