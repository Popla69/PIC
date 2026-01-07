"""Configuration management for Popla Comet backend."""

import os
from typing import Optional, Union
from pydantic import model_validator
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
    allowed_image_types: Union[str, list[str]] = "image/jpeg,image/png,image/webp"

    cors_origins: Union[str, list[str]] = "*"
    cors_credentials: bool = True
    cors_methods: Union[str, list[str]] = "*"
    cors_headers: Union[str, list[str]] = "*"

    log_level: str = "INFO"
    
    @model_validator(mode='after')
    def parse_list_fields(self):
        """Parse comma-separated strings into lists for list fields."""
        if isinstance(self.allowed_image_types, str):
            self.allowed_image_types = [item.strip() for item in self.allowed_image_types.split(',')]
        
        if isinstance(self.cors_origins, str):
            self.cors_origins = [item.strip() for item in self.cors_origins.split(',')]
        
        if isinstance(self.cors_methods, str):
            self.cors_methods = [item.strip() for item in self.cors_methods.split(',')]
        
        if isinstance(self.cors_headers, str):
            self.cors_headers = [item.strip() for item in self.cors_headers.split(',')]
        
        return self


settings = Settings()
