from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="HOMEFIN_",
        extra="ignore",
    )

    api_title: str = "HomeFin Agent"
    database_url: str = "sqlite+pysqlite:///./homefin.db"
    auth_secret_key: str = "dev-only-change-me"
    auth_token_ttl_minutes: int = 60
    import_storage_dir: str = "./data/imports"
    worker_poll_interval_seconds: int = 5
    openclaw_cli_command: str = "openclaw"
    openclaw_default_channel: str | None = None
    openclaw_default_target: str | None = None
    allowed_write_roles: list[str] = Field(default_factory=lambda: ["owner"])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
