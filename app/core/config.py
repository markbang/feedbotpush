# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///app_database.db"
    AI_API_KEY: str = "your_ai_api_key_please_set_in_env"
    WEBHOOK_URL: str = "https://example.com/webhook"
    OPENAI_MODEL_NAME: str = "X.grok-3-mini-fast-beta"
    OPENAI_API_BASE_URL: str = "https://ai.bangwu.top/api/"
    SUMMARY_SCHEDULE_HOURS: str = "17"  # Default to run daily at midnight UTC, comma-separated for multiple hours e.g., "0,6,12,18"
    SUMMARY_INTERVAL_HOURS: int = (
        0  # Alternative: run every X hours, 0 to disable interval-based scheduling
    )
    RUN_SUMMARY_ON_STARTUP: bool = True  # Added for debugging startup task

    class Config:
        env_file = ".env"  # Load variables from .env file in the project root
        env_file_encoding = "utf-8"


settings = Settings()
