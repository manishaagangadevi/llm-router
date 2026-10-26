from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Provider keys (all optional -- a provider without a key runs in demo mode)
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Which model serves each routing tier. Model names change often, so
    # they live in .env instead of code. Defaults use free-tier providers.
    fast_model: str = "openai/gpt-oss-20b"       # Groq
    balanced_model: str = "gemini-2.5-flash"       # Gemini
    premium_model: str = "openai/gpt-oss-120b"  # Groq

    database_url: str = "sqlite+aiosqlite:///./router.db"
    cors_origins: str = "http://localhost:3000"


settings = Settings()
