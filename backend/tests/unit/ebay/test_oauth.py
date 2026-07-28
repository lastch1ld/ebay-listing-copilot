from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from app.config import Environment
from app.integrations.ebay.oauth import EbayOAuth, EbayTokenStore, OAuthStateError
from app.security.secrets import SecretStore


class FakeKeyring:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, name: str) -> str | None:
        return self._values.get((service, name))

    def set_password(self, service: str, name: str, value: str) -> None:
        self._values[(service, name)] = value

    def delete_password(self, service: str, name: str) -> None:
        del self._values[(service, name)]


@pytest.fixture
def token_store() -> EbayTokenStore:
    secret_store = SecretStore(service="ebay-listing-copilot-test", backend=FakeKeyring())
    return EbayTokenStore(secret_store)


@pytest.fixture
def oauth(token_store: EbayTokenStore) -> EbayOAuth:
    return EbayOAuth(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://127.0.0.1:8000/api/auth/ebay/callback",
        environment=Environment.SANDBOX,
        scopes=("https://api.ebay.com/oauth/api_scope/sell.inventory",),
        token_store=token_store,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_production_token_is_never_used_for_sandbox(token_store: EbayTokenStore) -> None:
    token_store.set("production", "prod-token")
    assert token_store.get("sandbox") is None


def test_begin_returns_state_and_pkce_challenge(oauth: EbayOAuth) -> None:
    request = oauth.begin()
    assert request.state
    assert "code_challenge=" in request.authorization_url
    assert f"state={request.state}" in request.authorization_url
    assert request.authorization_url.startswith("https://auth.sandbox.ebay.com/")


def test_callback_rejects_wrong_state(oauth: EbayOAuth) -> None:
    request = oauth.begin()
    with pytest.raises(OAuthStateError):
        oauth.complete(code="auth-code", state=request.state + "changed")


def test_expired_state_is_rejected(oauth: EbayOAuth) -> None:
    request = oauth.begin()
    oauth._clock = lambda: datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=11)
    with pytest.raises(OAuthStateError):
        oauth.complete(code="auth-code", state=request.state)


def test_complete_exchanges_code_and_stores_refresh_token(
    oauth: EbayOAuth, token_store: EbayTokenStore
) -> None:
    request = oauth.begin()
    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "access-1",
                    "refresh_token": "refresh-1",
                    "expires_in": 7200,
                },
            )
        )
        tokens = oauth.complete(code="auth-code", state=request.state)

    assert tokens.access_token == "access-1"
    assert tokens.refresh_token == "refresh-1"
    assert token_store.get("sandbox") == "refresh-1"


def test_refresh_rotates_token_atomically(oauth: EbayOAuth, token_store: EbayTokenStore) -> None:
    token_store.set("sandbox", "old-refresh-token")

    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "access-2",
                    "refresh_token": "new-refresh-token",
                    "expires_in": 7200,
                },
            )
        )
        tokens = oauth.refresh()

    assert tokens.access_token == "access-2"
    assert token_store.get("sandbox") == "new-refresh-token"


def test_refresh_failure_leaves_old_token_in_place(
    oauth: EbayOAuth, token_store: EbayTokenStore
) -> None:
    token_store.set("sandbox", "old-refresh-token")

    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(
            return_value=httpx.Response(400, json={"error": "invalid_grant"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            oauth.refresh()

    assert token_store.get("sandbox") == "old-refresh-token"
