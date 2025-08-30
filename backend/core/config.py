# File: backend/core/config.py
"""Application configuration using lightweight Pydantic-style settings."""

from pathlib import Path

from pydantic import BaseModel, BaseSettings, Field


class DatabaseSettings(BaseModel):
    """Database related configuration."""

    path: str = Field(
        str(Path(__file__).resolve().parents[1] / "rockmundo.db"),
        env="ROCKMUNDO_DB_PATH",
    )


class AuthSettings(BaseModel):
    """Authentication and security settings."""

    jwt_secret: str = Field("dev-change-me", env="ROCKMUNDO_JWT_SECRET")
    jwt_iss: str = Field("rockmundo", env="ROCKMUNDO_JWT_ISS")
    jwt_aud: str = Field("rockmundo-app", env="ROCKMUNDO_JWT_AUD")
    jwt_alg: str = Field("HS256", env="ROCKMUNDO_JWT_ALG")
    access_token_ttl_min: int = Field(30, env="ROCKMUNDO_ACCESS_TTL_MIN")
    refresh_token_ttl_days: int = Field(30, env="ROCKMUNDO_REFRESH_TTL_DAYS")
    discord_webhook_url: str = Field("", env="DISCORD_WEBHOOK_URL")


class RateLimitSettings(BaseModel):
    """Request rate limiting configuration."""

    requests_per_min: int = Field(60, env="ROCKMUNDO_RATE_LIMIT_REQUESTS_PER_MIN")
    storage: str = Field("memory", env="ROCKMUNDO_RATE_LIMIT_STORAGE")
    redis_url: str = Field(
        "redis://localhost:6379/0", env="ROCKMUNDO_RATE_LIMIT_REDIS_URL"
    )


class CORSSettings(BaseModel):
    """Cross-origin resource sharing settings."""

    allowed_origins: list[str] = Field(
        default_factory=lambda: ["*"], env="ROCKMUNDO_CORS_ALLOWED_ORIGINS"
    )


class RealtimeSettings(BaseModel):
    """Realtime hub configuration."""

    backend: str = Field("memory", env="ROCKMUNDO_REALTIME_BACKEND")
    redis_url: str = Field(
        "redis://localhost:6379/0", env="ROCKMUNDO_REALTIME_REDIS_URL"
    )


class Settings(BaseSettings):
    """Top level application settings."""

    env: str = Field("dev", env="ROCKMUNDO_ENV")
    log_level: str = Field("INFO", env="ROCKMUNDO_LOG_LEVEL")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    realtime: RealtimeSettings = Field(default_factory=RealtimeSettings)

    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"


settings = Settings()

