from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, read from environment variables / .env.

    Auth-related settings (SECRET_KEY, token TTLs) are declared now so the
    schema is stable, but they are not exercised until Sprint 2 (Auth).
    """

    ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg2://seo:seo@localhost:5432/seo_link_building"
    SECRET_KEY: str = "change-me-in-prod"

    # Populated/used from Sprint 3 (AI Agents) onward.
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
