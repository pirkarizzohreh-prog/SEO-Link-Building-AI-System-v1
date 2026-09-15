from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, read from environment variables / .env."""

    ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg2://seo:seo@localhost:5432/seo_link_building"
    SECRET_KEY: str = "change-me-in-prod"

    # Origin(s) the Next.js dashboard is served from, comma-separated
    # (e.g. "https://dashboard.example.com"). Ignored in development,
    # where all origins are allowed for convenience.
    FRONTEND_ORIGINS: str = ""

    # --- Auth (Sprint 2) ---
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Populated/used from Sprint 3 (AI Agents) onward.
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
