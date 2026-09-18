import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "homebrain-default-secret-key"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 365

    DEFAULT_ADMIN_USERNAME: str = "radek"
    DEFAULT_ADMIN_PASSWORD: str = "admin"
    DEFAULT_ADMIN_NAME: str = "Radek"

    DEFAULT_WIFE_USERNAME: str = "monika"
    DEFAULT_WIFE_PASSWORD: str = "monika"
    DEFAULT_WIFE_NAME: str = "Monika"

    SMTP_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "homebrain@rodina.local"
    SMTP_USE_TLS: bool = True

    STORAGE_DIR: str = "storage"
    DATABASE_URL: str = "sqlite:///./storage/homebrain.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

# Ensure storage directory exists
storage_path = BASE_DIR / settings.STORAGE_DIR
storage_path.mkdir(parents=True, exist_ok=True)
(storage_path / "uploads").mkdir(parents=True, exist_ok=True)
(storage_path / "mail_previews").mkdir(parents=True, exist_ok=True)
