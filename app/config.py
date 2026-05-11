from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    app_log_level: str = "INFO"
    app_jwt_secret: str = "change-me-in-prod"
    app_jwt_alg: str = "HS256"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/aidocs"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "aidocs-uploads"

    openai_api_key: str = Field(default="")
    llm_model: str = "gpt-4.1"
    llm_temperature: float = 0.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
