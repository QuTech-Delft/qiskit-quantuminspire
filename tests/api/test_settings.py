from pathlib import Path
from typing import Any

import pytest

import qiskit_quantuminspire.api.settings as settings
from qiskit_quantuminspire.api.settings import ApiSettings, AuthSettings


@pytest.fixture
def clear_singleton() -> None:
    settings._settings = None
    settings.API_SETTINGS_FILE = Path.home() / ".quantuminspire" / "config.json"


def test_store_tokens(auth_settings: AuthSettings, tmpdir: str, clear_singleton: Any) -> None:
    # Arrange
    host = "https://host.com"
    api_settings = ApiSettings(auths={host: auth_settings}, default_host=host)
    stored_tokens_path = Path(tmpdir.join("tokens.json"))

    # Act
    assert auth_settings.tokens is not None
    api_settings.store_tokens(host=host, tokens=auth_settings.tokens, path=stored_tokens_path)

    # Assert
    assert api_settings == api_settings.model_validate_json(stored_tokens_path.read_text())


def test_api_settings_read_file(auth_settings: AuthSettings, tmpdir: str, clear_singleton: Any) -> None:
    # Arrange
    settings_file = Path(tmpdir.join("config.json"))
    host = "https://host.com"
    settings_stored = ApiSettings(auths={host: auth_settings}, default_host=host)
    settings_file.write_text(settings_stored.model_dump_json())

    # Act
    settings_read = ApiSettings.from_config_file(path=settings_file)

    # Assert
    assert settings_stored == settings_read


def test_api_settings_no_configuration_file(tmpdir: str, clear_singleton: Any) -> None:
    # Arrange
    settings_file = Path(tmpdir.join("non-existent.json"))

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        ApiSettings.from_config_file(path=settings_file)
