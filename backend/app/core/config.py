"""
Application configuration module using Pydantic settings.

This module defines a ``Settings`` class that reads configuration from
environment variables or default values. When running the application in
different environments (development, staging, production), you can set
environment variables or create a ``.env`` file to override these
defaults. The ``settings`` object is instantiated at import time and
can be imported throughout the application to access configuration
values.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration values for the ClubIQ Segreteria backend."""

    APP_NAME: str = "ClubIQ Segreteria"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # Database connection string. For SQLite, the path is relative to
    # the working directory. In production, replace with a PostgreSQL URL.
    DATABASE_URL: str = "sqlite:///./clubiq.db"

    # JWT settings
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # OpenAI API key placeholder (if needed for future AI features)
    OPENAI_API_KEY: str = ""

    # Comma-separated platform admin emails allowed to access /api/admin.
    PLATFORM_ADMIN_EMAILS: str = "admin4@test.it"

    class Config:
        env_file = ".env"


settings = Settings()


if (
    settings.ENVIRONMENT.lower() in {"production", "prod"}
    and settings.SECRET_KEY == "change-this-secret-key"
):
    raise RuntimeError("Configura SECRET_KEY in produzione prima di avviare ClubIQ.")
