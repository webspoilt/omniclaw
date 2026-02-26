import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openrouter/anthropic/claude-3.5-sonnet"  # default model
    database_url: str = "sqlite:///./agents.db"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
