import json
import os

from tingyun_cli.commands import run_source_capability
from tingyun_cli.config import Config
from tingyun_cli.storage import RunStore


class FakeClock:
    def __init__(self):
        self.now = 1_783_430_000.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        return self.responses.pop(0)


def _config(tmp_path):
    return Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0)


def _write_item_run(store, item):
    run = store.begin_run(command="collect", run_type="COLLECT")
    store.write_json(run.path / "evidence" / "items.json", {
        "schema_version": 1,
        "kind": "items",
        "status": "SUCCESS",
        "data": {"items": [item]},
    })
    store.finalize_run(
        run,
        manifest={
            "schema_version": 1,
            "run_id": run.run_id,
            "run_type": "COLLECT",
            "overall": "SUCCESS",
            "artifacts": [{"kind": "items", "path": "evidence/items.json", "status": "SUCCESS"}],
            "coverage_ref": "coverage.json",
            "live_request_count": 0,
        },
        coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {"items": {"status": "SUCCESS"}}},
    )
    return run.run_id


def test_source_capability_alarm_events_creates_immutable_run_without_source_item(tmp_path):
    store = RunStore(tmp_path)
    transport = FakeTransport([{"status": 200, "data": {"content": [{
        "id": "alarm-1",
        "level": "CRITICAL",
        "target": {"value": "findRelation"},
        "parentGroup": {"$biz_system_id": "1061", "$application_id": "1626"},
    }]}}])

    receipt = run_source_capability(
        store=store,
        config=_config(tmp_path),
        capability="alarm_events",
        time_context_value="last_30m",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    artifact = json.loads((run_path / "evidence" / "alarm_events.json").read_text())
    assert receipt["status"] == "SUCCESS"
    assert transport.requests[0]["path"] == "/nalarm-api/event/traceList"
    assert artifact["kind"] == "alarm_events"
    item = artifact["data"]["items"][0]
    assert item["item_type"] == "alarm_event"
    assert item["scope"] == {"type": "alarm", "alarm_id": "alarm-1"}
    assert item["identity"]["business_system_id"] == "1061"
    assert item["identity"]["application_id"] == "1626"
    assert item["wire_identity"]["alarmEventId"] == "alarm-1"
    assert item["source_run_id"] == receipt["run_id"]
    assert item["source_refs"] == ["raw/response-0001.json"]


def test_source_capability_recent_requests_is_identity_gated_and_ranking_specific(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "item-0001",
        "kind": "business_system_candidate",
        "wire_identity": {"bizSystemId": "1061"},
    })
    transport = FakeTransport([{"status": 200, "data": {"content": [{
        "applicationId": 1626,
        "applicationName": "app",
        "actionId": 13172,
        "actionName": "findRelation",
        "requestType": "WEB",
        "responseTimeMillisecondAvg": 129000,
        "errorRate": 0.5,
    }]}}])

    receipt = run_source_capability(
        store=store,
        config=_config(tmp_path),
        capability="recent_requests",
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        ranking="error",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    artifact = json.loads((run_path / "evidence" / "recent_requests.json").read_text())
    assert transport.requests[0]["path"] == "/server-api/webaction/list/errorList"
    assert artifact["source"]["capability"] == "list_recent_requests"
    assert artifact["source"]["ranking"] == "error"
    item = artifact["data"]["items"][0]
    assert item["item_type"] == "request_candidate"
    assert item["scope"] == {
        "type": "transaction",
        "business_system_id": "1061",
        "application_id": 1626,
        "action_id": 13172,
    }
    assert item["source"] == {"capability": "list_recent_requests", "ranking": "error"}
    assert item["selection_provenance"] == {"strategy": "error_rank", "rank": 1, "candidate_count": 1}
    assert item["metrics"]["response_avg"]["value"] == 129000
    assert item["wire_identity"]["bizSystemId"] == "1061"
    assert item["available_actions"] == []
    assert item["source_run_id"] == receipt["run_id"]
    assert item["source_refs"] == ["raw/response-0001.json"]


def test_source_capability_blocks_missing_identity_before_http(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "item-0001",
        "kind": "candidate",
        "wire_identity": {"applicationId": "1626"},
    })
    transport = FakeTransport([])

    receipt = run_source_capability(
        store=store,
        config=_config(tmp_path),
        capability="recent_requests",
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        ranking="error",
        transport=transport,
        clock=FakeClock(),
    )

    assert receipt["status"] == "BLOCKED"
    assert receipt["reason_code"] == "SOURCE_IDENTITY_INCOMPLETE"
    assert transport.requests == []


