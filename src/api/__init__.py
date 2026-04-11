from fastapi import APIRouter

from api.api_v1 import router as router_v1


api_router = APIRouter()


api_router.include_router(router_v1)