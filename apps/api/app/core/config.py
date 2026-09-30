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

    # Encrypts `blog_platforms.password_encrypted` at rest (Sprint 5,
    # docs/DATABASE_SCHEMA.md: "باید با KMS/Fernet رمزنگاری شود"). Must be
    # a valid `Fernet.generate_key()` value — this default is fine for
    # local dev/tests only; override it in any real deployment, same as
    # SECRET_KEY, and never rotate it without re-encrypting existing rows.
    FERNET_KEY: str = "MlhMxGHc5GuV4bDHLt0yoTutV43PAUR8FDFKontORfc="

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
