import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


def default_database_url() -> str:
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return f"sqlite:///{data_home / 'studyhub' / 'studyhub.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STUDYHUB_", extra="ignore")

    database_url: str = default_database_url()
    environment: Literal["development", "test", "production"] = "development"

    def ensure_database_directory(self) -> None:
        url = make_url(self.database_url)
        if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
            return
        Path(url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
