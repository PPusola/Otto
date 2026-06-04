from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="JARVIS_", extra="ignore")

    app_name: str = "JARVIS"
    host: str = "127.0.0.1"
    port: int = 8787
    auth_token: str = "change-me-generate-a-long-random-token"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:8787", "http://localhost:8787"])

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "mistral:7b"

    data_dir: Path = Path(".jarvis-data")
    memory_password: str = "change-me-memory-password"

    whisper_cpp_binary: Optional[str] = None
    whisper_cpp_model: Optional[str] = None

    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    spotify_redirect_uri: str = "http://127.0.0.1:8787/api/spotify/callback"
    spotify_default_device_id: Optional[str] = None

    allow_spotify_autorun: bool = True
    allow_wiz_autorun: bool = True
    wiz_lights: dict[str, str] = Field(default_factory=dict)
    wiz_broadcast: str = "192.168.1.255"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("wiz_lights", mode="before")
    @classmethod
    def parse_wiz_lights(cls, value: str | dict[str, str]) -> dict[str, str]:
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        pairs = [part.strip() for part in value.split(",") if part.strip()]
        mapping: dict[str, str] = {}
        for pair in pairs:
            name, ip = pair.split("=", 1)
            mapping[name.strip()] = ip.strip()
        return mapping


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
