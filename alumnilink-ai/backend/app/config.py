from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "AlumniLink AI"
    app_env: str = "development"

    database_url: str = "postgresql+asyncpg://alumnilink:alumnilink_secret@localhost:5432/alumnilink_db"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "supersecretkey_change_in_prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    embedding_dimension: int = 384

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
