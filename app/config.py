from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./scanner.db"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    scan_interval_minutes: int = 60
    event_webhook_url: str = ""


settings = Settings()

# Regulator RSS feeds scanned by default. Each is a live, verified feed as of 2026-08.
SOURCES = [
    {"name": "FCA News", "url": "https://www.fca.org.uk/news/rss.xml"},
    {
        "name": "PRA Publications",
        "url": "https://www.bankofengland.co.uk/rss/prudential-regulation-publications",
    },
    {"name": "Bank of England News", "url": "https://www.bankofengland.co.uk/rss/news"},
]
