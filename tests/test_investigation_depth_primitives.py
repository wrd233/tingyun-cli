from tingyun_cli.compare import compare_instances, compare_windows, diff_call_trees
from tingyun_cli.narrowing import adaptive_window_narrow, locate_peak
from tingyun_cli.selection import select_trace, trace_candidates_from_rows
from tingyun_cli.triage import analyze_external_dependencies, classify_request_path, cluster_error_signatures


def _trace_rows():
    rows = []
    for index in range(8):
        rows.append({
            "traceId": f"normal-{index}",
            "timestamp": f"2026-07-08T00:{index:02d}:00Z",
            "duration_ms": 120 + index,
            "error": False,
            "instanceId": "server1",
            "actionId": 13172,
        })
    for index in range(9):
        rows.append({
            "traceId": f"slow-{index}",
            "timestamp": f"2026-07-08T01:{index:02d}:00Z",
            "duration_ms": 128000 + index,
            "error": index == 4,
            "instanceId": "server1",
            "actionId": 13172,
        })
    return rows


def test_trace_candidates_have_units_scope_source_and_selection_inputs():
    candidates = trace_candidates_from_rows(
        _trace_rows(),
        scope={"type": "transaction", "business_system_id": 1061, "application_id": 1626, "action_id": 13172},
        source={
            "capability": "list_recent_requests",
            "ranking_type": "response",
            "source_run_id": "run-source",
            "source_item_ref": "recent-request-0001",
        },
        time_window={"from": "2026-07-08T00:00:00Z", "to": "2026-07-08T02:00:00Z"},
    )

    assert len(candidates) == 17
    assert candidates[0]["duration_ms"]["value"] == 120
    assert candidates[0]["scope"]["type"] == "trace"
    assert candidates[0]["parent_scope"]["type"] == "transaction"
    assert candidates[0]["source"]["capability"] == "list_recent_requests"
    assert candidates[0]["source_run_id"] == "run-source"
    assert candidates[0]["source_item_ref"] == "recent-request-0001"


def test_explicit_trace_selection_is_deterministic_and_records_provenance():
    candidates = trace_candidates_from_rows(
        _trace_rows(),
        scope={"type": "transaction", "business_system_id": 1061, "application_id": 1626, "action_id": 13172},
        source={
            "capability": "list_recent_requests",
            "ranking_type": "response",
            "source_run_id": "run-source",
            "source_item_ref": "recent-request-0001",
        },
        time_window={"from": "2026-07-08T00:00:00Z", "to": "2026-07-08T02:00:00Z"},
    )

    slowest = select_trace(candidates, strategy="slowest")
    error = select_trace(candidates, strategy="error")
    exact = select_trace(candidates, strategy="exact", trace_id="normal-3")

    assert slowest["trace_id"] == "slow-8"
    assert slowest["selection"]["strategy"] == "slowest"
    assert slowest["selection"]["rank"] == 1
    assert slowest["selection"]["candidate_count"] == 17
    assert error["trace_id"] == "slow-4"
    assert error["selection"]["strategy"] == "error"
    assert exact["trace_id"] == "normal-3"
    assert exact["selection"]["strategy"] == "exact"


def test_adaptive_window_narrowing_selects_high_density_window_with_lineage_and_budget():
    windows = [
        {"from": 0, "to": 105, "error_count": 12, "request_count": 240},
        {"from": 45, "to": 75, "error_count": 10, "request_count": 55},
        {"from": 55, "to": 65, "error_count": 8, "request_count": 18},
    ]

    result = adaptive_window_narrow(
        windows,
        signal="error_rate",
        min_window_minutes=10,
        max_steps=3,
        request_budget=3,
    )

    assert result["status"] == "SUCCESS"
    assert result["recommended_window"] == {"from": 55, "to": 65}
    assert result["actual_request_count"] == 0
    assert result["inspected_window_count"] == 3
    assert [step["selection_reason"] for step in result["steps"]] == [
        "highest_error_rate",
        "highest_error_rate",
        "min_window_reached",
    ]


def test_peak_locator_preserves_unknown_max_semantics_and_unresolved_state():
    result = locate_peak(
        windows=[
            {"from": 0, "to": 105, "reported_max_metric": 498419},
            {"from": 45, "to": 75, "reported_max_metric": 343000},
            {"from": 55, "to": 65, "reported_max_metric": 219000},
        ],
        metric_semantic_status="UNKNOWN",
        candidates=[],
        request_budget=3,
    )

    assert result["status"] == "UNRESOLVED"
    assert result["metric"]["name"] == "reported_max_metric"
    assert result["metric"]["semantic_status"] == "UNKNOWN"
    assert result["candidate_match"]["status"] == "NOT_FOUND"


