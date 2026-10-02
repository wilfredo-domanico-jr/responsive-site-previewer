from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    screenshot_dir: Path = Path("./screenshots")
    cors_origins: str = "http://localhost:3000"
    navigation_timeout_ms: int = 30_000
    network_idle_timeout_ms: int = 5_000
    settle_delay_ms: int = 500
    max_concurrent_jobs: int = 2
    max_full_page_height: int = 10_000
    blocked_hostnames: str = "metadata.google.internal"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def blocked_hostname_set(self) -> frozenset[str]:
        return frozenset(name.strip().lower() for name in self.blocked_hostnames.split(",") if name.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
