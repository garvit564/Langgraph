from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration and environment variables."""
    app_name: str = "Agent Desk Backend"
    app_env: str = "development"

    # Ollama Local Configuration (Optional / Fallback)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "nemotron-3-nano:4b"
    ollama_temperature: float = 0.0

    # API Keys & Database Connections
    tavily_api_key: str
    weatherapi_api_key: str
    database_url: str
    google_api_key: str

    # JWT Authentication Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def get_settings() -> Settings:
    """Returns the application settings singleton."""
    return settings
