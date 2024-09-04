import time
from typing import Tuple

import requests

from qiskit_quantuminspire.api.settings import AuthSettings, TokenInfo, Url, store_tokens


class AuthorisationError(Exception):
    """Indicates that the authorisation permanently went wrong."""

    pass


class OauthDeviceSession:
    def __init__(self, host: Url, settings: AuthSettings):
        self._settings = settings
        self._host = host
        self._client_id = settings.client_id
        self._token_info = settings.tokens
        self._token_endpoint, self._device_endpoint = self._get_endpoints()
        self._headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self._refresh_time_reduction = 5  # the number of seconds to refresh the expiration time

    def _get_endpoints(self) -> Tuple[str, str]:
        response = requests.get(self._settings.well_known_endpoint)
        response.raise_for_status()
        config = response.json()
        return config["token_endpoint"], config["device_authorization_endpoint"]

    def refresh(self) -> TokenInfo:
        if self._token_info is None:
            raise AuthorisationError("You should authenticate first before you can refresh")

        if self._token_info.access_expires_at > time.time() + self._refresh_time_reduction:
            return self._token_info

        data = {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "refresh_token": self._token_info.refresh_token,
        }

        response = requests.post(self._token_endpoint, data=data, headers=self._headers)

        if response.status_code == 200:
            self._token_info = TokenInfo(**response.json())
            store_tokens(self._host, self._token_info)
            return self._token_info

        raise AuthorisationError(f"Received status code: {response.status_code}\n {response.text}")
