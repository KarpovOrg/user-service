from fastapi import APIRouter

from core.config import settings


router = APIRouter(
    prefix=settings.api.v1.users,
    tags=["Health"],
)


@router.get("/health")
async def health_check():
    return {
        "service": "user-service",
        "status": "ok"
    }