def test_window_and_instance_compare_return_units_scope_deltas_and_completeness():
    window_compare = compare_windows(
        before={"source_run_id": "run-before", "scope": {"type": "transaction", "action_id": 13172}, "metrics": {"p99_ms": 400, "error_count": 0}},
        incident={"source_run_id": "run-incident", "scope": {"type": "transaction", "action_id": 13172}, "metrics": {"p99_ms": 131026, "error_count": 0}},
    )
    instance_compare = compare_instances([
        {"instance_id": 2691, "metrics": {"request_count": 5, "avg_response_ms": 130000}},
        {"instance_id": 2692, "metrics": {"request_count": 0, "avg_response_ms": None}},
    ])

    assert window_compare["metrics"]["p99_ms"]["delta"] == 130626
    assert window_compare["scope"]["type"] == "transaction"
    assert window_compare["source_refs"] == ["run-before", "run-incident"]
    assert instance_compare["completeness"] == "PARTIAL"
    assert instance_compare["items"][0]["scope"] == {"type": "instance", "instance_id": 2691}


def test_call_tree_diff_finds_abnormal_only_nodes_and_duration_amplification():
    baseline = {
        "name": "findRelation",
        "duration_ms": 121,
        "children": [{"name": "open.api.tianyancha.com", "duration_ms": 83}],
    }
    abnormal = {
        "name": "findRelation",
        "duration_ms": 129661,
        "children": [
            {"name": "open.api.tianyancha.com", "duration_ms": 207},
            {"name": "file-open.tianyancha.com", "duration_ms": 129401, "exception_class": "ConnectException"},
        ],
    }

    baseline["source_run_id"] = "run-normal"
    abnormal["source_run_id"] = "run-abnormal"
    diff = diff_call_trees(baseline, abnormal)

    assert diff["common_path"] == ["findRelation", "open.api.tianyancha.com"]
    assert diff["abnormal_only"][0]["name"] == "file-open.tianyancha.com"
    assert diff["abnormal_only"][0]["exception_class"] == "ConnectException"
    assert diff["duration_amplification"]["findRelation"] > 1000
    assert diff["source_refs"] == ["run-normal", "run-abnormal"]


def test_static_resource_triage_and_error_signature_clustering_are_explainable():
    assert classify_request_path("/favicon.ico") == {
        "class": "static_resource",
        "reason_code": "KNOWN_STATIC_EXTENSION",
    }
    assert classify_request_path("/grcv5/api/flow-mobile/v1/task-form-process/todo-pages/2449642") == {
        "class": "business_request",
        "reason_code": "API_PATH_PATTERN",
    }

    clusters = cluster_error_signatures([
        {"trace_id": "a", "http_status": 404, "message": "Not found TodoListItem ,todoId=2449642", "action_id": 13198},
        {"trace_id": "b", "http_status": 404, "message": "Not found TodoListItem ,todoId=2449666", "action_id": 13198},
        {"trace_id": "c", "exception_class": "ConnectException", "message": "Connection timed out", "action_id": 13172},
    ])

    assert clusters[0]["signature"] == "http_status=404|action=13198|message=not found todolistitem ,todoid=?"
    assert clusters[0]["representative"]["selection"]["strategy"] == "representative_signature"
    assert clusters[1]["signature"] == "exception=ConnectException|action=13172|message=connection timed out"


def test_external_dependency_analysis_flags_fixed_duration_cluster_without_root_cause_claim():
    result = analyze_external_dependencies([
        {"dependency": "file-open.tianyancha.com", "duration_ms": 128400, "action_id": 13172, "instance_id": "server1", "trace_id": "slow-1"},
        {"dependency": "file-open.tianyancha.com", "duration_ms": 129401, "action_id": 13172, "instance_id": "server1", "trace_id": "slow-2"},
        {"dependency": "file-open.tianyancha.com", "duration_ms": 131020, "action_id": 13172, "instance_id": "server2", "trace_id": "slow-3"},
        {"dependency": "open.api.tianyancha.com", "duration_ms": 207, "action_id": 13172, "instance_id": "server1", "trace_id": "normal-1"},
    ])

    dependency = result["dependencies"][0]
    assert dependency["dependency"] == "file-open.tianyancha.com"
    assert dependency["observed_duration_cluster"] == {"from_ms": 128400, "to_ms": 131020, "count": 3}
    assert dependency["fixed_timeout_signature_candidate"] is True
    assert dependency["interpretation"] == "candidate_signal_only"
    assert dependency["affected_transactions"] == [13172]
    assert dependency["representative_abnormal_trace"]["trace_id"] == "slow-3"
