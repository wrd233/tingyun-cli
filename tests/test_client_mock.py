from __future__ import annotations

import json
from pathlib import Path

import httpx

from ty_apm_cli.artifacts import RunRecorder
from ty_apm_cli.catalog import Catalog
from ty_apm_cli.client import TingyunClient
from ty_apm_cli.config import AppConfig


CATALOG_PATH = Path(__file__).resolve().parents[1] / "catalog" / "tingyun-apm-api.catalog.json"


def test_mock_read_api_call_saves_artifacts(tmp_path) -> None:
    catalog = Catalog(CATALOG_PATH)
    endpoint = catalog.get("business_system.2_1.application_business_list")
    seen = {"api_called": False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth-api/auth/token":
            return httpx.Response(200, json={"access_token": "mock-access-token-abcdef"})
        seen["api_called"] = True
        assert request.url.path == "/server-api/application/business/list"
        assert request.headers["authorization"] == "Bearer mock-access-token-abcdef"
        return httpx.Response(200, json={"code": 200, "data": {"content": []}})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    config = AppConfig(
        base_url="https://tingyun.example",
        api_key="key",
        secret_key="secret",
        output_dir=tmp_path,
        run_id="run_test",
    )
    recorder = RunRecorder(config)
    envelope = TingyunClient(config, http_client=http_client, recorder=recorder).call(
        endpoint, {"endTime": "2026-06-14 20:00:00", "timePeriod": 60}
    )

    assert seen["api_called"] is True
    assert envelope["ok"] is True
    assert envelope["meta"]["raw_file"].endswith(".response.raw.json")
    request_payload = json.loads((tmp_path / "runs" / "run_test" / "calls" / "0001_business_system.2_1.application_business_list.request.json").read_text(encoding="utf-8"))
    assert request_payload["headers"]["Authorization"] != "Bearer mock-access-token-abcdef"
    assert (tmp_path / "runs" / "run_test" / "logs" / "calls.jsonl").exists()


def test_non_read_endpoint_is_rejected_before_http(tmp_path) -> None:
    catalog = Catalog(CATALOG_PATH)
    endpoint = catalog.get("business_system.2_2_5.graph_savetopolayout")

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("HTTP must not be called for non-read endpoints")

    config = AppConfig(base_url="https://tingyun.example", api_key="key", secret_key="secret", output_dir=tmp_path)
    envelope = TingyunClient(config, http_client=httpx.Client(transport=httpx.MockTransport(handler))).call(endpoint, {"key": "x"})

    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "UnsupportedSafetyLevel"
    assert envelope["meta"]["safety"] == "write"
