from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings using pydantic-settings."""

    APP_NAME: str = "AgentCart API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/agentcart"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173"]

    RAZORPAY_KEY_ID: Union[str, None] = None
    RAZORPAY_KEY_SECRET: Union[str, None] = None
    LLM_API_KEY: Union[str, None] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list of strings."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


settings = get_settings()
