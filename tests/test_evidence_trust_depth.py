from tingyun_cli.budgeting import RequestBudget, RequestCacheKey, RequestLedger
from tingyun_cli.corrections import active_artifacts, correction_record
from tingyun_cli.evidence import (
    Scope,
    duration_metric,
    metric_contract,
    scoped_item,
    url_evidence,
)


def test_duration_metrics_are_self_describing_ms_values():
    metric = duration_metric("duration", 833.358, raw_unit="ms")

    assert metric == {
        "name": "duration_ms",
        "value": 833.358,
        "unit": "ms",
        "raw": {"field": "duration", "value": 833.358, "unit": "ms"},
        "semantic_status": "VERIFIED",
    }


def test_unknown_time_units_keep_raw_value_without_guessing_ms():
    metric = duration_metric("overview.max", 498419, raw_unit=None)

    assert metric["name"] == "overview.max"
    assert metric["semantic_status"] == "UNKNOWN"
    assert metric["raw"] == {"field": "overview.max", "value": 498419, "unit": None}
    assert "value" not in metric
    assert "unit" not in metric


def test_scope_is_explicit_and_not_inferred_from_nearby_trace_identity():
    aggregate = scoped_item(
        item_ref="item-0001",
        item_type="candidate",
        scope=Scope.transaction(business_system_id=1061, application_id=1626, action_id=13198),
        metrics={"error_rate_pct": {"value": 20.69, "unit": "percent"}},
        identity={"instance_id": 2692},
    )

    assert aggregate["scope"] == {
        "type": "transaction",
        "business_system_id": 1061,
        "application_id": 1626,
        "action_id": 13198,
    }
    assert aggregate["identity"]["instance_id"] == 2692


def test_metric_contract_marks_ambiguous_fields_unknown_or_partial():
    exception_count = metric_contract("exception_count")
    overview_max = metric_contract("overview.max")

    assert exception_count["semantic_status"] == "AMBIGUOUS"
    assert "not equivalent to Java exception count" in exception_count["caveats"][0]
    assert overview_max["semantic_status"] == "UNKNOWN"
    assert overview_max["stable_normalized_name"] is None


def test_url_evidence_requires_successful_verification_for_success_status():
    unverified = url_evidence(
        object_type="trace",
        object_id="442933645",
        url="/web/server/action/trace/442933645",
        source_type="verified_template",
    )
    verified = url_evidence(
        object_type="transaction",
        object_id="13172",
        url="/web/server/action/overview/1061/1626/13172",
        source_type="observed_route",
        verification={"status": "SUCCESS", "verified_at": "2026-07-08T01:00:00Z", "http_status": 200},
    )

    assert unverified["verification"]["status"] == "NOT_ATTEMPTED"
    assert verified["verification"]["status"] == "SUCCESS"


def test_corrections_supersede_old_derived_artifacts_without_mutating_runs():
    artifacts = [
        {"artifact_id": "handoff-v1", "status": "ACTIVE"},
        {"artifact_id": "corrections-v1", "status": "ACTIVE"},
    ]
    correction = correction_record(
        artifact_id="handoff-v1",
        superseded_by="corrections-v1",
        reason="duration values were interpreted as seconds instead of milliseconds",
        evidence_refs=["runs/run-1/evidence/trace.json"],
        timestamp="2026-07-08T02:00:00Z",
    )

    assert correction["status"] == "SUPERSEDED"
    assert [item["artifact_id"] for item in active_artifacts(artifacts, [correction])] == ["corrections-v1"]


def test_request_budget_blocks_over_budget_and_counts_reuse_separately():
    budget = RequestBudget(max_live_requests=2, min_request_interval_seconds=2.0, max_narrowing_steps=3)
    ledger = RequestLedger(budget)
    key = RequestCacheKey(endpoint_id="ep", params_hash="abc", scope_hash="scope", time_window_hash="window")

    assert ledger.try_live_request("first")["status"] == "ALLOW"
    assert ledger.try_reuse(key, reused_from_run_id="run-old")["status"] == "REUSED"
    assert ledger.try_live_request("second")["status"] == "ALLOW"
    blocked = ledger.try_live_request("third")

    assert blocked["status"] == "BLOCKED"
    assert blocked["reason_code"] == "REQUEST_BUDGET_EXCEEDED"
    assert ledger.summary() == {
        "max_live_requests": 2,
        "actual_live_requests": 2,
        "reused_request_count": 1,
        "budget_remaining": 0,
    }

    assert not hasattr(ledger, "transport")
