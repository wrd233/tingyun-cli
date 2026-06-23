import httpx

from ty_apm_cli.auth import TokenResult
from ty_apm_cli.config import AppConfig
from ty_apm_cli.http_client import TingyunClient


class FakeAuth:
    def get_token(self, force_refresh=False):
        return TokenResult("secret-token", 9999999999, False)


def _transport(payload, status=200):
    def handler(request):
        return httpx.Response(status, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_read_call_success_is_raw_first_and_redacted():
    entry = {
        "id": "x.read",
        "method": "POST",
        "path": "/server-api/read",
        "safety": "read",
        "execution_supported": True,
        "request": {"params": [{"name": "applicationId", "required": True}]},
    }
    cfg = AppConfig(base_url="https://tingyun.example")
    client = TingyunClient(cfg, http_client=_transport({"code": 200, "data": {"ok": True}}), auth_manager=FakeAuth())
    record = client.call(entry, {"applicationId": 1})
    assert record.envelope["ok"] is True
    assert record.envelope["data"]["response"]["data"]["ok"] is True
    assert record.request["headers"]["Authorization"] == "***REDACTED***"


def test_blocked_call_never_hits_http():
    entry = {"id": "x.write", "method": "POST", "path": "/write", "safety": "write", "execution_supported": False, "request": {"params": []}}
    cfg = AppConfig(base_url="https://tingyun.example")
    record = TingyunClient(cfg, http_client=_transport({"code": 200}), auth_manager=FakeAuth()).call(entry, {})
    assert record.envelope["ok"] is False
    assert record.envelope["error"]["type"] == "SafetyBlocked"


def test_upstream_business_error_is_structured():
    entry = {"id": "x.read", "method": "GET", "path": "/read", "safety": "read", "execution_supported": True, "request": {"params": []}}
    cfg = AppConfig(base_url="https://tingyun.example")
    record = TingyunClient(cfg, http_client=_transport({"code": 500, "msg": "bad"}), auth_manager=FakeAuth()).call(entry, {})
    assert record.envelope["ok"] is False
    assert record.envelope["error"]["type"] == "UpstreamError"


def test_timeout_error_is_structured():
    def handler(request):
        raise httpx.TimeoutException("boom")

    entry = {"id": "x.read", "method": "GET", "path": "/read", "safety": "read", "execution_supported": True, "request": {"params": []}}
    cfg = AppConfig(base_url="https://tingyun.example")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    record = TingyunClient(cfg, http_client=client, auth_manager=FakeAuth()).call(entry, {})
    assert record.envelope["error"]["type"] == "TimeoutError"
