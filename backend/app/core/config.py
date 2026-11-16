"""
MediSync AI — Application Settings
Loads configuration from environment variables via Pydantic BaseSettings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "MediSync AI"
    APP_ENV: str = "development"

    # ── Auth ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://medisync_user:medisync_pass@localhost:5432/medisync_db"
    )

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://:medisync_redis_pass@localhost:6379/0"

    # ── MinIO / S3 ────────────────────────────────────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "medisync_minio"
    MINIO_SECRET_KEY: str = "medisync_minio_secret"
    MINIO_BUCKET_MEDICAL_IMAGES: str = "medical-images"
    MINIO_USE_SSL: bool = False

    # ── LLM ───────────────────────────────────────────────────────────────────
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_USE_LOCAL: bool = False


# Singleton instance used across the app
settings = Settings()
