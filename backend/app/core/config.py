"""
Application configuration.

Settings are loaded from environment variables (or a .env file in local dev).
Using pydantic-settings means every value here is type-validated at startup —
if DATABASE_URL is missing or ACCESS_TOKEN_EXPIRE_MINUTES isn't a number,
the app fails fast at boot instead of failing mysteriously later.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    APP_NAME: str = "AI Career Intelligence Platform"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Database ---
    # Defaults to a local SQLite file so the project runs with zero setup.
    # In production (Render/Docker) this is overridden via env var to a
    # postgresql+psycopg2://... URL — no code changes needed, same ORM code
    # works against both because SQLAlchemy abstracts the SQL dialect.
    DATABASE_URL: str = "sqlite:///./career_platform.db"

    # --- Auth / JWT ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_this_is_only_for_local_dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- File uploads ---
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_RESUME_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt"}

    # --- LLM-assisted resume recovery (optional — see llm_resume_engine.py) ---
    # Left unset by default: the app must work with pure rule-based parsing
    # and no external API dependency when this isn't configured. LLM
    # features (messy-resume recovery, suggestions, rebuilding) only
    # activate when a real key is provided.
    ANTHROPIC_API_KEY: str | None = None
    LLM_MODEL: str = "claude-sonnet-4-5"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Cached so Settings() is only constructed once per process, not re-parsed
    from the environment on every request that depends on it.
    """
    return Settings()
