import httpx

from ty_apm_cli.auth import AuthManager, build_auth_signature, build_auth_source
from ty_apm_cli.config import AppConfig
from ty_apm_cli.redact import redact, redact_url


def test_auth_source_string_uses_timestamp_literal():
    source = build_auth_source("ak", "sk", 123)
    assert source == 'api_key="ak"&secret_key="sk"&timestamp="123"'
    assert "×tamp" not in source


def test_auth_signature_matches_manual_formula():
    assert build_auth_signature("ak", "sk", 123) == "4474e4d64d4a8d199a4766f19a92d460"


def test_token_request_uses_timestamp_query_and_redacts_cache(tmp_path):
    seen = {}

    def handler(request):
        seen["query"] = str(request.url.query)
        return httpx.Response(200, json={"code": 200, "msg": "success", "access_token": "live-token"})

    cfg = AppConfig(
        base_url="https://tingyun.example",
        api_key="ak",
        secret_key="sk",
        artifacts_dir=tmp_path,
        token_cache_path=tmp_path / "token-cache.json",
    )
    token = AuthManager(cfg, http_client=httpx.Client(transport=httpx.MockTransport(handler))).get_token()
    assert token.access_token == "live-token"
    assert "timestamp=" in seen["query"]
    assert "%C3%97tamp" not in seen["query"]
    assert not (tmp_path / "runs").exists()


def test_redaction_masks_secret_strings_and_bearer_headers():
    payload = {
        "api_key": "abc",
        "Authorization": "Bearer live-token",
        "nested": {"access_token": "token"},
        "domain_counts": {"auth": 1},
    }
    redacted = redact(payload)
    assert redacted["api_key"] == "***REDACTED***"
    assert redacted["Authorization"] == "***REDACTED***"
    assert redacted["nested"]["access_token"] == "***REDACTED***"
    assert redacted["domain_counts"]["auth"] == 1


def test_redact_url_masks_auth_query_values():
    url = redact_url("https://x/auth-api/auth/token?api_key=a&auth=b&timestamp=1")
    assert "api_key=%2A%2A%2AREDACTED%2A%2A%2A" in url
    assert "auth=%2A%2A%2AREDACTED%2A%2A%2A" in url
    assert "timestamp=1" in url
