from typing import Any

import compute_api_client

from qiskit_quantuminspire.api.authentication import IdentityProvider, OauthDeviceSession
from qiskit_quantuminspire.api.settings import api_settings


class Configuration(compute_api_client.Configuration):  # type: ignore[misc]
    def __init__(self, host: str, oauth_session: OauthDeviceSession, **kwargs: Any):
        self._oauth_session = oauth_session
        super().__init__(host=host, **kwargs)

    def auth_settings(self) -> Any:
        token_info = self._oauth_session.refresh()
        self.access_token = token_info.access_token
        return super().auth_settings()


_config: Configuration | None = None


def connect() -> None:
    """Set connection configuration for the Quantum Inspire API."""
    global _config
    settings = api_settings()

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
