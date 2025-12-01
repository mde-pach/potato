"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Database
    database_url: str = "sqlite:///./example_blog.db"
    
    # Application
    app_name: str = "Potato Example - Blog Management System"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # API
    api_prefix: str = "/api/v1"


# Global settings instance
settings = Settings()
