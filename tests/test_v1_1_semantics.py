import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from tingyun_cli.candidates import candidate_semantic_kind, normalize_candidates, resolve_verified_trace_action_type
from tingyun_cli.cli import main
from tingyun_cli.evidence_adapter import adapt_evidence
from tingyun_cli.source_normalization import classify_exception_signal, normalize_source
from tingyun_cli.commands import run_investigate
from tingyun_cli.config import Config
from tingyun_cli.storage import RunStore


FIXTURES = Path(__file__).parent / "fixtures" / "v1_1"


def _fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_candidate_semantics_make_web_composite_eligible_and_dubbo_unresolved():
    artifact = normalize_candidates(
        response={"status": 200, "data": [_fixture("candidate_web_tx_if.json"), _fixture("candidate_dubbo_tx_if.json")]},
        source_run_id="run-collect-a",
        scope={"bizSystemId": "biz-001"},
        time_context={"requested": {"kind": "exact_range", "value": "synthetic"}},
        raw_ref="raw/response-0003.json",
    )
    web, dubbo = artifact["data"]["items"]

    assert web["semantic_kind"] == "WEB_TRANSACTION"
    assert web["labels"]["requestType"] == "TX,IF"
    assert web["wire_identity"]["requestType"] == "TX,IF"
    assert web["available_actions"] == ["investigate_trace"]
    assert resolve_verified_trace_action_type(web["semantic_kind"], "TX,IF") == "TX"

    assert dubbo["semantic_kind"] == "DUBBO_PROVIDER_INTERFACE"
    assert "available_actions" not in dubbo
    assert resolve_verified_trace_action_type(dubbo["semantic_kind"], "TX,IF") is None
    assert dubbo["action_resolution"]["reason_code"] == "UNRESOLVED_TRACE_ACTION_TYPE"


def test_candidate_semantics_do_not_promote_unproven_http_or_blank_names():
    assert candidate_semantic_kind("GET /synthetic", "WEB") == "UNKNOWN"
    assert candidate_semantic_kind("", "TX") == "UNKNOWN"
    with pytest.raises(TypeError):
        resolve_verified_trace_action_type("TX")


def test_external_text_value_normalization_is_nonempty_and_deterministic():
    items, _ = normalize_source(
        "external_calls",
        _fixture("external_text_value.json"),
        {"capability": "list_external_calls", "business_system_id": "biz-001", "application_id": "app-001"},
        run_id="run-source-001",
        raw_ref="raw/response-0001.json",
    )

    assert items[0]["name"] == "/synthetic/dependency/path"
    assert items[0]["dependency_uri"] == "/synthetic/dependency/path"
    assert items[1]["name"] == "explicit-name"
    assert items[1]["dependency_uri"] == "https://public.example/api"


@pytest.mark.parametrize(
    ("fixture", "ranking", "metric", "wire_field", "value"),
    [
        ("recent_response_ranking.json", "response", "ranking_response", "response", 987.5),
        ("recent_error_ranking.json", "error", "ranking_error", "error", 17),
        ("recent_throughput_ranking.json", "throughput", "ranking_throughput", "throught", 321.25),
    ],
)
def test_recent_ranking_metrics_preserve_value_and_wire_field(fixture, ranking, metric, wire_field, value):
    items, _ = normalize_source(
        "recent_requests",
        _fixture(fixture),
        {"capability": "list_recent_requests", "ranking": ranking, "business_system_id": "biz-001"},
        run_id="run-source-001",
        raw_ref="raw/response-0001.json",
    )

    ranking_metric = items[0]["metrics"][metric]
    assert ranking_metric == {
        "value": value,
        "unit": "UNKNOWN",
        "semantic_status": "UNKNOWN",
        "wire_field": wire_field,
    }
    assert items[0]["selection_provenance"]["ranking_value"] == value
    assert items[0]["selection_provenance"]["wire_field"] == wire_field


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"exceptionClass": "SyntheticError", "stack": ["frame"]}, "THROWN_EXCEPTION"),
        ({"type": "Logged Error Message", "message": "synthetic"}, "LOGGED_ERROR_EVENT"),
        ({"type": "Logged Error Message", "message": "synthetic", "error": False}, "ERROR_FLAG_FALSE_LOG_EVENT"),
        ({"message": "unclassified"}, "UNKNOWN_EXCEPTION_SIGNAL"),
    ],
)
def test_exception_signal_classification_is_conservative(row, expected):
    assert classify_exception_signal(row) == expected


