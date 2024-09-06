import time
from typing import Any, Tuple, cast

import requests

from qiskit_quantuminspire.api.settings import ApiSettings, TokenInfo, Url


class AuthorisationError(Exception):
    """Indicates that the authorisation permanently went wrong."""

    pass


class IdentityProvider:
    """Class for interfacing with the IdentityProvider."""

    def __init__(self, well_known_endpoint: str):
        self._well_known_endpoint = well_known_endpoint
        self._token_endpoint, self._device_endpoint = self._get_endpoints()
        self._headers = {"Content-Type": "application/x-www-form-urlencoded"}

    def _get_endpoints(self) -> Tuple[str, str]:
        response = requests.get(self._well_known_endpoint)
        response.raise_for_status()
        config = response.json()
        return config["token_endpoint"], config["device_authorization_endpoint"]

    def refresh_access_token(self, client_id: str, refresh_token: str) -> dict[str, Any]:
        data = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        }
        response = requests.post(self._token_endpoint, headers=self._headers, data=data)
        response.raise_for_status()
        return cast(dict[str, Any], response.json())


class OauthDeviceSession:
    """Class for storing OAuth session information and refreshing tokens when needed."""

    def __init__(self, host: Url, settings: ApiSettings, identity_provider: IdentityProvider):
        self._api_settings = settings
        _auth_settings = settings.auths[host]
        self._host = host
        self._client_id = _auth_settings.client_id
        self._token_info = _auth_settings.tokens
        self._refresh_time_reduction = 5  # the number of seconds to refresh the expiration time
        self._identity_provider = identity_provider

    def refresh(self) -> TokenInfo:
        if self._token_info is None:
            raise AuthorisationError("You should authenticate first before you can refresh")

        if self._token_info.access_expires_at > time.time() + self._refresh_time_reduction:
            return self._token_info

        try:
            self._token_info = TokenInfo(
                **self._identity_provider.refresh_access_token(self._client_id, self._token_info.refresh_token)
            )
            self._api_settings.store_tokens(self._host, self._token_info)
            return self._token_info
        except requests.HTTPError as e:
            raise AuthorisationError(f"An error occurred during token refresh: {e}")
