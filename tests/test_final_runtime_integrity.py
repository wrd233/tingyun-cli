from __future__ import annotations

import json
import os
from dataclasses import fields
from pathlib import Path

import pytest

import tingyun_cli
import tingyun_cli.http
from tingyun_cli.commands import run_collect, run_discover, run_investigate, run_source_capability
from tingyun_cli.config import Config
from tingyun_cli.http import ExecutionResult, HttpExecutor
from tingyun_cli.storage import RunStore


class FakeClock:
    def __init__(self):
        self.now = 1_783_430_000.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class SequenceTransport:
    def __init__(self, responses, *, recover_auth_result=True):
        self.responses = list(responses)
        self.requests = []
        self.recover_auth_result = recover_auth_result
        self.recover_auth_calls = 0

    def send(self, request):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    def recover_auth(self):
        self.recover_auth_calls += 1
        return self.recover_auth_result


def _config(root):
    return Config(base_url="https://tingyun.example", data_root=root, min_request_interval_seconds=0)


def _core_request():
    return {
        "endpoint_id": "ep_get_server_api_data_business_getbusinesstree",
        "method": "GET",
        "path": "/server-api/data/business/getBusinessTree",
    }


def _executor(root, transport):
    store = RunStore(root)
    run = store.begin_run(command="test", run_type="TEST")
    return HttpExecutor(store=store, run=run, config=_config(root), transport=transport, clock=FakeClock())


def _write_item_run(store, item):
    run = store.begin_run(command="fixture", run_type="COLLECT")
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
        coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {}},
    )
    return run.run_id


def test_pytest_imports_runtime_from_current_checkout():
    repo_src = (Path(__file__).resolve().parents[1] / "src").resolve()
    package_path = Path(tingyun_cli.__file__).resolve()
    http_path = Path(tingyun_cli.http.__file__).resolve()

    assert os.path.commonpath([str(package_path), str(repo_src)]) == str(repo_src)
    assert os.path.commonpath([str(http_path), str(repo_src)]) == str(repo_src)


def test_execution_result_contract_is_importable_and_complete():
    assert {field.name for field in fields(ExecutionResult)} == {
        "outcome",
        "response",
        "final_response_ref",
        "final_error_ref",
        "attempt_refs",
        "attempt_count",
        "transient_retried",
        "auth_recovered",
        "reason_code",
    }


@pytest.mark.parametrize(
    ("status", "expected_attempts"),
    [(500, 1), (502, 2), (503, 2), (504, 2)],
)
def test_core_retry_contract_is_exact(status, expected_attempts, tmp_path):
    responses = [{"transport_status": status, "status": status}]
    if expected_attempts == 2:
        responses.append({"transport_status": 200, "status": 200, "data": {"ok": True}})
    transport = SequenceTransport(responses)

    result = _executor(tmp_path / str(status), transport).execute(_core_request())

    assert result.attempt_count == expected_attempts
    assert len(transport.requests) == expected_attempts
    assert result.transient_retried is (expected_attempts == 2)


def test_auth_recovery_is_shared_by_all_requests_in_one_executor(tmp_path):
    transport = SequenceTransport([
        {"transport_status": 401, "status": 401},
        {"transport_status": 200, "status": 200, "data": {"first": True}},
        {"transport_status": 401, "status": 401},
    ])
    executor = _executor(tmp_path, transport)

    first = executor.execute(_core_request())
    second = executor.execute(_core_request())

    assert first.outcome == "SUCCESS"
    assert first.auth_recovered is True
    assert first.attempt_count == 2
    assert second.outcome == "FAILED"
    assert second.reason_code == "AUTH_EXPIRED"
    assert second.auth_recovered is False
    assert second.attempt_count == 1
    assert transport.recover_auth_calls == 1


