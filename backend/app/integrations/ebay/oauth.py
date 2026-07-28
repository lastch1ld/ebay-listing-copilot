import base64
import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.config import Environment
from app.security.secrets import SecretStore

_AUTH_BASE_URLS = {
    Environment.SANDBOX: "https://auth.sandbox.ebay.com/oauth2/authorize",
    Environment.PRODUCTION: "https://auth.ebay.com/oauth2/authorize",
}
_TOKEN_URLS = {
    Environment.SANDBOX: "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
    Environment.PRODUCTION: "https://api.ebay.com/identity/v1/oauth2/token",
}

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(UTC)


class OAuthStateError(ValueError):
    pass


class EbayTokenStore:
    """Keeps eBay refresh tokens under environment-scoped keychain entries."""

    def __init__(self, secret_store: SecretStore) -> None:
        self._secret_store = secret_store

    def set(self, environment: str, refresh_token: str) -> None:
        self._secret_store.set(f"ebay.{environment}.refresh_token", refresh_token)

    def get(self, environment: str) -> str | None:
        return self._secret_store.get(f"ebay.{environment}.refresh_token")


@dataclass(frozen=True)
class AuthorizationRequest:
    authorization_url: str
    state: str


@dataclass(frozen=True)
class TokenSet:
    access_token: str
    refresh_token: str
    expires_at: datetime


@dataclass
class _PendingAuthorization:
    code_verifier: str
    expires_at: datetime


def _generate_pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode("ascii")
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    return verifier, challenge


class EbayOAuth:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        environment: Environment,
        scopes: tuple[str, ...],
        token_store: EbayTokenStore,
        clock: Clock = utcnow,
        state_ttl: timedelta = timedelta(minutes=10),
        http_client: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._environment = environment
        self._scopes = scopes
        self._token_store = token_store
        self._clock = clock
        self._state_ttl = state_ttl
        self._http_client = http_client or httpx.Client(timeout=30.0)
        self._pending: dict[str, _PendingAuthorization] = {}

    def begin(self) -> AuthorizationRequest:
        state = secrets.token_urlsafe(32)
        code_verifier, code_challenge = _generate_pkce_pair()
        self._pending[state] = _PendingAuthorization(
            code_verifier=code_verifier,
            expires_at=self._clock() + self._state_ttl,
        )
        query = urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "response_type": "code",
                "scope": " ".join(self._scopes),
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
        authorization_url = f"{_AUTH_BASE_URLS[self._environment]}?{query}"
        return AuthorizationRequest(authorization_url=authorization_url, state=state)

    def complete(self, code: str, state: str) -> TokenSet:
        pending = self._pending.pop(state, None)
        if pending is None:
            raise OAuthStateError("unknown or already-consumed authorization state")
        if pending.expires_at <= self._clock():
            raise OAuthStateError("authorization state has expired")

        response = self._http_client.post(
            _TOKEN_URLS[self._environment],
            auth=(self._client_id, self._client_secret),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._redirect_uri,
                "code_verifier": pending.code_verifier,
            },
        )
        response.raise_for_status()
        tokens = self._parse_tokens(response.json())
        self._token_store.set(self._environment.value, tokens.refresh_token)
        return tokens

    def refresh(self) -> TokenSet:
        current_refresh_token = self._token_store.get(self._environment.value)
        if current_refresh_token is None:
            raise OAuthStateError(f"no stored refresh token for {self._environment.value}")

        response = self._http_client.post(
            _TOKEN_URLS[self._environment],
            auth=(self._client_id, self._client_secret),
            data={
                "grant_type": "refresh_token",
                "refresh_token": current_refresh_token,
                "scope": " ".join(self._scopes),
            },
        )
        response.raise_for_status()
        tokens = self._parse_tokens(response.json(), fallback_refresh_token=current_refresh_token)
        self._token_store.set(self._environment.value, tokens.refresh_token)
        return tokens

    def _parse_tokens(
        self, payload: dict[str, object], fallback_refresh_token: str | None = None
    ) -> TokenSet:
        refresh_token = payload.get("refresh_token")
        if refresh_token is None:
            refresh_token = fallback_refresh_token
        if not isinstance(refresh_token, str):
            raise OAuthStateError("token response did not include a refresh token")
        expires_in_raw = payload.get("expires_in", 0)
        expires_in = int(expires_in_raw) if isinstance(expires_in_raw, int | str) else 0
        return TokenSet(
            access_token=str(payload["access_token"]),
            refresh_token=refresh_token,
            expires_at=self._clock() + timedelta(seconds=expires_in),
        )