def test_source_capability_alarm_detail_uses_alarm_identity_and_normalizes_detail(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "alarm-event-0001",
        "kind": "alarm_event",
        "wire_identity": {"alarmEventId": "alarm-1", "bizSystemId": "1061", "applicationId": "1626"},
    })
    transport = FakeTransport([{"status": 200, "data": {
        "id": "alarm-1",
        "target": {"value": "findRelation"},
        "parentGroup": {"$biz_system_id": "1061", "$application_id": "1626"},
        "alarmEventItems": [{"eventTraceId": "event-trace-1"}],
    }}])

    receipt = run_source_capability(
        store=store,
        config=_config(tmp_path),
        capability="alarm_detail",
        source_run_id=source_run_id,
        source_item_ref="alarm-event-0001",
        time_context_value="last_30m",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    artifact = json.loads((run_path / "evidence" / "alarm_detail.json").read_text())
    item = artifact["data"]["items"][0]

    assert transport.requests[0]["path"] == "/nalarm-api/event/trace"
    assert transport.requests[0]["body"]["id"] == "alarm-1"
    assert item["item_type"] == "alarm_detail"
    assert item["scope"] == {"type": "alarm", "alarm_id": "alarm-1"}
    assert item["identity"]["event_trace_ids"] == ["event-trace-1"]
    assert item["identity"]["business_system_id"] == "1061"
    assert item["source_run_id"] == receipt["run_id"]


def test_source_capability_alarm_metric_series_requires_detail_identity_and_preserves_series(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "alarm-detail-0001",
        "kind": "alarm_detail",
        "wire_identity": {
            "alarmEventId": 123,
            "metric": "response_time",
            "codeIndex": "avg",
            "policyId": 456,
            "policyCheckMode": 1,
            "product": "SERVER",
            "targetType": "ACTION",
            "eventItems": [{"eventTraceId": "event-trace-1"}],
        },
    })
    transport = FakeTransport([{"status": 200, "data": {"series": [{"time": "08:45", "value": 129000}]}}])

    receipt = run_source_capability(
        store=store,
        config=_config(tmp_path),
        capability="alarm_metric_series",
        source_run_id=source_run_id,
        source_item_ref="alarm-detail-0001",
        time_context_value="last_30m",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    artifact = json.loads((run_path / "evidence" / "alarm_metric_series.json").read_text())

    assert transport.requests[0]["path"] == "/nalarm-api/event/metric/chart"
    assert transport.requests[0]["body"]["metric"] == "response_time"
    assert artifact["kind"] == "alarm_metric_series"
    assert artifact["source"]["capability"] == "read_alarm_metric_series"
    assert artifact["data"]["items"][0]["value"] == 129000
    assert artifact["data"]["items"][0]["source_refs"] == ["raw/response-0001.json"]


def test_source_capability_application_instances_normalizes_complete_instance_list(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "item-0001",
        "kind": "application_candidate",
        "wire_identity": {"bizSystemId": "1061", "applicationId": "1626"},
    })
    transport = FakeTransport([{"status": 200, "data": {
        "nodes": [
            {"id": "app-1626", "type": "APPLICATION", "name": "group-legal"},
            {"id": "server1", "type": "INSTANCE", "instanceId": "server1", "name": "server1", "ip": "10.0.0.1"},
            {"id": "server2", "type": "INSTANCE", "instanceId": "server2", "name": "server2", "ip": "10.0.0.2"},
        ],
        "edges": [],
    }}])

    receipt = run_source_capability(
        store=store,
        config=_config(tmp_path),
        capability="application_instances",
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    artifact = json.loads((run_path / "evidence" / "instance_context.json").read_text())

    assert transport.requests[0]["path"] == "/server-api/graph/information"
    assert artifact["source"]["capability"] == "read_application_overview"
    assert artifact["data"]["instance_count"] == 2
    assert [item["identity"]["instance_id"] for item in artifact["data"]["items"]] == ["server1", "server2"]
    assert artifact["data"]["items"][0]["scope"] == {
        "type": "instance",
        "business_system_id": "1061",
        "application_id": "1626",
        "instance_id": "server1",
    }
    assert artifact["data"]["items"][0]["source_run_id"] == receipt["run_id"]


def test_source_capability_external_calls_normalizes_dependency_items(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "item-0001",
        "kind": "application_candidate",
        "wire_identity": {"bizSystemId": "1061", "applicationId": "1626"},
    })
    transport = FakeTransport([{"status": 200, "data": {"content": [{
        "host": "file-open.tianyancha.com",
        "uri": "https://file-open.tianyancha.com/open",
        "callCount": 17,
        "errorCount": 9,
        "responseTimeMillisecondAvg": 129000,
    }]}}])

    receipt = run_source_capability(
        store=store,
        config=_config(tmp_path),
        capability="external_calls",
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    artifact = json.loads((run_path / "evidence" / "external_calls.json").read_text())
    item = artifact["data"]["items"][0]

    assert transport.requests[0]["path"] == "/server-api/application/ext/uriList"
    assert item["item_type"] == "external_dependency"
    assert item["scope"] == {
        "type": "external_dependency",
        "business_system_id": "1061",
        "application_id": "1626",
        "dependency": "file-open.tianyancha.com",
    }
    assert item["metrics"]["call_count"]["value"] == 17
    assert item["metrics"]["error_count"]["value"] == 9
    assert item["metrics"]["response_avg"]["unit"] == "ms"
    assert item["dependency_uri"] == "https://file-open.tianyancha.com/open"
    assert item["source_refs"] == ["raw/response-0001.json"]


def test_source_capability_trace_exceptions_normalizes_exception_items(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "item-0001",
        "kind": "trace",
        "wire_identity": {
            "bizSystemId": "1061",
            "applicationId": "1626",
            "actionGuid": "ag-1",
            "traceId": "trace-129s",
            "actionType": "WEB",
        },
    })
    transport = FakeTransport([{"status": 200, "data": {"content": [{
        "exceptionClass": "java.net.ConnectException",
        "message": "Connection timed out",
        "stack": ["Socket.connect", "HttpClient.execute"],
    }]}}])

    receipt = run_source_capability(
        store=store,
        config=_config(tmp_path),
        capability="trace_exceptions",
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    artifact = json.loads((run_path / "evidence" / "trace_exceptions.json").read_text())
    item = artifact["data"]["items"][0]

    assert transport.requests[0]["path"] == "/server-api/action/trace/detail/exceptions"
    assert item["item_type"] == "trace_exception"
    assert item["scope"] == {"type": "trace", "trace_id": "trace-129s"}
    assert item["identity"]["exception_class"] == "java.net.ConnectException"
    assert item["message"] == "Connection timed out"
    assert item["stack"] == ["Socket.connect", "HttpClient.execute"]
    assert item["source_run_id"] == receipt["run_id"]


def test_response_ranking_alone_can_expose_main_verified_trace_action(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "item-0001",
        "kind": "business_system_candidate",
        "wire_identity": {"bizSystemId": "1061"},
    })
    row = {"applicationId": "1626", "actionId": "13172", "requestType": "TX,IF", "actionName": "SpringController/example/work"}

    receipt = run_source_capability(
        store=store, config=_config(tmp_path), capability="recent_requests",
        source_run_id=source_run_id, source_item_ref="item-0001", time_context_value="last_30m",
        ranking="response", transport=FakeTransport([{"status": 200, "data": {"content": [row]}}]), clock=FakeClock(),
    )

    item = json.loads((tmp_path / "runs" / receipt["run_id"] / "evidence" / "recent_requests.json").read_text())["data"]["items"][0]
    assert item["available_actions"] == ["investigate_trace"]
    assert item["source_run_id"] == receipt["run_id"]
    assert item["wire_identity"]["requestType"] == "TX,IF"


