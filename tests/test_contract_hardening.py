import json
from contextlib import redirect_stdout
from io import StringIO

import pytest

from tingyun_cli.candidates import (
    inspect_candidates_filter,
    inspect_candidates_top,
    normalize_candidates,
)
from tingyun_cli.cli import main
from tingyun_cli.commands import export_sanitized_run, run_collect, run_investigate
from tingyun_cli.config import Config
from tingyun_cli.http import HttpExecutor
from tingyun_cli.storage import RunStore


class SequenceTransport:
    def __init__(self, responses, *, recover_auth_result=True):
        self.responses = list(responses)
        self.requests = []
        self.recoveries = 0
        self.recover_auth_result = recover_auth_result

    def send(self, request):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    def recover_auth(self):
        self.recoveries += 1
        return self.recover_auth_result


class NoopTransport:
    def __init__(self):
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        raise AssertionError("HTTP must not be called")


class FakeClock:
    def __init__(self):
        self.now = 1_783_430_000.0
        self.sleeps = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def _config(tmp_path):
    return Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0)


def _write_discovery_run(store):
    run = store.begin_run(command="discover", run_type="DISCOVERY")
    target = {
        "item_ref": "item-0001",
        "kind": "business_system_candidate",
        "display_name": "billing",
        "wire_identity": {"bizSystemId": "biz-1"},
    }
    store.write_json(run.path / "evidence" / "targets.json", {
        "schema_version": 1,
        "kind": "targets",
        "status": "SUCCESS",
        "data": {"items": [target]},
    })
    store.finalize_run(
        run,
        manifest={
            "schema_version": 1,
            "run_id": run.run_id,
            "run_type": "DISCOVERY",
            "overall": "SUCCESS",
            "artifacts": [{"kind": "targets", "path": "evidence/targets.json", "status": "SUCCESS"}],
            "coverage_ref": "coverage.json",
            "live_request_count": 1,
        },
        coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {"targets": {"status": "SUCCESS"}}},
    )
    return run.run_id


def _write_source_item_run(store, *, run_type="COLLECT", item):
    run = store.begin_run(command="collect", run_type=run_type)
    artifact_name = "candidates.json" if item["kind"] == "candidate" else "trace.json"
    store.write_json(run.path / "evidence" / artifact_name, {
        "schema_version": 1,
        "kind": artifact_name.removesuffix(".json"),
        "status": "SUCCESS",
        "data": {"items": [item]},
    })
    store.finalize_run(
        run,
        manifest={
            "schema_version": 1,
            "run_id": run.run_id,
            "run_type": run_type,
            "overall": "SUCCESS",
            "time_context": {
                "requested": {"kind": "relative", "value": "last_30m"},
                "endpoint": {"timePeriod": 30, "endTime": "2026-07-07 12:00"},
            },
            "artifacts": [{"kind": artifact_name.removesuffix(".json"), "path": f"evidence/{artifact_name}", "status": "SUCCESS"}],
            "coverage_ref": "coverage.json",
            "live_request_count": 1,
        },
        coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {}},
    )
    return run.run_id


def _candidate_row(**overrides):
    row = {
        "bizSystemId": "biz-ignored",
        "applicationId": "app-1",
        "applicationName": "app",
        "actionId": "action-1",
        "actionName": "GET /slow",
        "requestType": "WEB",
        "responseP50": 10,
        "responseP75": 15,
        "responseP95": 20,
        "responseP99": 30,
        "responseTimeMillisecondAvg": 12,
        "throughput": 4,
        "totalCount": 9,
        "errorRate": 0.1,
        "errorTotalCount": 1,
        "slowCount": 2,
        "exceptionCountTotal": 0,
        "apdex": 0.9,
    }
    row.update(overrides)
    return row


def test_executor_returns_attempt_provenance_and_does_not_retry_http_500(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="collect", run_type="COLLECT")
    transport = SequenceTransport([{"transport_status": 500, "status": 500, "message": "server error"}])
    executor = HttpExecutor(
        store=store,
        run=run,
        config=_config(tmp_path),
        transport=transport,
        clock=FakeClock(),
    )

    result = executor.execute({"method": "POST", "path": "/server-api/graph/query/overview", "body": {}, "body_kind": "json"})

    assert result.outcome == "FAILED"
    assert result.response["transport_status"] == 500
    assert result.final_response_ref == "raw/response-0001.json"
    assert result.final_error_ref is None
    assert result.attempt_refs == ("raw/request-0001.json", "raw/response-0001.json")
    assert result.attempt_count == 1
    assert result.transient_retried is False
    assert len(transport.requests) == 1


