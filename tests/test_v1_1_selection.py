import json
import pytest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tingyun_cli.candidate_matching import match_candidates
from tingyun_cli.cli import main
from tingyun_cli.investigation_selection import trace_target_check
from tingyun_cli.trace_sample_assessment import assess_trace_sample


FIXTURES = Path(__file__).parent / "fixtures" / "v1_1"


def _fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _candidate_artifact():
    return {
        "schema_version": 1,
        "kind": "candidates",
        "time_context": {"requested": {"kind": "exact_range", "value": "synthetic-window"}},
        "data": {
            "items": [
                {
                    "item_ref": "item-0001",
                    "source_run_id": "run-collect-a",
                    "name": "SpringController/example/orders/list",
                    "semantic_kind": "WEB_TRANSACTION",
                    "labels": {"applicationName": "Synthetic Web Application", "requestType": "TX,IF"},
                    "metrics": {"p95": {"value": 900, "unit": "ms"}},
                    "available_actions": ["investigate_trace"],
                    "links": [{"url": "/verified/synthetic", "verification": "DERIVED_FROM_VERIFIED_ROUTE"}],
                    "navigation": {"status": "SUCCESS", "verification": "DERIVED_FROM_VERIFIED_ROUTE"},
                },
                {
                    "item_ref": "item-0002",
                    "source_run_id": "run-collect-a",
                    "name": "SpringController/example/orders/detail",
                    "semantic_kind": "WEB_TRANSACTION",
                    "labels": {"applicationName": "Other Application", "requestType": "TX"},
                    "metrics": {},
                    "available_actions": ["investigate_trace"],
                },
            ]
        },
    }


def test_candidate_match_contract_exact_strong_weak_and_not_found():
    artifact = _candidate_artifact()

    exact = match_candidates(artifact, run_id="run-collect-a", name="SpringController/example/orders/list", application="Synthetic Web Application", request_type="TX,IF")
    strong = match_candidates(artifact, run_id="run-collect-a", name="orders/list", route_fragment="/example/orders/list")
    weak = match_candidates(artifact, run_id="run-collect-a", name="orders")
    missing = match_candidates(artifact, run_id="run-collect-a", name="SpringController/example/missing")

    assert exact["overall_match_level"] == "EXACT"
    assert exact["matches"][0]["execution_eligible"] is True
    assert exact["matches"][0]["matched_fields"] == ["application", "name", "request_type"]
    assert strong["overall_match_level"] == "STRONG"
    assert strong["matches"][0]["match_basis"] == "exact_route_fragment"
    assert weak["overall_match_level"] == "WEAK"
    assert weak["matches"][0]["execution_eligible"] is False
    assert missing == {
        "schema_version": 1,
        "run_id": "run-collect-a",
        "time_context": artifact["time_context"],
        "query": {"name": "SpringController/example/missing"},
        "overall_match_level": "NOT_FOUND",
        "matches": [],
    }


def test_candidate_match_constraint_mismatch_is_visible_but_never_executable():
    result = match_candidates(_candidate_artifact(), run_id="run-collect-a", name="SpringController/example/orders/list", application="Wrong Application")

    assert result["matches"][0]["match_level"] == "WEAK"
    assert result["matches"][0]["mismatched_fields"] == ["application"]
    assert result["matches"][0]["execution_eligible"] is False


def test_inspect_candidates_match_cli_is_local_and_does_not_mutate_data_root(tmp_path):
    run_path = tmp_path / "runs" / "run-collect-a"
    (run_path / "evidence").mkdir(parents=True)
    (run_path / "evidence" / "candidates.json").write_text(json.dumps(_candidate_artifact()), encoding="utf-8")
    before = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    output = StringIO()
    with redirect_stdout(output):
        code = main(["--data-root", str(tmp_path), "inspect", "candidates", "match", "--run-id", "run-collect-a", "--name", "SpringController/example/orders/list"])

    after = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    payload = json.loads(output.getvalue())
    assert code == 0
    assert payload["overall_match_level"] == "EXACT"
    assert before == after


def test_trace_target_check_prefers_exact_lineage_and_rejects_wrong_target():
    scenario = _fixture("wrong_target_trace/scenario.json")

    assert trace_target_check(scenario["candidate_binding"], scenario["correct_trace"]) == {
        "status": "EXACT_TARGET",
        "expected": {"source_run_id": "run-collect-a", "source_item_ref": "item-0007"},
        "observed": {"source_run_id": "run-collect-a", "source_item_ref": "item-0007"},
    }
    assert trace_target_check(scenario["candidate_binding"], scenario["wrong_trace"])["status"] == "WRONG_TARGET"
    assert trace_target_check(scenario["candidate_binding"], {"source": {}})["status"] == "UNVERIFIABLE"


def test_trace_sample_assessment_covers_abnormal_normal_and_unknown():
    normal = _fixture("aggregate_abnormal_trace_normal.json")
    abnormal_trace = json.loads(json.dumps(normal["trace"]))
    abnormal_trace["data"]["summary"]["duration"] = 1200
    abnormal_trace["data"]["items"][0]["summary"]["duration"] = 1200

    abnormal = assess_trace_sample(normal["candidate"], abnormal_trace, alarm_metric="response_time")
    contrast = assess_trace_sample(normal["candidate"], normal["trace"], alarm_metric="response_time")
    unknown = assess_trace_sample({"metrics": {}}, {"data": {"summary": {}, "exceptions": []}})

    assert abnormal["duration_position"] == "P95_TO_P99"
    assert abnormal["sample_assessment"] == "ABNORMAL_ALIGNED"
    assert contrast["duration_position"] == "AT_OR_BELOW_P50"
    assert contrast["sample_assessment"] == "NORMAL_CONTRAST"
    assert contrast["candidate_exception_count_semantic_status"] == "UNKNOWN"
    assert unknown["duration_position"] == "UNAVAILABLE"
    assert unknown["sample_assessment"] == "UNKNOWN"


def test_trace_sample_assess_cli_consumes_evidence_files_without_data_root_writes(tmp_path):
    scenario = _fixture("aggregate_abnormal_trace_normal.json")
    candidate_path = tmp_path / "candidate.json"
    trace_path = tmp_path / "trace.json"
    candidate_path.write_text(json.dumps(scenario["candidate"]), encoding="utf-8")
    trace_path.write_text(json.dumps(scenario["trace"]), encoding="utf-8")
    before = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    output = StringIO()
    with redirect_stdout(output):
        code = main(["--data-root", str(tmp_path / "unused-data-root"), "depth", "trace-sample-assess", "--candidate", str(candidate_path), "--trace", str(trace_path), "--alarm-metric", "response_time"])

    after = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert code == 0
    assert json.loads(output.getvalue())["assessment"]["sample_assessment"] == "NORMAL_CONTRAST"
    assert before == after


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["inspect", "candidates", "--help"], "{all,top,filter,match}"),
        (["depth", "trace-sample-assess", "--help"], "--candidate"),
        (["depth", "evidence-compile", "--help"], "--manifest"),
        (["depth", "evidence-validate", "--help"], "--compiled-dir"),
    ],
)
def test_v1_1_cli_surfaces_are_reachable_from_actual_argparse(argv, expected):
    output = StringIO()
    with redirect_stdout(output), pytest.raises(SystemExit) as stopped:
        main(argv)

    assert stopped.value.code == 0
    assert expected in output.getvalue()
