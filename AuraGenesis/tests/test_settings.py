"""Tests for AuraSettings (Phase 4)."""
import pytest
from AuraGenesis.config.settings import AuraSettings, get_settings, reload_settings


def test_settings_defaults():
    """Test that default values are correct and validated."""
    settings = AuraSettings()
    assert settings.ollama_url == "http://localhost:11434"
    assert settings.owner_name == "Owner"
    assert settings.max_input_length == 2000
    assert settings.enable_self_modification is True


def test_settings_validation():
    """Test URL and owner name validation."""
    with pytest.raises(ValueError):
        AuraSettings(ollama_url="invalid-url")

    with pytest.raises(ValueError):
        AuraSettings(owner_name="<script>alert(1)</script>")


def test_settings_singleton():
    """Test singleton behavior."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2

    # After reload
    s3 = reload_settings()
    assert s3 is not s1


def test_settings_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("OWNER_NAME", "TestOwner")
    monkeypatch.setenv("MAX_INPUT_LENGTH", "1500")
    settings = reload_settings()
    assert settings.owner_name == "TestOwner"
    assert settings.max_input_length == 1500
