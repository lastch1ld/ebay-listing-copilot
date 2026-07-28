from typing import Any

_SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "token",
    "refresh_token",
    "access_token",
    "client_secret",
    "password",
    "email",
    "address",
    "phone",
    "tax_id",
}

REDACTED = "[REDACTED]"


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return normalized in _SENSITIVE_KEYS or any(
        sensitive in normalized for sensitive in _SENSITIVE_KEYS
    )


def redact_mapping(value: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if _is_sensitive_key(key):
            result[key] = REDACTED
        elif isinstance(item, dict):
            result[key] = redact_mapping(item)
        elif isinstance(item, list):
            result[key] = [
                redact_mapping(entry) if isinstance(entry, dict) else entry for entry in item
            ]
        else:
            result[key] = item
    return result
