import json
import os
from contextlib import redirect_stdout
from io import StringIO

import pytest

from tingyun_cli import candidates
from tingyun_cli.cli import main
from tingyun_cli.commands import (
    export_sanitized_run,
    plan_collect,
    run_collect,
    run_discover,
    run_investigate,
)
from tingyun_cli.config import Config
from tingyun_cli.safety import assert_read_endpoint
from tingyun_cli.storage import RunStore


class FakeTransport:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("unexpected HTTP call")
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


def _config(tmp_path):
    return Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0)


def _write_discovery_run(store, *, kind="business_system_candidate", wire_identity=None):
    run = store.begin_run(command="discover", run_type="DISCOVERY")
    item = {
        "item_ref": "item-0001",
        "kind": kind,
        "display_name": "synthetic business",
        "wire_identity": wire_identity or {"bizSystemId": "biz-1"},
    }
    store.write_json(run.path / "evidence" / "targets.json", {
        "schema_version": 1,
        "kind": "targets",
        "status": "SUCCESS",
        "data": {"items": [item]},
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


def _write_candidate_run(store, *, request_type="WEB", available_actions=None):
    run = store.begin_run(command="collect", run_type="COLLECT")
    item = {
        "item_ref": "item-0001",
        "kind": "candidate",
        "source_run_id": run.run_id,
        "wire_identity": {
            "bizSystemId": "biz-1",
            "applicationId": "app-1",
            "actionId": "action-1",
            "requestType": request_type,
        },
    }
    if available_actions is not None:
        item["available_actions"] = available_actions
    elif candidates.is_investigate_trace_eligible(item):
        item["available_actions"] = ["investigate_trace"]
    store.write_json(run.path / "evidence" / "candidates.json", {
        "schema_version": 1,
        "kind": "candidates",
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
            "time_context": {
                "requested": {"kind": "relative", "value": "last_30m"},
                "endpoint": {"timePeriod": 30, "endTime": "2026-07-07 12:00"},
            },
            "artifacts": [{"kind": "candidates", "path": "evidence/candidates.json", "status": "SUCCESS"}],
            "coverage_ref": "coverage.json",
            "live_request_count": 3,
        },
        coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {}},
    )
    return run.run_id


def _candidate_row(request_type):
    return {
        "applicationId": "app-1",
        "applicationName": "Synthetic App",
        "actionId": "action-1",
        "actionName": "GET /synthetic",
        "requestType": request_type,
        "responseP99": 250,
        "errorRate": 5,
    }


def _snapshot_tree(root):
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


def test_shared_trace_resolver_uses_exact_verified_mappings_only():
    resolver = candidates.resolve_verified_trace_action_type

    assert resolver("WEB") == "WEB"
    assert resolver("TX") == "TX"
    assert resolver("BG") == "BG"
    assert resolver("TX,IF") == "TX"
    assert resolver("IF,TX") is None
    assert resolver("BG,IF") is None
    assert resolver("TX,BG") is None
    assert resolver("ZZ,TX") is None
    assert resolver("") is None


def test_candidate_trace_eligibility_and_execution_use_same_resolver(tmp_path):
    artifact = candidates.normalize_candidates(
        response={"status": 200, "data": [_candidate_row("TX,IF"), _candidate_row("IF,TX")]},
        source_run_id="run-collect",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )
    tx_if, if_tx = artifact["data"]["items"]

    assert tx_if["available_actions"] == ["investigate_trace"]
    assert tx_if["navigation"] == {"status": "MISSING", "reason": "URL_NOT_VERIFIED"}
    assert "links" not in tx_if
    assert "available_actions" not in if_tx

    store = RunStore(tmp_path)
    source_run_id = _write_candidate_run(store, request_type="TX,IF")
    transport = FakeTransport([{"status": 200, "data": {"actionGuid": "ag-1", "data": {"id": "trace-1"}}}])

    receipt = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        action="investigate_trace",
        transport=transport,
        clock=FakeClock(),
    )

    assert receipt["status"] == "SUCCESS"
    assert transport.requests[0]["body"]["actionType"] == "TX"


