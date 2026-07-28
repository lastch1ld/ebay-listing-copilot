from collections.abc import Callable

import httpx

from app.config import Environment

_API_BASE_URLS = {
    Environment.SANDBOX: "https://api.sandbox.ebay.com",
    Environment.PRODUCTION: "https://api.ebay.com",
}

AccessTokenProvider = Callable[[], str]


class EbayRestClient:
    """Thin authenticated REST client shared by the eBay integration adapters."""

    def __init__(
        self,
        environment: Environment,
        access_token_provider: AccessTokenProvider,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = _API_BASE_URLS[environment]
        self._access_token_provider = access_token_provider
        self._http_client = http_client or httpx.Client(timeout=30.0)

    def get(self, path: str, params: dict[str, str] | None = None) -> dict[str, object]:
        response = self._http_client.get(
            f"{self._base_url}{path}",
            params=params,
            headers=self._headers(),
        )
        response.raise_for_status()
        result: dict[str, object] = response.json()
        return result

    def post(self, path: str, json_body: dict[str, object]) -> dict[str, object]:
        response = self._http_client.post(
            f"{self._base_url}{path}",
            json=json_body,
            headers=self._headers(),
        )
        response.raise_for_status()
        result: dict[str, object] = response.json()
        return result

    def put(self, path: str, json_body: dict[str, object]) -> dict[str, object]:
        response = self._http_client.put(
            f"{self._base_url}{path}",
            json=json_body,
            headers=self._headers(),
        )
        response.raise_for_status()
        if not response.content:
            return {}
        result: dict[str, object] = response.json()
        return result

    def upload_binary(
        self, path: str, filename: str, content_type: str, content: bytes
    ) -> dict[str, object]:
        response = self._http_client.post(
            f"{self._base_url}{path}",
            files={"file": (filename, content, content_type)},
            headers={"Authorization": f"Bearer {self._access_token_provider()}"},
        )
        response.raise_for_status()
        result: dict[str, object] = response.json()
        return result

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token_provider()}",
            "Content-Type": "application/json",
        }
