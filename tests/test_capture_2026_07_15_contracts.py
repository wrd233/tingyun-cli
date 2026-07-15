import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "capture_2026_07_15"


def _json(path):
    return json.loads(path.read_text())


def test_sanitized_fixtures_preserve_only_required_protocol_relationships():
    alarm = _json(FIXTURES / "alarm_detail.json")["data"]
    parent = {item["key"]: item["value"] for item in alarm["parentGroup"]}
    assert alarm["target"] == {"key": "$$transaction", "value": "action-fake-1"}
    assert parent == {"$application_id": "app-fake-1", "$biz_system_id": "biz-fake-1"}
    assert len(alarm["metrics"]) == 1

    detail = _json(FIXTURES / "trace_detail.json")["data"]
    call_tree = _json(FIXTURES / "trace_call_tree.json")["data"]
    exceptions = _json(FIXTURES / "trace_exceptions.json")["data"]
    stack = _json(FIXTURES / "trace_stack.json")["data"]
    assert detail["id"] == "trace-fake-1"
    assert "treeNode" not in detail
    assert call_tree["treeNode"][0]["child"][0]["id"] == "tree-fake-error"
    assert exceptions[0]["stack"] and stack


def test_protocol_workflows_and_gap_dispositions_are_consistent():
    endpoints = _json(ROOT / "research" / "protocol" / "endpoint-contracts.yaml")
    workflows = _json(ROOT / "research" / "protocol" / "workflows.yaml")
    gaps = (ROOT / "research" / "protocol" / "gaps-and-conflicts.md").read_text()

    overlay = endpoints["capture_integration_2026_07_15"]
    assert overlay["scope"]["network_records"] == 502
    assert endpoints["coverage"]["catalogued_endpoint_entries"] == len(endpoints["endpoints"]) == 400
    assert endpoints["coverage"]["identified_variants"] == sum(len(endpoint["variants"]) for endpoint in endpoints["endpoints"])
    deltas = {delta["path"]: delta for delta in overlay["endpoint_contract_deltas"]}
    assert deltas["/nalarm-api/query/event/pageList"]["body_kind"] == "json"
    assert deltas["/nalarm-api/query/initView"]["body_parameters"] == ["lang"]
    assert any(delta.get("path") == "/server-api/action/trace/detail/exceptions" and delta["body_parameters"][:4] == ["treeId", "traceId", "bizSystemId", "queryTimestamp"] for delta in overlay["endpoint_contract_deltas"])
    canonical = {endpoint["path"]: endpoint for endpoint in endpoints["endpoints"]}
    assert canonical["/server-api/action/trace/detail/exceptions"]["observed_scope"]["count"] == 16
    assert canonical["/server-api/action/trace/detail/stackTraces"]["observed_scope"]["count"] == 3
    assert canonical["/nalarm-api/query/event/pageList"]["request"]["body_kinds"] == {"json": 2}
    assert canonical["/nalarm-api/event/read"]["access"] == "WRITE"
    alarm_detail_capability = next(capability for capability in workflows["capabilities"] if capability["id"] == "read_alarm_event_detail")
    assert "ep_post_nalarm_api_event_read" not in alarm_detail_capability["uses"]

    capabilities = {capability["id"]: capability for capability in workflows["capabilities"]}
    assert capabilities["search_trace_candidates"]["verification"] == "VERIFIED"
    assert capabilities["get_trace_stack"]["verification"] == "VERIFIED"
    assert "SPLIT" in gaps.split("## gap_runtime_to_trace_list", 1)[1].splitlines()[0]
    assert "CLOSED" in gaps.split("## gap_stack_non_empty", 1)[1].splitlines()[0]
    assert "STILL_OPEN" in gaps.split("## gap_dubbo_provider_trace_action_type", 1)[1].splitlines()[0]
    assert "NEW_GAP" in gaps.split("## gap_alarm_read_state_readback", 1)[1].splitlines()[0]


def test_capture_fixtures_do_not_contain_private_transport_material():
    combined = "\n".join(path.read_text() for path in sorted(FIXTURES.glob("*.json"))).lower()
    for forbidden in ("authorization", "cookie", "bearer ", "token", "http://", "https://"):
        assert forbidden not in combined
