import json
from pathlib import Path

import pytest

from tingyun_cli.commands import export_sanitized_run, run_source_capability
from tingyun_cli.config import Config
from tingyun_cli.safety import ADVANCED_SOURCE_READ_ENDPOINTS, assert_read_endpoint, assert_source_read_endpoint
from tingyun_cli.source_capabilities import (
    alarm_event_detail_request,
    alarm_events_request,
    alarm_metric_series_request,
    application_instances_request,
    external_uri_request,
    performance_timeseries_requests,
    recent_request_ranking_request,
    trace_exceptions_request,
)
from tingyun_cli.storage import RunStore


class FakeClock:
    def __init__(self):
        self.now = 1_783_430_000.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class RawFirstTransport:
    def __init__(self, root, response):
        self.root = root
        self.response = response
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        inflight = list((self.root / ".inflight").glob("*/raw/request-0001.json"))
        assert len(inflight) == 1
        assert not list((self.root / ".inflight").glob("*/evidence/*.json"))
        return self.response


def _config(root):
    return Config(base_url="https://tingyun.example", data_root=root, min_request_interval_seconds=0)


def _write_item_run(store, item):
    run = store.begin_run(command="collect", run_type="COLLECT")
    store.write_json(run.path / "evidence" / "items.json", {"schema_version": 1, "kind": "items", "status": "SUCCESS", "data": {"items": [item]}})
    store.finalize_run(run, manifest={"schema_version": 1, "run_id": run.run_id, "run_type": "COLLECT", "overall": "SUCCESS", "artifacts": [{"kind": "items", "path": "evidence/items.json", "status": "SUCCESS"}], "coverage_ref": "coverage.json", "live_request_count": 0}, coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {}})
    return run.run_id


def test_advanced_source_safety_surface_is_exactly_the_formal_recipe_paths():
    time_context = {"endpoint": {"timePeriod": 30, "endTime": "2026-07-08 08:50"}}
    identity = {"alarmEventId": "alarm-1", "metric": "response", "codeIndex": "avg", "policyId": "policy-1", "policyCheckMode": 1, "product": "SERVER", "targetType": "ACTION", "eventItems": [{"eventTraceId": "event-1"}]}
    trace_identity = {"bizSystemId": "biz-1", "applicationId": "app-1", "actionGuid": "guid-1", "traceId": "trace-1", "actionType": "WEB"}
    requests = [
        *performance_timeseries_requests("biz-1", time_context)[1:],
        alarm_events_request(time_context),
        alarm_event_detail_request("alarm-1", time_context),
        alarm_metric_series_request(identity, time_context),
        application_instances_request("biz-1", "app-1", time_context),
        *(recent_request_ranking_request("biz-1", time_context, ranking=ranking) for ranking in ("response", "error", "throughput")),
        external_uri_request("biz-1", "app-1", time_context),
        trace_exceptions_request(trace_identity, time_context),
    ]
    actual = {(request["method"], request["path"]) for request in requests}

    assert actual == ADVANCED_SOURCE_READ_ENDPOINTS
    for method, path in actual:
        assert_source_read_endpoint(method, path)
    with pytest.raises(ValueError):
        assert_read_endpoint("POST", "/server-api/webaction/list/responseList")
    with pytest.raises(ValueError):
        assert_source_read_endpoint("POST", "/nalarm-api/config/setting/save")


def test_source_writes_raw_before_normalized_and_uses_current_run_lineage(tmp_path):
    store = RunStore(tmp_path)
    parent_run_id = _write_item_run(store, {"item_ref": "item-0001", "kind": "business_system_candidate", "wire_identity": {"bizSystemId": "biz-1"}})
    transport = RawFirstTransport(tmp_path, {"status": 200, "data": {"content": [{"applicationId": "app-1", "actionId": "action-1", "requestType": "WEB"}]}})

    receipt = run_source_capability(store=store, config=_config(tmp_path), capability="recent_requests", source_run_id=parent_run_id, source_item_ref="item-0001", time_context_value="last_30m", ranking="response", transport=transport, clock=FakeClock())

    run_path = tmp_path / "runs" / receipt["run_id"]
    item = json.loads((run_path / "evidence" / "recent_requests.json").read_text())["data"]["items"][0]
    manifest = json.loads((run_path / "manifest.json").read_text())
    assert item["source_run_id"] == receipt["run_id"]
    assert item["source_refs"] == ["raw/response-0001.json"]
    assert manifest["source"] == {"run_id": parent_run_id, "item_ref": "item-0001"}


def test_sanitized_source_export_removes_friendly_identity_urls_actions_and_raw_responses(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="source", run_type="SOURCE")
    store.write_json(run.path / "raw" / "request-0001.json", {"body": {"bizSystemId": "bs-1061", "applicationId": "app-1626"}})
    store.write_json(run.path / "raw" / "response-0001.json", {"response": {"traceId": "trace-4429"}})
    store.write_json(run.path / "evidence" / "external_calls.json", {
        "schema_version": 1,
        "kind": "external_calls",
        "status": "SUCCESS",
        "data": {"items": [{
            "item_ref": "external-0001",
            "source_run_id": run.run_id,
            "scope": {"type": "external_dependency", "business_system_id": "bs-1061", "application_id": "app-1626", "dependency": "upstream.example"},
            "identity": {"trace_id": "trace-4429", "action_id": "action-13172", "alarm_id": "alarm-918"},
            "dependency_uri": "https://upstream.example/private",
            "available_actions": ["investigate_trace"],
        }]},
    })
    store.finalize_run(run, manifest={"schema_version": 1, "run_id": run.run_id, "run_type": "SOURCE", "overall": "SUCCESS", "artifacts": [{"kind": "external_calls", "path": "evidence/external_calls.json", "status": "SUCCESS"}], "coverage_ref": "coverage.json", "live_request_count": 1}, coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {}})

    output = tmp_path / "export"
    export_sanitized_run(store, run.run_id, output)
    exported_text = "\n".join(path.read_text() for path in output.rglob("*.json"))

    assert not (output / "raw" / "response-0001.json").exists()
    for secret in ("bs-1061", "app-1626", "trace-4429", "action-13172", "alarm-918", "upstream.example", "investigate_trace"):
        assert secret not in exported_text


def test_local_depth_modules_have_no_http_or_run_dependencies():
    root = Path(__file__).parents[1] / "src" / "tingyun_cli"
    for module in ("budgeting.py", "compare.py", "corrections.py", "evidence.py", "narrowing.py", "promotion.py", "selection.py", "triage.py", "workflows.py"):
        text = (root / module).read_text(encoding="utf-8")
        assert "HttpExecutor" not in text
        assert "RunStore" not in text
        assert "urllib" not in text
