"""Flask application configuration classes."""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Diagnostic: Log API key suffix (safe)
import os
import logging
_key = os.environ.get("OPENAI_API_KEY", "")
if _key:
    logging.info("Config: OPENAI_API_KEY loaded, suffix: %s", _key[-5:])
else:
    logging.warning("Config: OPENAI_API_KEY NOT FOUND in environment")


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Database (Supabase PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    }

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    # LLM
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")

    # Security — Fernet key for encrypting tokens at rest
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")

    # Email / Brevo
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")

    # Google Calendar scopes
    GOOGLE_CALENDAR_SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]
    GOOGLE_CALENDAR_EXTRA_SCOPES = [
        "https://www.googleapis.com/auth/calendar",
    ]


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}  # SQLite doesn't support pool_size
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
