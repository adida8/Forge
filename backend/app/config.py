from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from environment / .env."""

    anthropic_api_key: str = ""
    forge_model: str = "claude-haiku-4-5-20251001"
    readiness_threshold: int = 80
    database_url: str = "sqlite:///./forge.db"
    cors_origins: str = "http://localhost:5173"
    shared_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
