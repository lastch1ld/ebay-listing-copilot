import pytest

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
def fake_keyring() -> FakeKeyring:
    return FakeKeyring()


def test_secret_store_uses_named_keyring(fake_keyring: FakeKeyring) -> None:
    store = SecretStore(service="ebay-listing-copilot-test", backend=fake_keyring)
    store.set("ebay.refresh_token", "secret")
    assert store.get("ebay.refresh_token") == "secret"


def test_secret_store_returns_none_for_missing_secret(fake_keyring: FakeKeyring) -> None:
    store = SecretStore(service="ebay-listing-copilot-test", backend=fake_keyring)
    assert store.get("ebay.refresh_token") is None


def test_secret_store_delete_removes_value(fake_keyring: FakeKeyring) -> None:
    store = SecretStore(service="ebay-listing-copilot-test", backend=fake_keyring)
    store.set("ebay.refresh_token", "secret")
    store.delete("ebay.refresh_token")
    assert store.get("ebay.refresh_token") is None
