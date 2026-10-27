from typing import Literal
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DEBUG: bool = True
    APP_SECRET_KEY: str = "change-this-in-production-to-at-least-32-random-bytes-min-len"

    # Database URLs (NR-2, TN-3)
    # Privileged role for migrations (creates tables & forced RLS policies)
    DB_MIGRATOR_URL: str = Field(
        default="postgresql+psycopg://campuscare_migrator:campuscare_migrator_pass@localhost:5433/campuscare",
        validation_alias=AliasChoices("DB_MIGRATOR_URL", "MIGRATION_DATABASE_URL"),
    )
    # Non-owner application runtime role (NOBYPASSRLS)
    DB_APP_URL: str = Field(
        default="postgresql+psycopg://campuscare_app:campuscare_app_pass@localhost:5433/campuscare",
        validation_alias=AliasChoices("DB_APP_URL", "DATABASE_URL"),
    )

    # Server Bindings
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Session Hardening (C5, ADR-003)
    SESSION_COOKIE_NAME: str = "campuscare_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    SESSION_LIFETIME_SECONDS: int = 86400  # 24 hours
    MFA_ISSUER: str = "CampusCareAI"

    # AI Gateway Config (NR-8: Must fallback safely if disabled)
    AI_ENABLED: bool = False
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str = "mock-key-not-for-production"
    AI_MODEL_NAME: str = "gemini-2.5-flash"

    # Storage Config
    STORAGE_DRIVER: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_PATH: str = "./uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
