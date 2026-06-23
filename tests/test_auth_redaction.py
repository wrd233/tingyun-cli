from ty_apm_cli.auth import build_auth_signature
from ty_apm_cli.redact import redact, redact_url


def test_auth_signature_matches_manual_formula():
    assert build_auth_signature("ak", "sk", 123) == "4474e4d64d4a8d199a4766f19a92d460"


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