def test_depth_adapter_consumes_performance_candidate_trace_and_call_tree_envelopes():
    performance = {
        "kind": "performance",
        "derived_from": ["raw/response-0002.json"],
        "data": {"metrics": {"p95": {"semantic": "response_time", "unit": "ms", "series": [{"timestamp": 1000, "value": 10}, {"timestamp": 2000, "value": 30}]}}},
    }
    candidate = {"kind": "candidates", "data": {"items": [{"item_ref": "item-0001", "name": "SpringController/example"}]}}
    trace = {"kind": "trace", "data": {"exceptions": [{"message": "synthetic", "error": False}]}}
    call_tree = {"kind": "call_tree", "data": {"call_tree": _fixture("deep_call_tree/call_tree.json")}}

    windows = adapt_evidence(performance, "performance_windows")
    assert windows[1]["reported_max_metric"] == 30
    assert windows[0]["source_refs"] == ["raw/response-0002.json"]
    assert adapt_evidence(candidate, "candidate_items")[0]["item_ref"] == "item-0001"
    assert adapt_evidence(trace, "error_events")[0]["signal_type"] == "ERROR_FLAG_FALSE_LOG_EVENT"
    assert adapt_evidence(call_tree, "call_tree")["nodeMap"]["node-sql"]["sql"].startswith("select synthetic")


def test_depth_cli_adapts_envelopes_for_four_existing_primitives(tmp_path):
    performance_path = tmp_path / "performance.json"
    trace_path = tmp_path / "trace.json"
    tree_path = tmp_path / "call-tree.json"
    performance_path.write_text(json.dumps({"kind": "performance", "derived_from": ["raw/response.json"], "data": {"metrics": {"p95": {"series": [{"timestamp": 1000, "value": 10}, {"timestamp": 2000, "value": 30}]}}}}), encoding="utf-8")
    trace_path.write_text(json.dumps({"kind": "trace", "data": {"exceptions": [{"type": "Logged Error Message", "message": "synthetic", "error": False}]}}), encoding="utf-8")
    tree_path.write_text(json.dumps({"kind": "call_tree", "data": {"call_tree": _fixture("deep_call_tree/call_tree.json")}}), encoding="utf-8")

    commands = [
        ["depth", "locate-peak", "--input", str(performance_path), "--metric-semantic-status", "VERIFIED"],
        ["depth", "narrow-window", "--input", str(performance_path), "--signal", "p95", "--min-window-minutes", "1", "--max-steps", "2", "--request-budget", "2"],
        ["depth", "cluster-errors", "--input", str(trace_path)],
        ["depth", "diff-call-trees", "--baseline", str(tree_path), "--abnormal", str(tree_path)],
    ]
    payloads = []
    for command in commands:
        output = StringIO()
        with redirect_stdout(output):
            assert main(command) == 0
        payloads.append(json.loads(output.getvalue()))

    assert payloads[0]["result"]["peak_window"] == {"from": 2000, "to": 62000}
    assert payloads[1]["result"]["steps"][0]["source_refs"] == ["raw/response.json"]
    assert payloads[2]["clusters"][0]["representative"]["signal_type"] == "ERROR_FLAG_FALSE_LOG_EVENT"
    assert "SpringController/example/root" in payloads[3]["diff"]["common_path"]


def test_unresolved_dubbo_trace_action_returns_specific_zero_http_reason(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="collect", run_type="COLLECT")
    artifact = normalize_candidates(
        response={"data": [_fixture("candidate_dubbo_tx_if.json")]},
        source_run_id=run.run_id,
        scope={"bizSystemId": "biz-001"},
        time_context={"requested": {"kind": "exact_range", "value": "synthetic"}},
        raw_ref="raw/response-0001.json",
    )
    store.write_json(run.path / "evidence" / "candidates.json", artifact)
    store.finalize_run(run, manifest={"schema_version": 1, "run_id": run.run_id, "run_type": "COLLECT", "overall": "SUCCESS", "artifacts": [{"kind": "candidates", "path": "evidence/candidates.json", "status": "SUCCESS"}], "coverage_ref": "coverage.json", "live_request_count": 1}, coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {}})

    class NoHttp:
        requests = []

        def send(self, request):
            self.requests.append(request)
            raise AssertionError("HTTP must not be called")

    transport = NoHttp()
    receipt = run_investigate(
        store=store,
        config=Config(base_url="https://example.invalid", data_root=tmp_path, min_request_interval_seconds=0),
        source_run_id=run.run_id,
        source_item_ref="item-0001",
        action="investigate_trace",
        transport=transport,
    )

    assert receipt["status"] == "BLOCKED"
    assert receipt["reason_code"] == "UNRESOLVED_TRACE_ACTION_TYPE"
    manifest = json.loads(Path(receipt["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["live_request_count"] == 0
    assert transport.requests == []
