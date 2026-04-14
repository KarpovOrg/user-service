from fastapi import APIRouter

from api.api_v1.health import router as health_router
from api.api_v1.users import router as users_router

from core.config import settings


router = APIRouter(
    prefix=settings.api.v1.prefix,
)


router.include_router(health_router)
router.include_router(users_router)