def test_malformed_old_composite_action_is_blocked_before_http(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_candidate_run(
        store,
        request_type="BG,IF",
        available_actions=["investigate_trace"],
    )
    transport = FakeTransport()

    receipt = run_investigate(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        action="investigate_trace",
        transport=transport,
        clock=FakeClock(),
    )

    manifest = json.loads((tmp_path / "runs" / receipt["run_id"] / "manifest.json").read_text())
    assert receipt["status"] == "BLOCKED"
    assert receipt["reason_code"] == "ACTION_IDENTITY_INCOMPLETE"
    assert manifest["live_request_count"] == 0
    assert transport.requests == []


def test_trace_proof_does_not_create_unproven_navigation_urls():
    for request_type in ("BG", "TX,IF"):
        artifact = candidates.normalize_candidates(
            response={"status": 200, "data": [_candidate_row(request_type)]},
            source_run_id="run-collect",
            scope={"bizSystemId": "biz-1"},
            time_context={"requested": "last_30m"},
            raw_ref="raw/response-0003.json",
        )
        item = artifact["data"]["items"][0]

        assert item["available_actions"] == ["investigate_trace"]
        assert "links" not in item
        assert item["navigation"] == {"status": "MISSING", "reason": "URL_NOT_VERIFIED"}


def test_startup_freezes_stale_inflight_before_plan_only_dispatch(tmp_path):
    store = RunStore(tmp_path)
    stale = store.begin_run(command="collect", run_type="COLLECT", pid=99999999)
    store.write_json(stale.path / "raw" / "request-0001.json", {"request_id": "request-0001"})

    out = StringIO()
    with redirect_stdout(out):
        code = main([
            "--data-root",
            str(tmp_path),
            "collect",
            "--source-run-id",
            "missing",
            "--source-item-ref",
            "item-0001",
            "--time-context",
            "last_30m",
            "--plan-only",
        ])

    payload = json.loads(out.getvalue())
    assert code == 0
    assert payload["status"] == "BLOCKED"
    interrupted_manifest = json.loads((tmp_path / "runs" / stale.run_id / "manifest.json").read_text())
    assert interrupted_manifest["overall"] == "INTERRUPTED"
    assert interrupted_manifest["live_request_count"] == 1


def test_plan_only_invalid_inputs_are_machine_safe_and_have_zero_side_effects(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    wrong_kind_run_id = _write_discovery_run(store, kind="not_business_system")
    before = _snapshot_tree(tmp_path)

    invalid_source = plan_collect(store, "missing-run", "item-0001", "last_30m")
    invalid_item = plan_collect(store, source_run_id, "missing-item", "last_30m")
    wrong_kind = plan_collect(store, wrong_kind_run_id, "item-0001", "last_30m")
    invalid_time = plan_collect(store, source_run_id, "item-0001", "2026-07-06T13:00..2026-07-06T13:37:30")
    unsupported_time = plan_collect(store, source_run_id, "item-0001", "last_7d")

    after = _snapshot_tree(tmp_path)
    assert invalid_source["reason_code"] == "INVALID_SOURCE_REF"
    assert invalid_item["reason_code"] == "INVALID_SOURCE_REF"
    assert wrong_kind["reason_code"] == "INVALID_SOURCE_KIND"
    assert invalid_time["reason_code"] == "UNSUPPORTED_TIME_SHAPE"
    assert unsupported_time["reason_code"] == "UNSUPPORTED_TIME_SHAPE"
    assert all(result["status"] == "BLOCKED" for result in [invalid_source, invalid_item, wrong_kind, invalid_time, unsupported_time])
    assert before == after


def test_local_validation_happens_before_live_lock_busy(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    (tmp_path / "live.lock").write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")

    invalid_source = run_collect(
        store=store,
        config=_config(tmp_path),
        source_run_id="missing",
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=FakeTransport(),
    )
    invalid_time = run_collect(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_7d",
        transport=FakeTransport(),
    )
    valid_busy = run_collect(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=FakeTransport(),
    )

    assert invalid_source["reason_code"] == "INVALID_SOURCE_REF"
    assert invalid_time["reason_code"] == "UNSUPPORTED_TIME_SHAPE"
    assert valid_busy["reason_code"] == "LIVE_EXECUTION_BUSY"


def test_missing_auth_blocks_default_live_commands_before_http(tmp_path, monkeypatch):
    monkeypatch.delenv("TINGYUN_AUTHORIZATION", raising=False)
    config = _config(tmp_path)
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    candidate_run_id = _write_candidate_run(store, request_type="WEB")

    discover = run_discover(store=store, config=config, query="synthetic")
    collect = run_collect(
        store=store,
        config=config,
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
    )
    investigate = run_investigate(
        store=store,
        config=config,
        source_run_id=candidate_run_id,
        source_item_ref="item-0001",
        action="investigate_trace",
    )

    assert discover["reason_code"] == "AUTH_NOT_CONFIGURED"
    assert collect["reason_code"] == "AUTH_NOT_CONFIGURED"
    assert investigate["reason_code"] == "AUTH_NOT_CONFIGURED"
    for receipt in (discover, collect, investigate):
        manifest = json.loads((tmp_path / "runs" / receipt["run_id"] / "manifest.json").read_text())
        assert manifest["live_request_count"] == 0


def test_fake_transport_remains_auth_independent_for_offline_tests(tmp_path, monkeypatch):
    monkeypatch.delenv("TINGYUN_AUTHORIZATION", raising=False)
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    transport = FakeTransport([
        {"status": 200, "data": {"nodeDataArray": [{"id": "n1"}], "linkeDataArray": []}},
        {"status": 200, "data": {"series": [{"name": "响应时间", "data": [{"x": 1, "y": 20}]}]}},
        {"status": 200, "data": [_candidate_row("WEB")]},
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

    assert receipt["status"] == "SUCCESS"
    assert len(transport.requests) == 3


def test_preflight_uses_expected_logical_request_count_and_manifest_counts_attempts(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    transport = FakeTransport([
        TimeoutError("first attempt"),
        {"status": 200, "data": {"nodeDataArray": [{"id": "n1"}], "linkeDataArray": []}},
        {"status": 200, "data": {"series": [{"name": "响应时间", "data": [{"x": 1, "y": 20}]}]}},
        {"status": 200, "data": [_candidate_row("WEB")]},
    ])

    plan = plan_collect(store, source_run_id, "item-0001", "last_30m")
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
    preflight = json.loads((run_path / "preflight.json").read_text())
    manifest = json.loads((run_path / "manifest.json").read_text())

    assert plan["expected_logical_request_count"] == 3
    assert "expected_live_request_count" not in plan
    assert preflight["expected_logical_request_count"] == 3
    assert "expected_live_request_count" not in preflight
    assert manifest["live_request_count"] == 4


def test_response_list_is_not_in_production_runtime_safety_surface():
    with pytest.raises(ValueError, match="not in stable read surface"):
        assert_read_endpoint("POST", "/server-api/webaction/list/responseList")


def test_sanitized_export_uses_one_pseudonym_state_and_sanitizes_embedded_identities(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="collect", run_type="COLLECT")
    store.write_json(run.path / "manifest.json", {
        "schema_version": 1,
        "run_id": run.run_id,
        "overall": "SUCCESS",
        "source": {
            "display_name": "Synthetic Billing",
            "wire_identity": {"bizSystemId": "123", "applicationId": "456"},
        },
        "metric_number": 123,
        "local_path": str(tmp_path / "private-root" / "run"),
    })
    store.write_json(run.path / "evidence" / "candidates.json", {
        "data": {
            "items": [
                {
                    "item_ref": "item-0001",
                    "name": "Synthetic Other",
                    "labels": {
                        "display_name": "Synthetic Other",
                        "applicationName": "Synthetic App",
                        "aliases": ["123", "prefix-123-suffix", "safe-789"],
                    },
                    "wire_identity": {"bizSystemId": "123", "applicationId": "456", "actionId": "789"},
                    "internal_route": "/web/server/action/overview/123/456/789",
                    "metrics": {"total_count": {"value": 123, "unit": "count"}},
                    "available_actions": ["investigate_trace"],
                    "links": [{"url": "/web/server/action/overview/123/456/789"}],
                },
                {
                    "item_ref": "item-0002",
                    "display_name": "Synthetic Billing",
                    "labels": {"applicationName": "Synthetic App"},
                },
            ]
        }
    })
    store.write_json(run.path / "raw" / "request-0001.json", {"body": {"bizSystemId": "123"}})
    store.write_json(run.path / "raw" / "response-0001.json", {"response": {"data": {"bizSystemId": "123"}}})
    store.finalize_existing_inflight(run)

    output_dir = tmp_path / "exports" / "safe"
    export_sanitized_run(store, run.run_id, output_dir)

    exported_files = {str(path.relative_to(output_dir)): json.loads(path.read_text(encoding="utf-8")) for path in output_dir.rglob("*.json")}
    text = "\n".join(json.dumps(data, ensure_ascii=False, sort_keys=True) for data in exported_files.values())
    manifest = exported_files["manifest.json"]
    candidates_json = exported_files["evidence/candidates.json"]

    assert "raw/response-0001.json" not in exported_files
    assert '"123"' not in text
    assert '"456"' not in text
    assert '"789"' not in text
    assert "prefix-123-suffix" not in text
    assert "safe-789" not in text
    assert "Synthetic Billing" not in text
    assert "Synthetic App" not in text
    assert "/web/server/action/overview" not in text
    assert "available_actions" not in text
    assert str(tmp_path) not in text
    assert manifest["source"]["display_name"] == candidates_json["data"]["items"][1]["display_name"]
    aliases = candidates_json["data"]["items"][0]["labels"]["aliases"]
    assert aliases[0].startswith("ID_")
    assert aliases[0] in aliases[1]
    assert aliases[2].startswith("safe-ID_")
    assert aliases[2] != f"safe-{aliases[0]}"
    assert manifest["metric_number"] == 123
    assert candidates_json["data"]["items"][0]["metrics"]["total_count"]["value"] == 123
