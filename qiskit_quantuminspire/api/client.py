from typing import Any, Optional

import compute_api_client

from qiskit_quantuminspire.api.authentication import IdentityProvider, OauthDeviceSession
from qiskit_quantuminspire.api.settings import ApiSettings


class Configuration(compute_api_client.Configuration):  # type: ignore[misc]
    """Original Configuration class in compute_api_client does not handle refreshing bearer tokens, so we need to add
    some functionality."""

    def __init__(self, host: str, oauth_session: OauthDeviceSession, **kwargs: Any):
        self._oauth_session = oauth_session
        super().__init__(host=host, **kwargs)

    def auth_settings(self) -> Any:
        token_info = self._oauth_session.refresh()
        self.access_token = token_info.access_token
        return super().auth_settings()


_config: Optional[Configuration] = None


def connect() -> None:
    """Set connection configuration for the Quantum Inspire API.

    Call after logging in with the CLI. Will remove old configuration.
    """
    global _config
    settings = ApiSettings.from_config_file()

    tokens = settings.auths[settings.default_host].tokens

    if tokens is None:
        raise ValueError("No access token found for the default host. Please connect to Quantum Inspire using the CLI.")

    host = settings.default_host
    _config = Configuration(
        host=host,
        oauth_session=OauthDeviceSession(host, settings, IdentityProvider(settings.auths[host].well_known_endpoint)),
    )


def config() -> Configuration:
    global _config
    if _config is None:
        connect()

    assert _config is not None
    return _config
