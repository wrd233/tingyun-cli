from __future__ import annotations

import hashlib
import json

import httpx

from ty_apm_cli.auth import AuthManager, build_auth_signature
from ty_apm_cli.config import AppConfig
from ty_apm_cli.redact import redact, redact_url


def test_build_auth_signature_uses_pdf_rule() -> None:
    timestamp = 1710000000000
    expected_raw = 'api_key="key"&secret_key="secret"&timestamp="1710000000000"'
    assert build_auth_signature("key", "secret", timestamp) == hashlib.md5(expected_raw.encode("utf-8")).hexdigest()


def test_token_fetch_and_cache(tmp_path) -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        assert request.url.path == "/auth-api/auth/token"
        assert "api_key" in request.url.params
        assert "auth" in request.url.params
        return httpx.Response(200, json={"code": 200, "msg": "success", "access_token": "token-123456789"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = AppConfig(base_url="https://tingyun.example", api_key="key", secret_key="secret", output_dir=tmp_path)
    manager = AuthManager(config, http_client=client)

    first = manager.get_token()
    second = manager.get_token()
    refreshed = manager.get_token(force_refresh=True)

    assert first.access_token == "token-123456789"
    assert first.from_cache is False
    assert second.from_cache is True
    assert refreshed.from_cache is False
    assert calls["count"] == 2
    cache = json.loads((tmp_path / "token-cache.json").read_text(encoding="utf-8"))
    assert cache["access_token"] == "token-123456789"


def test_redaction_masks_sensitive_keys_and_urls() -> None:
    payload = {
        "Authorization": "Bearer token-123456789",
        "nested": {"secret_key": "abcdef1234567890", "safe": "value"},
    }
    redacted = redact(payload)
    assert redacted["Authorization"] != payload["Authorization"]
    assert redacted["nested"]["secret_key"] == "abcd***7890"
    assert redacted["nested"]["safe"] == "value"
    assert redact({"domain_counts": {"auth": 1}, "authenticated": True}) == {
        "domain_counts": {"auth": 1},
        "authenticated": True,
    }
    safe_url = redact_url("https://example/auth-api/auth/token?api_key=abcdef123456&auth=xyz987654321&timestamp=1")
    assert "abcdef123456" not in safe_url
    assert "xyz987654321" not in safe_url
