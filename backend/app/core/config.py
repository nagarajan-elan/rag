from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RAG Backend"
    app_version: str = "1.0.0"
    database_url: str
    jwt_secret_key: str = "dev-secret-key"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
