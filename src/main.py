import uvicorn

from fastapi import FastAPI

from api import api_router

from core.config import settings


from core.lifespan import lifespan




def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.app_name,
        lifespan=lifespan
    )
    app.include_router(api_router, prefix=settings.api.prefix)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.app.host,
        port=settings.app.port,
    )