"""Module containing the handler for the Quantum Inspire persistent configuration."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, BeforeValidator, Field, HttpUrl
from typing_extensions import Annotated

Url = Annotated[str, BeforeValidator(lambda value: str(HttpUrl(value)).rstrip("/"))]
API_SETTINGS_FILE = Path.joinpath(Path.home(), ".quantuminspire", "config.json")


class TokenInfo(BaseModel):
    """A pydantic model for storing all information regarding oauth access and refresh tokens."""

    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: Optional[int] = None
    generated_at: float = Field(default_factory=time.time)

    @property
    def access_expires_at(self) -> float:
        """Timestamp containing the time when the access token will expire."""
        return self.generated_at + self.expires_in


class AuthSettings(BaseModel):
    """Pydantic model for storing all auth related settings for a given host."""

    client_id: str
    code_challenge_method: str
    code_verifyer_length: int
    well_known_endpoint: Url
    tokens: Optional[TokenInfo]
    team_member_id: Optional[int]


class ApiSettings(BaseModel):
    """The settings class for the Quantum Inspire persistent configuration."""

    auths: Dict[Url, AuthSettings]
    default_host: Url

    def store_tokens(self, host: Url, tokens: TokenInfo, path: Path = API_SETTINGS_FILE) -> None:
        """

        :param host: the hostname of the api for which the tokens are intended
        :param tokens: OAuth access and refresh tokens
        :return: None

        This functions stores the team_member_id, access and refresh tokens in the config.json file.
        """
        self.auths[host].tokens = tokens
        path.write_text(self.model_dump_json(indent=2))


_settings: Optional[ApiSettings] = None


def api_settings(clear: bool = False) -> ApiSettings:
    """Return the current settings for the Quantum Inspire persistent configuration."""
    global _settings

    if clear:
        _settings = None

    if _settings is None:
        if not API_SETTINGS_FILE.is_file():
            raise FileNotFoundError("No configuration file found. Please connect to Quantum Inspire using the CLI.")

        api_settings = API_SETTINGS_FILE.read_text()
        _settings = ApiSettings.model_validate_json(api_settings)
    return _settings
