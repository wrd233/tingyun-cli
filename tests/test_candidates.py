import json

import pytest

from tingyun_cli.candidates import (
    ALLOWED_CANDIDATE_METRICS,
    inspect_candidates_all,
    inspect_candidates_filter,
    inspect_candidates_top,
    is_investigate_trace_eligible,
    normalize_candidates,
)


def _row(index, *, action=True):
    row = {
        "applicationId": 1600 + index,
        "applicationName": f"app-{index}",
        "actionName": f"SpringController/api/{index}",
        "requestType": "WEB",
        "responseP50": 10 + index,
        "responseP75": 20 + index,
        "responseP95": 30 + index,
        "responseP99": 40 + index,
        "responseTimeMillisecondAvg": 15 + index,
        "throughput": 3 + index,
        "totalCount": 100 + index,
        "errorRate": 0.01 * index,
        "errorTotalCount": index,
        "slowCount": 2 * index,
        "exceptionCountTotal": index % 3,
        "apdex": 0.95,
    }
    if action:
        row["actionId"] = 9000 + index
    return row


def test_normalize_candidates_preserves_all_rows_and_does_not_mark_1000_full():
    rows = [_row(i) for i in range(1000)]

    artifact = normalize_candidates(
        response={"status": 200, "data": rows},
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )

    assert artifact["data"]["row_count"] == 1000
    assert artifact["data"]["completeness"] == "BOUNDED"
    assert len(artifact["data"]["items"]) == 1000
    assert artifact["data"]["items"][0]["item_ref"] == "item-0001"
    assert artifact["data"]["items"][0]["wire_identity"] == {
        "actionId": 9000,
        "applicationId": 1600,
        "bizSystemId": "biz-1",
        "requestType": "WEB",
    }
    assert artifact["data"]["items"][0]["available_actions"] == ["investigate_trace"]
    assert artifact["data"]["items"][0]["metrics"]["p99"] == {"value": 40, "unit": "ms"}


def test_candidate_without_exact_action_identity_has_no_available_actions():
    artifact = normalize_candidates(
        response={"status": 200, "data": [_row(1, action=False)]},
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0001.json",
    )

    item = artifact["data"]["items"][0]
    assert "available_actions" not in item
    assert "actionId" not in item["wire_identity"]


def test_inspect_candidates_all_top_and_filter_are_local_json_views(tmp_path):
    artifact = normalize_candidates(
        response={"status": 200, "data": [_row(1), _row(5), _row(2)]},
        source_run_id="run-candidates",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0001.json",
    )
    run_path = tmp_path / "runs" / "run-candidates"
    evidence = run_path / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "candidates.json").write_text(json.dumps(artifact), encoding="utf-8")

    all_items = inspect_candidates_all(run_path)
    top_items = inspect_candidates_top(run_path, metric="p99", limit=2)
    filtered_items = inspect_candidates_filter(run_path, metric="error_rate", operator=">", value=0.02)

    assert [item["item_ref"] for item in all_items["items"]] == ["item-0001", "item-0002", "item-0003"]
    assert [item["name"] for item in top_items["items"]] == ["SpringController/api/5", "SpringController/api/2"]
    assert [item["name"] for item in filtered_items["items"]] == ["SpringController/api/5"]
    assert "p99" in ALLOWED_CANDIDATE_METRICS


def test_inspect_candidates_rejects_unstable_metric_and_expressions(tmp_path):
    artifact = normalize_candidates(
        response={"status": 200, "data": [_row(1)]},
        source_run_id="run-candidates",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0001.json",
    )
    run_path = tmp_path / "runs" / "run-candidates"
    evidence = run_path / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "candidates.json").write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported metric"):
        inspect_candidates_top(run_path, metric="actionName", limit=1)

    with pytest.raises(ValueError, match="unsupported operator"):
        inspect_candidates_filter(run_path, metric="p99", operator="AND", value=1)


def test_error_rate_unit_is_percent_not_ratio():
    artifact = normalize_candidates(
        response={"status": 200, "data": [_row(1)]},
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )
    error_rate = artifact["data"]["items"][0]["metrics"]["error_rate"]
    assert error_rate["unit"] == "percent"


