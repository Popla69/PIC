"""Configuration management for Popla Comet backend."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    app_name: str = "Popla Comet API"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-vision-preview"
    openai_max_tokens: int = 4096

    max_upload_size: int = 10 * 1024 * 1024
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]

    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    log_level: str = "INFO"


settings = Settings()
