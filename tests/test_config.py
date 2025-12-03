"""Tests for configuration module."""

from pathlib import Path

from gmail_ai_unsub.config import Config


def test_config_loading(tmp_path: Path) -> None:
    """Test loading configuration from TOML file."""
    config_content = """
[gmail]
credentials_file = "credentials.json"
token_file = "token.json"

[llm]
provider = "google"
model = "gemini-3-pro-preview"
api_key_env = "GOOGLE_API_KEY"

[labels]
marketing = "Unsubscribe"
unsubscribed = "Unsubscribed"
failed = "Unsubscribe-Failed"
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    config = Config(str(config_file))

    assert config.llm_provider == "google"
    assert config.llm_model == "gemini-3-pro-preview"
    assert config.label_marketing == "Unsubscribe"


def test_config_defaults(tmp_path: Path) -> None:
    """Test configuration defaults."""
    config_content = """
[gmail]
credentials_file = "credentials.json"
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    config = Config(str(config_file))

    # Should use defaults for missing values
    assert config.llm_provider == "google"
    assert config.label_marketing == "Unsubscribe"  # Default action label
