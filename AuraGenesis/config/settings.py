"""Centralized, validated configuration for AuraGenesis.

Uses Pydantic v2 Settings for type safety, environment variable loading,
and secure defaults. This is the single source of truth for all secrets and limits.
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import Literal


class AuraSettings(BaseSettings):
    """AuraGenesis configuration with strict validation."""

    # === LLM ===
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL (or OpenAI-compatible endpoint)"
    )
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key (optional, for fallback)"
    )

    # === Personalization ===
    owner_name: str = Field(default="Owner", min_length=1, max_length=50)

    # === Hardware ===
    sense_interval: int = Field(default=8, ge=1, le=300)
    enable_camera: bool = True
    enable_microphone: bool = True
    enable_temperature_sensor: bool = False
    enable_bluetooth: bool = True

    # === Security Hardening ===
    max_input_length: int = Field(default=2000, ge=100, le=10000)
    rate_limit_per_minute: int = Field(default=30, ge=5, le=120)

    # === Advanced Features ===
    enable_self_modification: bool = True
    debug_mode: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    @field_validator("ollama_url")
    @classmethod
    def validate_ollama_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("OLLAMA_URL must start with http:// or https://")
        return v.rstrip("/")

    @field_validator("owner_name")
    @classmethod
    def validate_owner_name(cls, v: str) -> str:
        if any(char in v for char in ["<", ">", "&", "'", '"", ";", "`"]):
            raise ValueError("Owner name contains invalid characters")
        return v.strip()


# Singleton instance (lazy loaded)
_settings: AuraSettings | None = None


def get_settings() -> AuraSettings:
    """Get the validated settings singleton."""
    global _settings
    if _settings is None:
        _settings = AuraSettings()
    return _settings


def reload_settings() -> AuraSettings:
    """Force reload settings (useful after .env change)."""
    global _settings
    _settings = None
    return get_settings()
