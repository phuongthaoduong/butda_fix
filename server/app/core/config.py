import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    ENVIRONMENT: str
    HOST: str
    PORT: int
    CORS_ORIGINS: list[str]
    REDIS_URL: str | None
    CACHE_TTL_SECONDS: int
    SEARCH_TIMEOUT_SECONDS: int

    def __init__(self) -> None:
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", 8001))
        origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        self.CORS_ORIGINS = [origin.strip() for origin in origins.split(",") if origin.strip()]
        self.REDIS_URL = os.getenv("REDIS_URL") or None
        self.CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        self.SEARCH_TIMEOUT_SECONDS = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "30"))


settings = get_settings()
ENVIRONMENT = settings.ENVIRONMENT
HOST = settings.HOST
PORT = settings.PORT
CORS_ORIGINS = settings.CORS_ORIGINS
REDIS_URL = settings.REDIS_URL
CACHE_TTL_SECONDS = settings.CACHE_TTL_SECONDS
SEARCH_TIMEOUT_SECONDS = settings.SEARCH_TIMEOUT_SECONDS
