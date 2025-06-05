"""Application configuration loaded from environment variables."""

from pydantic import BaseSettings, validator
from typing import List


class Settings(BaseSettings):
    app_env: str = "local"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_review"
    redis_url: str = "redis://localhost:6379/0"
    mock_llm: bool = True
    allowed_origins: str = "http://localhost:5173"
    github_app_id: str | None = None
    github_app_private_key_base64: str | None = None
    github_webhook_secret: str | None = None
    otel_service_name: str = "ai-code-review-backend"
    otel_exporter_otlp_endpoint: str | None = None
    analytics_enabled: bool = True
    analytics_format: str = "PARQUET"  # or DELTA
    analytics_sink: str | None = None

    class Config:
        env_prefix = ""
        case_sensitive = False

    @validator("analytics_format")
    def validate_analytics_format(cls, v: str) -> str:
        if v not in {"PARQUET", "DELTA"}:
            raise ValueError("ANALYTICS_FORMAT must be PARQUET or DELTA")
        return v


settings = Settings()