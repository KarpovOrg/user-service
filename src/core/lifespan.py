from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения")
    yield
    logger.info("Остановка приложения")