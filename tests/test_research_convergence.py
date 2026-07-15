import json
from pathlib import Path

from tingyun_cli.research import build_research_view, diff_research_views, render_research_markdown
from tingyun_cli.manifest_schema import validate_schema


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ROOT = ROOT / "research" / "protocol"


def test_research_view_is_generated_from_canonical_ledgers_and_is_healthy():
    view = build_research_view(PROTOCOL_ROOT)

    assert view["schema_version"] == 1
    assert view["kind"] == "tingyun_research_view"
    assert view["summary"]["endpoint_count"] == 400
    assert view["summary"]["variant_count"] == 442
    assert view["summary"]["capability_count"] == 29
    assert view["summary"]["workflow_count"] == 5
    assert view["health"]["status"] == "PASS"
    assert not [issue for issue in view["health"]["issues"] if issue["severity"] == "ERROR"]

    stack = next(item for item in view["capabilities"] if item["id"] == "get_trace_stack")
    assert stack["verification"] == "VERIFIED"
    assert stack["endpoint_ids"] == ["ep_post_server_api_action_trace_detail_stacktraces"]
    assert stack["workflow_ids"] == ["trace_investigation", "trace_search_to_detail"]
    assert stack["gap_ids"] == ["gap_stack_non_empty"]


def test_research_health_detects_advertised_summary_drift(tmp_path):
    protocol = tmp_path / "protocol"
    protocol.mkdir()
    for name in ("endpoint-contracts.yaml", "workflows.yaml", "gaps-and-conflicts.md", "tingyun-capability-protocol.md"):
        (protocol / name).write_bytes((PROTOCOL_ROOT / name).read_bytes())

    contracts_path = protocol / "endpoint-contracts.yaml"
    contracts = json.loads(contracts_path.read_text())
    contracts["coverage"]["catalogued_endpoint_entries"] = 399
    contracts_path.write_text(json.dumps(contracts), encoding="utf-8")

    view = build_research_view(protocol)

    assert view["health"]["status"] == "FAIL"
    assert any(issue["code"] == "ENDPOINT_COUNT_DRIFT" for issue in view["health"]["issues"])


def test_research_diff_distinguishes_add_remove_modify_and_maturity_changes():
    before = {
        "schema_version": 1,
        "kind": "tingyun_research_view",
        "endpoints": [
            {"id": "ep-a", "fingerprint": "old"},
            {"id": "ep-b", "fingerprint": "same"},
        ],
        "capabilities": [
            {"id": "cap-a", "verification": "OBSERVED", "runtime_status": "RESEARCH_ONLY"}
        ],
        "gaps": [{"id": "gap-a", "status": "OPEN"}],
    }
    after = {
        "schema_version": 1,
        "kind": "tingyun_research_view",
        "endpoints": [
            {"id": "ep-a", "fingerprint": "new"},
            {"id": "ep-c", "fingerprint": "added"},
        ],
        "capabilities": [
            {"id": "cap-a", "verification": "LIVE_VERIFIED", "runtime_status": "ADVANCED_READ_ONLY"}
        ],
        "gaps": [{"id": "gap-a", "status": "CLOSED"}],
    }

    result = diff_research_views(before, after)

    assert result["status"] == "SUCCESS"
    assert result["endpoints"] == {
        "added": ["ep-c"],
        "removed": ["ep-b"],
        "modified": ["ep-a"],
    }
    assert result["capability_maturity_changes"] == [
        {
            "id": "cap-a",
            "before_verification": "OBSERVED",
            "after_verification": "LIVE_VERIFIED",
            "before_runtime_status": "RESEARCH_ONLY",
            "after_runtime_status": "ADVANCED_READ_ONLY",
        }
    ]
    assert result["gap_status_changes"] == [
        {"id": "gap-a", "before": "OPEN", "after": "CLOSED"}
    ]


def test_research_markdown_is_a_navigation_view_not_a_second_ledger():
    view = build_research_view(PROTOCOL_ROOT)

    rendered = render_research_markdown(view)

    assert "Generated from the four canonical files" in rendered
    assert "`get_trace_stack` | VERIFIED | ADVANCED_READ_ONLY" in rendered
    assert "Use `research-index.json`" in rendered


def test_research_health_detects_duplicate_variant_and_protocol_status_conflict(tmp_path):
    protocol = tmp_path / "protocol"
    protocol.mkdir()
    for name in ("endpoint-contracts.yaml", "workflows.yaml", "gaps-and-conflicts.md", "tingyun-capability-protocol.md"):
        (protocol / name).write_bytes((PROTOCOL_ROOT / name).read_bytes())
    contracts = json.loads((protocol / "endpoint-contracts.yaml").read_text())
    contracts["endpoints"][0]["variants"].append(dict(contracts["endpoints"][0]["variants"][0]))
    contracts["coverage"]["identified_variants"] += 1
    (protocol / "endpoint-contracts.yaml").write_text(json.dumps(contracts))
    workflows = json.loads((protocol / "workflows.yaml").read_text())
    next(item for item in workflows["capabilities"] if item["id"] == "get_trace_stack")["verification"] = "PARTIALLY_VERIFIED"
    (protocol / "workflows.yaml").write_text(json.dumps(workflows))

    view = build_research_view(protocol)
    codes = {issue["code"] for issue in view["health"]["issues"]}

    assert view["health"]["status"] == "FAIL"
    assert "DUPLICATE_VARIANT_ID" in codes
    assert "DUPLICATE_VARIANT_DISCRIMINANT" in codes
    assert "PROTOCOL_STATUS_CONFLICT" in codes


def test_research_machine_outputs_conform_to_committed_schemas():
    view = build_research_view(PROTOCOL_ROOT)
    diff = diff_research_views(view, view)

    assert validate_schema(view, json.loads((ROOT / "schemas" / "research-view.schema.json").read_text())) == []
    assert validate_schema(diff, json.loads((ROOT / "schemas" / "research-diff.schema.json").read_text())) == []
