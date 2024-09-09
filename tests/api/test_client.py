from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from qiskit_quantuminspire.api.client import Configuration, config, connect
from qiskit_quantuminspire.api.settings import ApiSettings, AuthSettings, TokenInfo


@pytest.fixture
def api_settings_mock(auth_settings: AuthSettings, mocker: MockerFixture) -> MagicMock:
    api_settings = MagicMock(spec=ApiSettings)
    api_settings.default_host = "https://host.com"
    api_settings.auths = {api_settings.default_host: auth_settings}
    api_settings.from_config_file.return_value = api_settings

    mocker.patch("qiskit_quantuminspire.api.client.ApiSettings", return_value=api_settings)

    return api_settings


def test_connect_no_tokens(api_settings_mock: MagicMock) -> None:
    # Arrange
    api_settings_mock.auths[api_settings_mock.default_host].tokens = None

    # Act & Assert
    with pytest.raises(ValueError):
        connect()


def test_config(api_settings_mock: MagicMock, mocker: MockerFixture) -> None:
    # Arrange
    session = MagicMock()
    mocker.patch("qiskit_quantuminspire.api.client.OauthDeviceSession", return_value=session)
    mocker.patch("qiskit_quantuminspire.api.client.IdentityProvider")

    # Act
    conf = config()

    # Assert
    assert conf._oauth_session == session


def test_configuration_auth_settings(token_info: TokenInfo) -> None:
    # Arrange
    session = MagicMock()
    session.refresh.return_value = token_info
    config = Configuration(host="host", oauth_session=session)

    # Act
    config.auth_settings()

    # Assert
    assert config.access_token == token_info.access_token
