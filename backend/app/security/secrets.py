import contextlib
from typing import Protocol


class KeyringBackend(Protocol):
    def get_password(self, service: str, name: str) -> str | None: ...

    def set_password(self, service: str, name: str, value: str) -> None: ...

    def delete_password(self, service: str, name: str) -> None: ...


def _default_backend() -> KeyringBackend:
    import keyring

    return keyring


class SecretStore:
    def __init__(self, service: str, backend: KeyringBackend | None = None) -> None:
        self._service = service
        self._backend = backend if backend is not None else _default_backend()

    def get(self, name: str) -> str | None:
        return self._backend.get_password(self._service, name)

    def set(self, name: str, value: str) -> None:
        self._backend.set_password(self._service, name, value)

    def delete(self, name: str) -> None:
        import keyring.errors

        with contextlib.suppress(LookupError, keyring.errors.PasswordDeleteError):
            self._backend.delete_password(self._service, name)

    def __repr__(self) -> str:
        return f"SecretStore(service={self._service!r})"
