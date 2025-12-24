"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://quantshift_bot:Cloudy_92!@10.92.3.21:5432/quantshift",
        description="PostgreSQL connection string",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string",
    )

    # Monitoring
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Trading
    max_position_size: float = 10000.0
    max_positions: int = 10
    risk_per_trade: float = 0.02  # 2% risk per trade


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
