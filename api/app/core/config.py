from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    GEMINI_EXTRACT_MODEL: str = "gemini-2.5-flash"
    GEMINI_REQUEST_TIMEOUT_S: float = 30.0
    EXTRACT_MOMENTS_MAX_ATTEMPTS: int = 3
    REPLICATE_API_TOKEN: str | None = None
    REPLICATE_GIMP_MODEL: str | None = None
    REPLICATE_VIDEO_MODEL: str | None = None
    REPLICATE_GIMP_MODEL_VERSION: str | None = None
    REPLICATE_VIDEO_MODEL_VERSION: str | None = None
    GCS_BUCKET: str | None = None

    @property
    def replicate_gimp_identifier(self) -> str | None:
        return self.REPLICATE_GIMP_MODEL or self.REPLICATE_GIMP_MODEL_VERSION

    @property
    def replicate_video_identifier(self) -> str | None:
        return self.REPLICATE_VIDEO_MODEL or self.REPLICATE_VIDEO_MODEL_VERSION

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

__all__ = ["Settings", "get_settings", "settings"]