def test_error_rate_percent_value_matches_wire():
    row = _row(1)
    row["errorTotalCount"] = 5
    row["totalCount"] = 100
    row["errorRate"] = 5.0
    artifact = normalize_candidates(
        response={"status": 200, "data": [row]},
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )
    er = artifact["data"]["items"][0]["metrics"]["error_rate"]
    assert er["unit"] == "percent"
    assert er["value"] == 5.0


def test_investigate_trace_eligible_only_for_proven_request_types():
    web_item = {"semantic_kind": "WEB_TRANSACTION", "wire_identity": {"bizSystemId": "b1", "applicationId": 1, "actionId": 10, "requestType": "WEB"}}
    tx_item = {"semantic_kind": "WEB_TRANSACTION", "wire_identity": {"bizSystemId": "b1", "applicationId": 1, "actionId": 10, "requestType": "TX"}}
    bg_item = {"semantic_kind": "BACKGROUND_TRANSACTION", "wire_identity": {"bizSystemId": "b1", "applicationId": 1, "actionId": 10, "requestType": "BG"}}
    composite_tx_item = {"semantic_kind": "WEB_TRANSACTION", "wire_identity": {"bizSystemId": "b1", "applicationId": 1, "actionId": 10, "requestType": "TX,IF"}}
    unknown_composite = {"wire_identity": {"bizSystemId": "b1", "applicationId": 1, "actionId": 10, "requestType": "XX,YY"}}
    unknown_single = {"wire_identity": {"bizSystemId": "b1", "applicationId": 1, "actionId": 10, "requestType": "ZZ"}}
    incomplete_item = {"wire_identity": {"bizSystemId": "b1", "applicationId": 1, "actionId": 10}}

    assert is_investigate_trace_eligible(web_item) is True
    assert is_investigate_trace_eligible(tx_item) is True
    assert is_investigate_trace_eligible(bg_item) is True
    assert is_investigate_trace_eligible(composite_tx_item) is True  # TX is proven, split works
    assert is_investigate_trace_eligible(unknown_composite) is False  # no proven type in parts
    assert is_investigate_trace_eligible(unknown_single) is False
    assert is_investigate_trace_eligible(incomplete_item) is False


def test_candidate_with_proven_request_type_gets_available_actions():
    row = _row(1)
    row["requestType"] = "WEB"
    artifact = normalize_candidates(
        response={"status": 200, "data": [row]},
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )
    item = artifact["data"]["items"][0]
    assert item["available_actions"] == ["investigate_trace"]
    assert "links" in item
    assert item["navigation"]["status"] == "SUCCESS"


def test_candidate_with_composite_tx_type_gets_actions():
    row = _row(1)
    row["requestType"] = "TX,IF"
    artifact = normalize_candidates(
        response={"status": 200, "data": [row]},
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )
    item = artifact["data"]["items"][0]
    assert item["available_actions"] == ["investigate_trace"]
    assert "links" not in item
    assert item["navigation"] == {"status": "MISSING", "reason": "URL_NOT_VERIFIED"}


def test_candidate_with_bg_type_gets_actions():
    row = _row(1)
    row["requestType"] = "BG"
    artifact = normalize_candidates(
        response={"status": 200, "data": [row]},
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )
    item = artifact["data"]["items"][0]
    assert item["available_actions"] == ["investigate_trace"]
    assert "links" not in item
    assert item["navigation"] == {"status": "MISSING", "reason": "URL_NOT_VERIFIED"}


def test_candidate_with_unknown_request_type_has_no_actions():
    row = _row(1)
    row["requestType"] = "XX"
    artifact = normalize_candidates(
        response={"status": 200, "data": [row]},
        source_run_id="run-source",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )
    item = artifact["data"]["items"][0]
    assert "available_actions" not in item
    assert "links" not in item
    assert item["navigation"]["status"] == "MISSING"


def test_source_run_id_preserved():
    artifact = normalize_candidates(
        response={"status": 200, "data": [_row(1)]},
        source_run_id="run-collect-123",
        scope={"bizSystemId": "biz-1"},
        time_context={"requested": "last_30m"},
        raw_ref="raw/response-0003.json",
    )
    assert artifact["data"]["items"][0]["source_run_id"] == "run-collect-123"
