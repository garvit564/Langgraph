from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Configuration settings for the Worker Microservice."""
    app_name: str = "Agent Desk Worker Service"
    port: int = 8001
    redis_url: str = "redis://localhost:6379/0"

    # SMTP Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # Tavily Web Search API
    tavily_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = WorkerSettings()


def get_worker_settings() -> WorkerSettings:
    """Returns the singleton worker configuration."""
    return settings
