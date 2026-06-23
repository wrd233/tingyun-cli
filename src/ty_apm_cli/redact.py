from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SECRET_KEYS = {
    "api_key",
    "apikey",
    "secret_key",
    "secretkey",
    "access_token",
    "token",
    "authorization",
    "auth",
    "password",
    "credential",
}

BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)


def _sensitive_key(key: str) -> bool:
    lower = key.lower().replace("-", "_")
    return lower in SECRET_KEYS or "secret" in lower or "token" in lower or lower == "auth"


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_item(str(key), item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, str):
        return BEARER_RE.sub("Bearer ***REDACTED***", value)
    return value


def _redact_item(key: str, value: Any) -> Any:
    if not _sensitive_key(key):
        return redact(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return "***REDACTED***"


def redact_url(url: str) -> str:
    parts = urlsplit(url)
    query = urlencode(
        [(key, "***REDACTED***" if _sensitive_key(key) else value) for key, value in parse_qsl(parts.query)],
        doseq=True,
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