def test_retry_success_drives_artifact_dynamic_provenance(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_item_run(store, {
        "item_ref": "item-0001",
        "kind": "business_system_candidate",
        "wire_identity": {"bizSystemId": "biz-1"},
    })
    transport = SequenceTransport([
        TimeoutError("first attempt"),
        {"status": 200, "data": {"nodes": [{"id": "app-1"}], "edges": []}},
        {"status": 200, "data": {"avg": [10]}},
        {"status": 200, "data": [{
            "applicationId": "app-1",
            "actionId": "action-1",
            "requestType": "WEB",
        }]},
    ])

    receipt = run_collect(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=transport,
        clock=FakeClock(),
    )

    topology = json.loads((tmp_path / "runs" / receipt["run_id"] / "evidence" / "topology.json").read_text())
    assert topology["derived_from"] == ["raw/response-0002.json"]
    assert topology["execution"]["attempt_count"] == 2
    assert topology["execution"]["final_response_ref"] == "raw/response-0002.json"


@pytest.mark.parametrize(
    ("surface", "path", "allowed"),
    [
        ("CORE", "/server-api/data/business/getBusinessTree", True),
        ("ADVANCED_SOURCE", "/nalarm-api/event/traceList", True),
        ("CORE", "/nalarm-api/event/traceList", False),
        ("ADVANCED_SOURCE", "/server-api/data/business/getBusinessTree", False),
        ("WRITE", "/server-api/data/business/getBusinessTree", False),
        ("UNKNOWN", "/server-api/data/business/getBusinessTree", False),
    ],
)
def test_runtime_surface_routing_is_exact(surface, path, allowed, tmp_path):
    request = {
        "endpoint_id": "test",
        "runtime_surface": surface,
        "method": "GET" if path.endswith("getBusinessTree") else "POST",
        "path": path,
    }
    executor = _executor(tmp_path / surface / path.strip("/").replace("/", "-"), SequenceTransport([{"status": 200, "data": {}}]))

    if allowed:
        assert executor.execute(request).outcome == "SUCCESS"
    else:
        with pytest.raises(ValueError):
            executor.execute(request)


SOURCE_CASES = [
    ("performance_error_series", "response", {"bizSystemId": "biz-1"}, {"status": 200, "data": {"series": [{"time": "t", "value": 1}]}}, "performance_error_series.json"),
    ("performance_throughput_series", "response", {"bizSystemId": "biz-1"}, {"status": 200, "data": {"series": [{"time": "t", "value": 2}]}}, "performance_throughput_series.json"),
    ("alarm_events", "response", None, {"status": 200, "data": {"content": [{"id": "alarm-1"}]}}, "alarm_events.json"),
    ("alarm_detail", "response", {"alarmEventId": "alarm-1"}, {"status": 200, "data": {"id": "alarm-1"}}, "alarm_detail.json"),
    ("alarm_metric_series", "response", {"alarmEventId": "alarm-1", "metric": "response", "codeIndex": "avg", "policyId": "p-1", "policyCheckMode": 1, "product": "SERVER", "targetType": "ACTION", "eventItems": [{"eventTraceId": "e-1"}]}, {"status": 200, "data": {"series": [{"time": "t", "value": 3}]}}, "alarm_metric_series.json"),
    ("recent_requests", "response", {"bizSystemId": "biz-1"}, {"status": 200, "data": {"content": [{"applicationId": "app-1", "actionId": "action-1", "requestType": "WEB"}]}}, "recent_requests.json"),
    ("recent_requests", "error", {"bizSystemId": "biz-1"}, {"status": 200, "data": {"content": [{"applicationId": "app-1", "actionId": "action-1", "requestType": "WEB"}]}}, "recent_requests.json"),
    ("recent_requests", "throughput", {"bizSystemId": "biz-1"}, {"status": 200, "data": {"content": [{"applicationId": "app-1", "actionId": "action-1", "requestType": "WEB"}]}}, "recent_requests.json"),
    ("application_instances", "response", {"bizSystemId": "biz-1", "applicationId": "app-1"}, {"status": 200, "data": {"nodes": [{"type": "INSTANCE", "instanceId": "instance-1"}]}}, "instance_context.json"),
    ("external_calls", "response", {"bizSystemId": "biz-1", "applicationId": "app-1"}, {"status": 200, "data": {"content": [{"host": "upstream.example", "callCount": 1}]}}, "external_calls.json"),
    ("trace_exceptions", "response", {"bizSystemId": "biz-1", "treeId": "tree-1", "traceId": "trace-1", "queryTimestamp": 1000}, {"status": 200, "data": [{"type": "ExampleError", "msg": "failed", "stack": ["example.Frame.call(Frame.java:1)"]}]}, "trace_exceptions.json"),
    ("trace_stack", "response", {"bizSystemId": "biz-1", "treeId": "tree-1", "traceId": "trace-1", "queryTimestamp": 1000}, {"status": 200, "data": ["example.Frame.call(Frame.java:1)"]}, "trace_stack.json"),
]


@pytest.mark.parametrize(("capability", "ranking", "wire_identity", "response", "artifact_name"), SOURCE_CASES)
def test_all_advanced_source_recipes_execute_through_runtime(capability, ranking, wire_identity, response, artifact_name, tmp_path):
    root = tmp_path / f"{capability}-{ranking}"
    store = RunStore(root)
    source_run_id = None
    source_item_ref = None
    if wire_identity is not None:
        source_item_ref = "item-0001"
        source_run_id = _write_item_run(store, {
            "item_ref": source_item_ref,
            "kind": "trace_tree_node" if capability in {"trace_exceptions", "trace_stack"} else "fixture",
            "wire_identity": wire_identity,
        })
    transport = SequenceTransport([response])

    receipt = run_source_capability(
        store=store,
        config=_config(root),
        capability=capability,
        source_run_id=source_run_id,
        source_item_ref=source_item_ref,
        time_context_value="last_30m",
        ranking=ranking,
        transport=transport,
        clock=FakeClock(),
    )

    run_path = root / "runs" / receipt["run_id"]
    manifest = json.loads((run_path / "manifest.json").read_text())
    coverage = json.loads((run_path / "coverage.json").read_text())
    artifact = json.loads((run_path / "evidence" / artifact_name).read_text())
    assert receipt["status"] == "SUCCESS"
    assert manifest["run_type"] == "SOURCE"
    assert manifest["live_request_count"] == 1
    assert coverage["overall"] == "SUCCESS"
    assert artifact["execution"]["outcome"] == "SUCCESS"
    assert artifact["derived_from"] == ["raw/response-0001.json"]
    assert (run_path / "raw" / "request-0001.json").exists()
    assert transport.requests[0]["runtime_surface"] == "ADVANCED_SOURCE"


def test_fake_core_golden_path_uses_execution_result_end_to_end(tmp_path):
    store = RunStore(tmp_path)
    discover = run_discover(
        store=store,
        config=_config(tmp_path),
        query="System",
        transport=SequenceTransport([{"status": 200, "data": [{"bizSystemId": "biz-1", "bizSystemName": "System"}]}]),
        clock=FakeClock(),
    )
    collect = run_collect(
        store=store,
        config=_config(tmp_path),
        source_run_id=discover["run_id"],
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=SequenceTransport([
            {"status": 200, "data": {"nodes": [{"id": "app-1"}], "edges": []}},
            {"status": 200, "data": {"avg": [10]}},
            {"status": 200, "data": [{"applicationId": "app-1", "actionId": "action-1", "actionName": "SpringController/synthetic/root", "requestType": "WEB"}]},
        ]),
        clock=FakeClock(),
    )
    trace = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=collect["run_id"],
        source_item_ref="item-0001",
        action="investigate_trace",
        transport=SequenceTransport([{"status": 200, "data": {"actionGuid": "guid-1", "data": {"id": "trace-1"}}}]),
        clock=FakeClock(),
    )
    call_tree = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=trace["run_id"],
        source_item_ref="item-0001",
        action="inspect_call_tree",
        transport=SequenceTransport([{"status": 200, "data": {"nodes": [{"id": "root"}]}}]),
        clock=FakeClock(),
    )

    assert [discover["status"], collect["status"], trace["status"], call_tree["status"]] == ["SUCCESS"] * 4
    for receipt in (discover, collect, trace, call_tree):
        run_path = tmp_path / "runs" / receipt["run_id"]
        manifest = json.loads((run_path / "manifest.json").read_text())
        assert manifest["overall"] == "SUCCESS"
