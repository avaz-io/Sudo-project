from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "University Event Manager API"
    database_url: str = "sqlite:///./event_manager.db"

    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    cors_origins: list[str] = ["http://localhost:5173"]
    university_timezone: str = "Asia/Tashkent"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
