import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from qiskit_quantuminspire.api.authentication import AuthorisationError, IdentityProvider, OauthDeviceSession
from qiskit_quantuminspire.api.settings import ApiSettings, AuthSettings, TokenInfo


@pytest.fixture
def identity_provider_mock() -> MagicMock:
    return MagicMock(spec=IdentityProvider)


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings(
        client_id="client_id",
        code_challenge_method="code_challenge_method",
        code_verifyer_length=1,
        well_known_endpoint="https://host.com/well-known-endpoint",
        tokens=TokenInfo(
            access_token="access_token",
            expires_in=100,
            refresh_token="refresh_token",
            refresh_expires_in=1000,
            generated_at=1,
        ),
        team_member_id=1,
    )


@pytest.fixture
def api_settings(auth_settings: AuthSettings) -> ApiSettings:
    host = "https://host.com"
    return ApiSettings(default_host=host, auths={host: auth_settings})


@pytest.fixture
def api_settings_mock(auth_settings: AuthSettings) -> MagicMock:
    api_settings = MagicMock(spec=ApiSettings)
    api_settings.default_host = "https://host.com"
    api_settings.auths = {api_settings.default_host: auth_settings}
    return api_settings


def test_oauth_device_session_refresh_no_token(api_settings: ApiSettings, identity_provider_mock: MagicMock):
    api_settings.auths[api_settings.default_host].tokens = None
    session = OauthDeviceSession("https://host.com", api_settings, identity_provider_mock)

    with pytest.raises(AuthorisationError):
        session.refresh()


def test_oauth_device_session_refresh_token_not_expired(api_settings: ApiSettings, identity_provider_mock: MagicMock):
    auth_settings = api_settings.auths[api_settings.default_host]
    auth_settings.tokens.generated_at = time.time()
    session = OauthDeviceSession("https://host.com", api_settings, identity_provider_mock)

    token_info = session.refresh()
    assert token_info == auth_settings.tokens

    identity_provider_mock.get_refresh_token.assert_not_called()


@freeze_time("2021-01-01")
def test_oauth_device_session_refresh_token_expired(api_settings_mock: MagicMock, identity_provider_mock: MagicMock):
    session = OauthDeviceSession("https://host.com", api_settings_mock, identity_provider_mock)
    new_token_info: dict[str, Any] = {
        "access_token": "new_access_token",
        "expires_in": 100,
        "refresh_token": "new_refresh_token",
        "refresh_expires_in": 1000,
        "generated_at": time.time(),
    }

    identity_provider_mock.get_refresh_token.return_value = new_token_info

    token_info = session.refresh()
    assert token_info == TokenInfo(**new_token_info)

    identity_provider_mock.get_refresh_token.assert_called_once_with("client_id", "refresh_token")
    api_settings_mock.store_tokens.assert_called_once_with("https://host.com", token_info)
