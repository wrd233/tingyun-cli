import json
from contextlib import redirect_stdout
from io import StringIO

from tingyun_cli.cli import main
from tingyun_cli.storage import RunStore


def _run_cli(args):
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(args)
    return code, json.loads(stdout.getvalue())


def test_depth_promotion_matrix_cli_returns_qualified_json():
    code, output = _run_cli(["depth", "promotion-matrix"])

    assert code == 0
    assert output["schema_version"] == 1
    assert output["command"] == "depth promotion-matrix"
    assert output["capabilities"]["read_error_timeseries"]["runtime_status"] == "ADVANCED_READ_ONLY"


def test_depth_select_trace_cli_uses_explicit_strategy_and_provenance(tmp_path):
    candidates_path = tmp_path / "trace-candidates.json"
    candidates_path.write_text(json.dumps({
        "data": {
            "items": [
                {"trace_id": "normal", "duration_ms": {"value": 120}, "error": False},
                {"trace_id": "slow", "duration_ms": {"value": 129000}, "error": False},
            ]
        }
    }), encoding="utf-8")

    code, output = _run_cli(["depth", "select-trace", "--input", str(candidates_path), "--strategy", "slowest"])

    assert code == 0
    assert output["command"] == "depth select-trace"
    assert output["selected"]["trace_id"] == "slow"
    assert output["selected"]["selection"]["strategy"] == "slowest"


def test_depth_narrow_and_triage_cli_are_local_json_views(tmp_path):
    windows_path = tmp_path / "windows.json"
    windows_path.write_text(json.dumps([
        {"from": 0, "to": 105, "error_count": 12, "request_count": 240},
        {"from": 55, "to": 65, "error_count": 8, "request_count": 18},
    ]), encoding="utf-8")

    _, narrowed = _run_cli([
        "depth",
        "narrow-window",
        "--input",
        str(windows_path),
        "--signal",
        "error_rate",
        "--min-window-minutes",
        "10",
        "--max-steps",
        "3",
        "--request-budget",
        "3",
    ])
    _, triage = _run_cli(["depth", "triage-path", "--path", "/favicon.ico"])

    assert narrowed["result"]["recommended_window"] == {"from": 55, "to": 65}
    assert triage["classification"]["class"] == "static_resource"


def test_depth_trace_candidates_locate_peak_and_cluster_errors_cli(tmp_path):
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps([
        {"traceId": "trace-a", "duration_ms": 120, "actionId": 13172},
        {"traceId": "trace-b", "duration_ms": 129000, "actionId": 13172, "error": True},
    ]), encoding="utf-8")
    windows = tmp_path / "peak-windows.json"
    windows.write_text(json.dumps([{"from": 0, "to": 10, "reported_max_metric": 498419}]), encoding="utf-8")
    errors = tmp_path / "errors.json"
    errors.write_text(json.dumps([
        {"trace_id": "a", "http_status": 404, "message": "Not found TodoListItem ,todoId=1", "action_id": 13198},
        {"trace_id": "b", "http_status": 404, "message": "Not found TodoListItem ,todoId=2", "action_id": 13198},
    ]), encoding="utf-8")

    _, candidates = _run_cli([
        "depth",
        "trace-candidates",
        "--input",
        str(rows),
        "--scope",
        '{"type":"transaction","business_system_id":1061,"application_id":1626,"action_id":13172}',
        "--source",
        '{"capability":"list_recent_requests","ranking_type":"response"}',
        "--time-window",
        '{"from":"2026-07-08T00:00:00Z","to":"2026-07-08T01:00:00Z"}',
    ])
    _, peak = _run_cli(["depth", "locate-peak", "--input", str(windows), "--metric-semantic-status", "UNKNOWN"])
    _, clusters = _run_cli(["depth", "cluster-errors", "--input", str(errors)])

    assert candidates["candidate_count"] == 2
    assert candidates["items"][1]["duration_ms"]["value"] == 129000
    assert peak["result"]["status"] == "UNRESOLVED"
    assert clusters["clusters"][0]["count"] == 2