def test_executor_retries_only_502_503_504_gateway_failures(tmp_path):
    for status in (502, 503, 504):
        store = RunStore(tmp_path / str(status))
        run = store.begin_run(command="collect", run_type="COLLECT")
        transport = SequenceTransport([
            {"transport_status": status, "status": status, "message": "gateway"},
            {"status": 200, "data": {"ok": True}},
        ])
        executor = HttpExecutor(store=store, run=run, config=_config(tmp_path), transport=transport, clock=FakeClock())

        result = executor.execute({"method": "POST", "path": "/server-api/graph/query/overview", "body": {}, "body_kind": "json"})

        assert result.outcome == "SUCCESS"
        assert result.final_response_ref == "raw/response-0002.json"
        assert result.attempt_count == 2
        assert result.transient_retried is True


def test_collect_finalizes_partial_run_when_one_step_fails(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    transport = SequenceTransport([
        {"status": 200, "data": {"nodes": [{"id": "app-1"}], "edges": []}},
        {"transport_status": 500, "status": 500, "message": "server error"},
        {"status": 200, "data": [_candidate_row()]},
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

    run_path = tmp_path / "runs" / receipt["run_id"]
    manifest = json.loads((run_path / "manifest.json").read_text())
    coverage = json.loads((run_path / "coverage.json").read_text())
    topology = json.loads((run_path / "evidence" / "topology.json").read_text())
    performance = json.loads((run_path / "evidence" / "performance.json").read_text())
    candidates = json.loads((run_path / "evidence" / "candidates.json").read_text())

    assert receipt["status"] == "PARTIAL"
    assert manifest["overall"] == "PARTIAL"
    assert manifest["live_request_count"] == 3
    assert topology["status"] == "SUCCESS"
    assert performance["status"] == "FAILED"
    assert performance["derived_from"] == ["raw/response-0002.json"]
    assert performance["error"]["reason_code"] == "UPSTREAM_HTTP_ERROR"
    assert candidates["status"] == "SUCCESS"
    assert candidates["derived_from"] == ["raw/response-0003.json"]
    assert coverage["artifacts"]["performance"]["status"] == "FAILED"
    assert coverage["artifacts"]["performance"]["steps"][0]["attempt_count"] == 1


def test_successful_empty_data_is_empty_but_business_failure_is_failed(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    transport = SequenceTransport([
        {"status": 200, "data": {"nodes": [], "edges": []}},
        {"status": 200, "success": False, "code": "INTERNAL", "message": "business failure", "data": {}},
        {"status": 200, "data": []},
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

    run_path = tmp_path / "runs" / receipt["run_id"]
    topology = json.loads((run_path / "evidence" / "topology.json").read_text())
    performance = json.loads((run_path / "evidence" / "performance.json").read_text())
    candidates = json.loads((run_path / "evidence" / "candidates.json").read_text())

    assert topology["status"] == "EMPTY"
    assert performance["status"] == "FAILED"
    assert candidates["status"] == "EMPTY"
    assert receipt["status"] == "PARTIAL"


def test_transient_retry_uses_final_response_in_derived_from(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    transport = SequenceTransport([
        TimeoutError("read timeout"),
        {"status": 200, "data": {"nodes": [{"id": "app-1"}], "edges": []}},
        {"status": 200, "data": {"avg": [1]}},
        {"status": 200, "data": [_candidate_row()]},
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

    run_path = tmp_path / "runs" / receipt["run_id"]
    topology = json.loads((run_path / "evidence" / "topology.json").read_text())
    coverage = json.loads((run_path / "coverage.json").read_text())

    assert receipt["status"] == "SUCCESS"
    assert topology["derived_from"] == ["raw/response-0002.json"]
    assert (run_path / "raw" / "error-0001.json").exists()
    assert (run_path / "raw" / "response-0002.json").exists()
    assert coverage["artifacts"]["topology"]["steps"][0]["attempt_count"] == 2
    assert coverage["artifacts"]["topology"]["steps"][0]["transient_retried"] is True


def test_collect_preserves_final_failure_after_two_transient_errors(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    transport = SequenceTransport([
        TimeoutError("first timeout"),
        TimeoutError("second timeout"),
        {"status": 200, "data": {"avg": [1]}},
        {"status": 200, "data": [_candidate_row()]},
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

    run_path = tmp_path / "runs" / receipt["run_id"]
    topology = json.loads((run_path / "evidence" / "topology.json").read_text())

    assert receipt["status"] == "PARTIAL"
    assert topology["status"] == "FAILED"
    assert topology["derived_from"] == ["raw/error-0002.json"]
    assert (run_path / "raw" / "request-0001.json").exists()
    assert (run_path / "raw" / "request-0002.json").exists()
    assert (run_path / "raw" / "error-0002.json").exists()


def test_auth_recovery_is_run_scoped_and_provenance_uses_replay_response(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    transport = SequenceTransport([
        {"transport_status": 401, "status": 401, "message": "AUTH_EXPIRED"},
        {"status": 200, "data": {"nodes": [{"id": "app-1"}], "edges": []}},
        {"transport_status": 401, "status": 401, "message": "AUTH_EXPIRED"},
        {"status": 200, "data": [_candidate_row()]},
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

    run_path = tmp_path / "runs" / receipt["run_id"]
    topology = json.loads((run_path / "evidence" / "topology.json").read_text())
    performance = json.loads((run_path / "evidence" / "performance.json").read_text())
    coverage = json.loads((run_path / "coverage.json").read_text())

    assert transport.recoveries == 1
    assert receipt["status"] == "PARTIAL"
    assert topology["status"] == "SUCCESS"
    assert topology["derived_from"] == ["raw/response-0002.json"]
    assert performance["status"] == "FAILED"
    assert performance["derived_from"] == ["raw/response-0003.json"]
    assert coverage["artifacts"]["topology"]["steps"][0]["auth_recovered"] is True
    assert coverage["artifacts"]["performance"]["steps"][0]["auth_recovered"] is False


def test_candidate_actions_and_links_require_complete_trace_identity():
    artifact = normalize_candidates(
        response={
            "status": 200,
            "data": [
                _candidate_row(),
                _candidate_row(applicationId=None),
                _candidate_row(actionId=None),
                _candidate_row(requestType=None),
            ],
        },
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0001.json",
    )

    complete, missing_app, missing_action, missing_type = artifact["data"]["items"]
    assert complete["available_actions"] == ["investigate_trace"]
    assert complete["links"] == [{
        "rel": "detail",
        "url": "/web/server/action/overview/biz-1/app-1/action-1",
        "verification": "DERIVED_FROM_VERIFIED_ROUTE",
        "route_id": "web_server_action_overview",
    }]
    assert "navigation" in complete
    assert "available_actions" not in missing_app
    assert "links" not in missing_app
    assert "available_actions" not in missing_action
    assert "available_actions" not in missing_type


def test_inspect_rejects_supported_metric_unavailable_for_all_rows(tmp_path):
    artifact = normalize_candidates(
        response={"status": 200, "data": [_candidate_row(responseP99=None), _candidate_row(responseP99=None)]},
        source_run_id="run-candidates",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0001.json",
    )
    run_path = tmp_path / "runs" / "run-candidates"
    (run_path / "evidence").mkdir(parents=True)
    (run_path / "evidence" / "candidates.json").write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(ValueError, match="unavailable metric: p99"):
        inspect_candidates_top(run_path, metric="p99", limit=1)

    with pytest.raises(ValueError, match="unavailable metric: p99"):
        inspect_candidates_filter(run_path, metric="p99", operator=">", value=1)


def test_cli_inspect_metric_unavailable_returns_machine_readable_local_error(tmp_path):
    artifact = normalize_candidates(
        response={"status": 200, "data": [_candidate_row(responseP99=None)]},
        source_run_id="run-candidates",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0001.json",
    )
    run_path = tmp_path / "runs" / "run-candidates"
    (run_path / "evidence").mkdir(parents=True)
    (run_path / "evidence" / "candidates.json").write_text(json.dumps(artifact), encoding="utf-8")

    out = StringIO()
    with redirect_stdout(out):
        code = main([
            "--data-root",
            str(tmp_path),
            "inspect",
            "candidates",
            "top",
            "--run-id",
            "run-candidates",
            "--metric",
            "p99",
        ])

    payload = json.loads(out.getvalue())
    assert code == 0
    assert payload == {
        "schema_version": 1,
        "command": "inspect",
        "status": "LOCAL_ERROR",
        "reason_code": "UNAVAILABLE_METRIC",
        "message": "unavailable metric: p99",
    }


def test_investigate_rechecks_malformed_trace_action_identity_before_http(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_source_item_run(
        store,
        item={
            "item_ref": "item-0001",
            "source_run_id": "run-source",
            "kind": "candidate",
            "name": "GET /malformed",
            "wire_identity": {"bizSystemId": "biz-1", "actionId": "action-1"},
            "available_actions": ["investigate_trace"],
        },
    )
    transport = NoopTransport()

    receipt = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        action="investigate_trace",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    preflight = json.loads((run_path / "preflight.json").read_text())
    manifest = json.loads((run_path / "manifest.json").read_text())

    assert receipt["status"] == "BLOCKED"
    assert receipt["reason_code"] == "ACTION_IDENTITY_INCOMPLETE"
    assert manifest["live_request_count"] == 0
    assert preflight["requested_intent"] == {
        "source_run_id": source_run_id,
        "source_item_ref": "item-0001",
        "action": "investigate_trace",
    }
    assert transport.requests == []


def test_investigate_rechecks_malformed_call_tree_identity_before_http(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_source_item_run(
        store,
        run_type="INVESTIGATION",
        item={
            "item_ref": "item-0001",
            "source_run_id": "run-source",
            "kind": "trace",
            "wire_identity": {"bizSystemId": "biz-1", "traceId": "trace-1"},
            "available_actions": ["inspect_call_tree"],
        },
    )
    transport = NoopTransport()

    receipt = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        action="inspect_call_tree",
        transport=transport,
        clock=FakeClock(),
    )

    assert receipt["status"] == "BLOCKED"
    assert receipt["reason_code"] == "ACTION_IDENTITY_INCOMPLETE"
    assert transport.requests == []


def test_trace_evidence_exposes_verified_domains_without_claiming_independent_stack_endpoint(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_source_item_run(
        store,
        item={
            "item_ref": "item-0001",
            "source_run_id": "run-source",
            "kind": "candidate",
            "name": "GET /slow",
            "wire_identity": {
                "bizSystemId": "biz-1",
                "applicationId": "app-1",
                "actionId": "action-1",
                "requestType": "WEB",
            },
            "available_actions": ["investigate_trace"],
        },
    )
    trace_response = {
        "status": 200,
        "data": {
            "actionGuid": "action-guid-1",
            "actionId": "action-1",
            "actionName": "GET /slow",
            "actionType": "WEB",
            "applicationId": "app-1",
            "applicationName": "app",
            "bizSystemId": "biz-1",
            "bizSystemName": "billing",
            "duration": 123.4,
            "instanceId": "instance-1",
            "instanceName": "node-1",
            "data": {"id": "trace-1", "beginTime": "2026-07-07 12:00:00"},
            "timeLine": {"metricName": "Controller", "subTimeLines": [{"errors": [{"stack": ["frame-a"]}]}]},
            "topology": {"nodes": [{"id": "n1"}], "lines": []},
            "serviceFlow": {"nodes": [{"id": "svc"}]},
            "requestServiceFlow": {"nodes": [{"id": "req"}]},
            "exceptions": [{"message": "HTTP 500", "stack": ["frame-b"]}],
        },
    }

    receipt = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        action="investigate_trace",
        transport=SequenceTransport([trace_response]),
        clock=FakeClock(),
    )

    trace = json.loads((tmp_path / "runs" / receipt["run_id"] / "evidence" / "trace.json").read_text())
    item = trace["data"]["items"][0]

    assert receipt["status"] == "SUCCESS"
    assert trace["data"]["summary"]["duration"] == 123.4
    assert trace["data"]["timeline"]["metricName"] == "Controller"
    assert trace["data"]["trace_topology"]["nodes"] == [{"id": "n1"}]
    assert trace["data"]["service_flow"]["nodes"] == [{"id": "svc"}]
    assert trace["data"]["request_service_flow"]["nodes"] == [{"id": "req"}]
    assert trace["data"]["exceptions"][0]["message"] == "HTTP 500"
    assert trace["data"]["embedded_stack"]["source"] == "trace_detail_embedded"
    assert trace["data"]["context"]["applicationName"] == "app"
    assert item["wire_identity"]["actionGuid"] == "action-guid-1"
    assert item["wire_identity"]["traceId"] == "trace-1"
    assert item["source_refs"] == ["raw/response-0001.json"]
    assert item["available_actions"] == ["inspect_call_tree"]
    assert "stackTraces" not in json.dumps(trace)


def test_stale_inflight_counts_raw_requests_and_preserves_safe_preflight_intent(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="investigate", run_type="INVESTIGATION", pid=99999999)
    preflight = {
        "schema_version": 1,
        "command": "investigate",
        "source": {"run_id": "run-source", "item_ref": "item-0001"},
        "action": "inspect_call_tree",
        "time_context": {"requested": {"kind": "relative", "value": "last_30m"}},
    }
    store.write_json(run.path / "preflight.json", preflight)
    store.write_json(run.path / "raw" / "request-0001.json", {"request_id": "request-0001"})
    store.write_json(run.path / "raw" / "response-0001.json", {"request_id": "request-0001", "response": {"status": 200}})
    store.write_json(run.path / "raw" / "request-0002.json", {"request_id": "request-0002"})
    store.write_json(run.path / "raw" / "error-0002.json", {"request_id": "request-0002", "error_type": "TimeoutError"})

    interrupted = store.freeze_stale_inflight()

    run_path = tmp_path / "runs" / run.run_id
    manifest = json.loads((run_path / "manifest.json").read_text())

    assert interrupted == [run.run_id]
    assert manifest["overall"] == "INTERRUPTED"
    assert manifest["live_request_count"] == 2
    assert manifest["raw_summary"] == {"request_count": 2, "response_count": 1, "error_count": 1}
    assert manifest["source"] == {"run_id": "run-source", "item_ref": "item-0001"}
    assert manifest["action"] == "inspect_call_tree"
    assert manifest["time_context"] == preflight["time_context"]
    assert (run_path / "raw" / "request-0002.json").exists()


def test_blocked_runs_preserve_safe_rejected_intent(tmp_path):
    store = RunStore(tmp_path)
    receipt = run_collect(
        store=store,
        config=_config(tmp_path),
        source_run_id="missing-run",
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=NoopTransport(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    preflight = json.loads((run_path / "preflight.json").read_text())
    manifest = json.loads((run_path / "manifest.json").read_text())

    assert receipt["status"] == "BLOCKED"
    assert preflight["requested_intent"] == {
        "source_run_id": "missing-run",
        "source_item_ref": "item-0001",
        "time_context": "last_30m",
    }
    assert manifest["requested_intent"] == preflight["requested_intent"]
    assert manifest["live_request_count"] == 0
    assert not (run_path / "evidence").exists()


def test_sanitized_export_removes_new_links_attempt_metadata_and_ids(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="collect", run_type="COLLECT")
    store.write_json(run.path / "manifest.json", {
        "schema_version": 1,
        "run_id": run.run_id,
        "overall": "SUCCESS",
        "raw_summary": {"request_count": 1, "response_count": 1, "error_count": 0},
        "local_path": str(tmp_path / "internal"),
    })
    store.write_json(run.path / "evidence" / "candidates.json", {
        "data": {
            "items": [{
                "item_ref": "item-0001",
                "wire_identity": {"bizSystemId": "biz-1", "applicationId": "app-1", "actionId": "action-1"},
                "available_actions": ["investigate_trace"],
                "links": [{
                    "rel": "detail",
                    "url": "/web/server/action/overview/biz-1/app-1/action-1",
                    "verification": "DERIVED_FROM_VERIFIED_ROUTE",
                }],
                "attempt_refs": ["raw/request-0001.json", "raw/response-0001.json"],
                "error": {"message": "Authorization failed"},
            }]
        }
    })
    store.finalize_existing_inflight(run)

    output_dir = tmp_path / "exports" / "safe"
    result = export_sanitized_run(store, run.run_id, output_dir)
    text = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.rglob("*.json"))

    assert result["status"] == "SUCCESS"
    assert "available_actions" not in text
    assert "wire_identity" not in text
    assert "links" not in text
    assert "/web/server/action/overview" not in text
    assert "biz-1" not in text
    assert "app-1" not in text
    assert "action-1" not in text
    assert "Authorization" not in text
    assert str(tmp_path) not in text
