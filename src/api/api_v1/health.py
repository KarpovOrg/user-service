from fastapi import APIRouter

from core.config import settings


router = APIRouter(
    prefix=settings.api.v1.health,
    tags=["Health"],
)


@router.get("/")
async def health_check():
    return {
        "service": "auth-service",
        "status": "ok"
    }