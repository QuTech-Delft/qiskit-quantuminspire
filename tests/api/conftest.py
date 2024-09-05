import pytest

from qiskit_quantuminspire.api.settings import AuthSettings, TokenInfo


@pytest.fixture
def token_info() -> TokenInfo:
    return TokenInfo(
        access_token="access_token",
        expires_in=100,
        refresh_token="refresh_token",
        refresh_expires_in=1000,
        generated_at=1,
    )


@pytest.fixture
def auth_settings(token_info: TokenInfo) -> AuthSettings:
    return AuthSettings(
        client_id="client_id",
        code_challenge_method="code_challenge_method",
        code_verifyer_length=1,
        well_known_endpoint="https://host.com/well-known-endpoint",
        tokens=token_info,
        team_member_id=1,
    )
