import json

from tingyun_cli.commands import (
    plan_collect,
    run_collect,
    run_investigate,
)
from tingyun_cli.config import Config
from tingyun_cli.storage import RunStore


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class FakeClock:
    def __init__(self):
        self.now = 1_783_430_000.0
        self.sleeps = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def _write_discovery_run(store):
    run = store.begin_run(command="discover", run_type="DISCOVERY")
    target = {
        "item_ref": "item-0001",
        "kind": "business_system_candidate",
        "display_name": "redacted business system",
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


def _config(tmp_path):
    return Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0)


def test_plan_collect_resolves_source_without_writing_new_run(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))

    plan = plan_collect(store, source_run_id, "item-0001", "last_30m")

    after = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    assert before == after
    assert plan["status"] == "READY"
    assert plan["expected_logical_request_count"] == 3
    assert plan["source"]["item_ref"] == "item-0001"


def test_collect_creates_core_evidence_run_with_request_overview_candidates(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    transport = FakeTransport([
        {"status": 200, "data": {"nodes": [{"id": "app-1"}], "edges": [{"response": 12, "throught": 2, "error": 0}]}},
        {"status": 200, "data": {"avg": [10], "p50": [8], "p80": [12], "p95": [20], "p99": [30]}},
        {"status": 200, "data": [{
            "applicationId": 1,
            "actionId": 2,
            "actionName": "GET /slow",
            "applicationName": "app",
            "requestType": "WEB",
            "responseTimeMillisecondAvg": 100,
            "responseP99": 300,
            "throughput": 4,
            "totalCount": 5,
            "errorRate": 0.2,
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

    run_path = tmp_path / "runs" / receipt["run_id"]
    assert receipt["status"] == "SUCCESS"
    assert json.loads((run_path / "manifest.json").read_text())["overall"] == "SUCCESS"
    assert (run_path / "raw" / "request-0001.json").exists()
    assert (run_path / "raw" / "response-0003.json").exists()
    candidates = json.loads((run_path / "evidence" / "candidates.json").read_text())
    assert candidates["data"]["items"][0]["available_actions"] == ["investigate_trace"]
    assert transport.requests[2]["path"] == "/server-api/graph/query/overview"
    assert transport.requests[2]["query"] == {"request_overview": "", "lang": "zh_CN"}
    assert transport.requests[2]["body"]["metric"] == "request_overview"
    assert transport.requests[2]["body"]["labels"] == {"systemIds": ["biz-1"]}


def test_investigate_trace_then_call_tree_are_separate_child_runs(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    collect_transport = FakeTransport([
        {"status": 200, "data": {"nodes": [], "edges": []}},
        {"status": 200, "data": {}},
        {"status": 200, "data": [{
            "applicationId": 1,
            "actionId": 2,
            "actionName": "GET /slow",
            "applicationName": "app",
            "requestType": "WEB",
            "responseP99": 300,
        }]},
    ])
    collect_receipt = run_collect(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=collect_transport,
        clock=FakeClock(),
    )

    trace_receipt = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=collect_receipt["run_id"],
        source_item_ref="item-0001",
        action="investigate_trace",
        transport=FakeTransport([{"status": 200, "data": {"actionGuid": "ag-1", "data": {"id": "trace-1"}}}]),
        clock=FakeClock(),
    )
    trace_run = tmp_path / "runs" / trace_receipt["run_id"]
    trace = json.loads((trace_run / "evidence" / "trace.json").read_text())
    assert trace["data"]["items"][0]["available_actions"] == ["inspect_call_tree"]
    assert json.loads((trace_run / "manifest.json").read_text())["source"] == {
        "run_id": collect_receipt["run_id"],
        "item_ref": "item-0001",
    }

    call_tree_receipt = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=trace_receipt["run_id"],
        source_item_ref="item-0001",
        action="inspect_call_tree",
        transport=FakeTransport([{"status": 200, "data": {"nodes": [{"id": "root"}]}}]),
        clock=FakeClock(),
    )
    call_tree_run = tmp_path / "runs" / call_tree_receipt["run_id"]
    assert (call_tree_run / "evidence" / "call_tree.json").exists()
    assert not (call_tree_run / "evidence" / "stack.json").exists()
