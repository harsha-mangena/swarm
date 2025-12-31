"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = "postgresql+asyncpg://swarmos:swarmos_dev@localhost:5432/swarmos"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # LLM Providers
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # Model preferences (user-configurable via settings)
    google_model: str = "gemini/gemini-1.5-flash"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4o"
    openrouter_model: str = "openrouter/anthropic/claude-3-sonnet"

    # Tools
    tavily_api_key: Optional[str] = None
    brave_api_key: Optional[str] = None

    # Application
    secret_key: str = "dev-secret-key-change-in-production"
    environment: str = "development"
    log_level: str = "INFO"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