def test_optional_performance_series_are_one_request_source_runs(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {"item_ref": "item-0001", "kind": "business_system_candidate", "wire_identity": {"bizSystemId": "1061"}})

    for capability, expected_path, unit in [
        ("performance_error_series", "/server-api/application/charts/error", "percent"),
        ("performance_throughput_series", "/server-api/application/charts/throught", "per_second"),
    ]:
        transport = FakeTransport([{"status": 200, "data": {"series": [{"time": "08:45", "value": 3}]}}])
        receipt = run_source_capability(
            store=store, config=_config(tmp_path), capability=capability,
            source_run_id=source_run_id, source_item_ref="item-0001", time_context_value="last_30m",
            transport=transport, clock=FakeClock(),
        )
        run_path = tmp_path / "runs" / receipt["run_id"]
        manifest = json.loads((run_path / "manifest.json").read_text())
        artifact = json.loads(next((run_path / "evidence").glob("performance_*.json")).read_text())
        assert transport.requests[0]["path"] == expected_path
        assert manifest["live_request_count"] == 1
        assert json.loads((run_path / "preflight.json").read_text())["expected_logical_request_count"] == 1
        assert artifact["data"]["metric"]["unit"] == unit


def test_source_failed_and_empty_are_separate_with_dynamic_provenance(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {"item_ref": "item-0001", "kind": "business_system_candidate", "wire_identity": {"bizSystemId": "1061"}})

    failed = run_source_capability(
        store=store, config=_config(tmp_path), capability="recent_requests", source_run_id=source_run_id,
        source_item_ref="item-0001", time_context_value="last_30m", ranking="response",
        transport=FakeTransport([{"transport_status": 500, "status": 500, "message": "failure"}]), clock=FakeClock(),
    )
    empty = run_source_capability(
        store=store, config=_config(tmp_path), capability="recent_requests", source_run_id=source_run_id,
        source_item_ref="item-0001", time_context_value="last_30m", ranking="response",
        transport=FakeTransport([{"status": 200, "data": {"content": []}}]), clock=FakeClock(),
    )

    failed_artifact = json.loads((tmp_path / "runs" / failed["run_id"] / "evidence" / "recent_requests.json").read_text())
    empty_artifact = json.loads((tmp_path / "runs" / empty["run_id"] / "evidence" / "recent_requests.json").read_text())
    assert failed_artifact["status"] == "FAILED"
    assert failed_artifact["derived_from"] == ["raw/response-0001.json"]
    assert failed_artifact["error"]["reason_code"] == "UPSTREAM_HTTP_ERROR"
    assert empty_artifact["status"] == "EMPTY"


def test_source_validation_and_auth_happen_before_live_lock(tmp_path, monkeypatch):
    monkeypatch.delenv("TINGYUN_AUTHORIZATION", raising=False)
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {"item_ref": "item-0001", "kind": "candidate", "wire_identity": {}})
    (tmp_path / "live.lock").write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")

    invalid = run_source_capability(
        store=store, config=_config(tmp_path), capability="recent_requests", source_run_id=source_run_id,
        source_item_ref="item-0001", time_context_value="last_30m", transport=FakeTransport([]), clock=FakeClock(),
    )
    auth_missing = run_source_capability(
        store=store, config=_config(tmp_path), capability="alarm_events", time_context_value="last_30m", clock=FakeClock(),
    )

    assert invalid["reason_code"] == "SOURCE_IDENTITY_INCOMPLETE"
    assert auth_missing["reason_code"] == "AUTH_NOT_CONFIGURED"
