from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


BASE_DIR = Path(__file__).parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class AppConfig(BaseModel):
    app_name: str = "user-service"
    debug: bool = True


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    health: str = "/health"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


#class DatabaseConfig(BaseModel):
#    url: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="USER_CONFIG__",
    )
    app: AppConfig
    api: ApiPrefix = ApiPrefix()
    #db: DatabaseConfig


settings = Settings()