def test_depth_compare_and_diff_cli_emit_deterministic_json(tmp_path):
    before = tmp_path / "before.json"
    incident = tmp_path / "incident.json"
    before.write_text(json.dumps({"scope": {"type": "transaction"}, "metrics": {"p99_ms": 100}}), encoding="utf-8")
    incident.write_text(json.dumps({"scope": {"type": "transaction"}, "metrics": {"p99_ms": 250}}), encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    abnormal = tmp_path / "abnormal.json"
    baseline.write_text(json.dumps({"name": "root", "duration_ms": 10, "children": []}), encoding="utf-8")
    abnormal.write_text(json.dumps({"name": "root", "duration_ms": 100, "children": [{"name": "external", "duration_ms": 90}]}), encoding="utf-8")

    _, compared = _run_cli(["depth", "compare-windows", "--before", str(before), "--incident", str(incident)])
    _, diffed = _run_cli(["depth", "diff-call-trees", "--baseline", str(baseline), "--abnormal", str(abnormal)])

    assert compared["comparison"]["metrics"]["p99_ms"]["delta"] == 150
    assert diffed["diff"]["abnormal_only"][0]["name"] == "external"


def test_depth_analyze_external_cli_flags_duration_cluster(tmp_path):
    rows = tmp_path / "external.json"
    rows.write_text(json.dumps([
        {"dependency": "file-open.tianyancha.com", "duration_ms": 128400, "action_id": 13172, "trace_id": "a"},
        {"dependency": "file-open.tianyancha.com", "duration_ms": 129401, "action_id": 13172, "trace_id": "b"},
        {"dependency": "file-open.tianyancha.com", "duration_ms": 131020, "action_id": 13172, "trace_id": "c"},
    ]), encoding="utf-8")

    code, output = _run_cli(["depth", "analyze-external", "--input", str(rows)])

    assert code == 0
    assert output["command"] == "depth analyze-external"
    assert output["analysis"]["dependencies"][0]["fixed_timeout_signature_candidate"] is True


def test_depth_workflow_plan_cli_returns_bounded_plan(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(json.dumps({
        "item_ref": "item-0001",
        "scope": {"type": "transaction", "business_system_id": 1061, "application_id": 1626, "action_id": 13172},
    }), encoding="utf-8")

    code, output = _run_cli([
        "depth",
        "workflow-plan",
        "--workflow",
        "slow_transaction",
        "--source",
        str(source),
        "--max-live-requests",
        "20",
    ])

    assert code == 0
    assert output["command"] == "depth workflow-plan"
    assert output["plan"]["workflow"] == "slow_transaction"
    assert output["plan"]["status"] == "READY"


def test_source_cli_blocks_missing_identity_without_http(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="collect", run_type="COLLECT")
    store.write_json(run.path / "evidence" / "items.json", {
        "schema_version": 1,
        "kind": "items",
        "status": "SUCCESS",
        "data": {"items": [{"item_ref": "item-0001", "kind": "candidate", "wire_identity": {}}]},
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

    code, output = _run_cli([
        "--data-root",
        str(tmp_path),
        "source",
        "recent-requests",
        "--source-run-id",
        run.run_id,
        "--source-item-ref",
        "item-0001",
        "--time-context",
        "last_30m",
        "--ranking",
        "error",
    ])

    assert code == 0
    assert output["status"] == "BLOCKED"
    assert output["reason_code"] == "SOURCE_IDENTITY_INCOMPLETE"


def test_source_alarm_detail_cli_blocks_missing_alarm_identity_without_http(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="source", run_type="SOURCE")
    store.write_json(run.path / "evidence" / "alarm_events.json", {
        "schema_version": 1,
        "kind": "alarm_events",
        "status": "SUCCESS",
        "data": {"items": [{"item_ref": "alarm-event-0001", "kind": "alarm_event", "wire_identity": {}}]},
    })
    store.finalize_run(
        run,
        manifest={
            "schema_version": 1,
            "run_id": run.run_id,
            "run_type": "SOURCE",
            "overall": "SUCCESS",
            "artifacts": [{"kind": "alarm_events", "path": "evidence/alarm_events.json", "status": "SUCCESS"}],
            "coverage_ref": "coverage.json",
            "live_request_count": 0,
        },
        coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {}},
    )

    code, output = _run_cli([
        "--data-root",
        str(tmp_path),
        "source",
        "alarm-detail",
        "--source-run-id",
        run.run_id,
        "--source-item-ref",
        "alarm-event-0001",
        "--time-context",
        "last_30m",
    ])

    assert code == 0
    assert output["status"] == "BLOCKED"
    assert output["reason_code"] == "SOURCE_IDENTITY_INCOMPLETE"


def test_depth_commands_do_not_create_data_root_or_runs(tmp_path):
    data_root = tmp_path / "must-not-exist"

    code, output = _run_cli([
        "--data-root", str(data_root), "depth", "triage-path", "--path", "/favicon.ico"
    ])

    assert code == 0
    assert output["status"] == "SUCCESS"
    assert not data_root.exists()
