from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SENSITIVE_KEY_RE = re.compile(
    r"^(authorization|access[_-]?token|token|secret|secret[_-]?key|api[_-]?key|auth|password)$",
    re.IGNORECASE,
)


def mask(value: Any) -> str:
    text = "" if value is None else str(value)
    if len(text) <= 8:
        return "***"
    return f"{text[:4]}***{text[-4:]}"


def is_sensitive_key(key: str) -> bool:
    return bool(SENSITIVE_KEY_RE.search(key))


def should_redact_value(key: str, value: Any) -> bool:
    if not is_sensitive_key(key):
        return False
    if key.lower() == "auth" and not isinstance(value, str):
        return False
    return True


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if should_redact_value(str(key), item):
                result[key] = mask(item)
            else:
                result[key] = redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value


def redact_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    safe_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        safe_query.append((key, mask(value) if is_sensitive_key(key) else value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(safe_query), parts.fragment))
