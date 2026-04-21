# src/config/config.py
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings loaded from .env file."""

    # Django Core
    SECRET_KEY: str = "django-insecure-default-key-change-me"
    DEBUG: bool = True
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"  # Простая строка

    # Database
    USE_POSTGRES: bool = False
    DB_NAME: str = "delivery_service_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # Application specific
    APP_NAME: str = "Delivery Service"
    API_VERSION: str = "v1"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"

    # Security
    SESSION_COOKIE_SECURE: bool = False
    CSRF_COOKIE_SECURE: bool = False
    SECURE_SSL_REDIRECT: bool = False

    # CORS - простая строка
    CORS_ALLOWED_ORIGINS: str = ""

    # File Upload - простая строка
    MAX_UPLOAD_SIZE: int = 10
    ALLOWED_EXTENSIONS: str = ".jpg,.jpeg,.png,.pdf"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Create global settings object
settings = AppSettings()


# Helper functions
def get_db_config() -> dict:
    """Get database configuration."""
    if settings.USE_POSTGRES:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": settings.DB_NAME,
            "USER": settings.DB_USER,
            "PASSWORD": settings.DB_PASSWORD,
            "HOST": settings.DB_HOST,
            "PORT": settings.DB_PORT,
        }
    else:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(__file__).resolve().parent.parent / "db.sqlite3",
        }


def get_allowed_hosts_list() -> list:
    """Get allowed hosts as list."""
    return [host.strip() for host in settings.ALLOWED_HOSTS.split(",")]


def get_cors_origins_list() -> list:
    """Get CORS origins as list."""
    if settings.CORS_ALLOWED_ORIGINS:
        return [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",")]
    return []


def get_allowed_extensions_list() -> list:
    """Get allowed extensions as list."""
    return [ext.strip() for ext in settings.ALLOWED_EXTENSIONS.split(",")]


def is_development() -> bool:
    """Check if running in development mode."""
    return settings.DEBUG


def is_production() -> bool:
    """Check if running in production mode."""
    return not settings.DEBUG
