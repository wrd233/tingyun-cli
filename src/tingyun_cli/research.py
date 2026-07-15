from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .manifest_schema import validate_schema
from .promotion import promotion_matrix


CANONICAL_FILES = (
    "endpoint-contracts.yaml",
    "workflows.yaml",
    "gaps-and-conflicts.md",
    "tingyun-capability-protocol.md",
)
SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"
RESEARCH_VIEW_SCHEMA_PATH = SCHEMA_ROOT / "research-view.schema.json"
RESEARCH_DIFF_SCHEMA_PATH = SCHEMA_ROOT / "research-diff.schema.json"


def build_research_view(protocol_root: Path) -> Dict[str, Any]:
    """Compile the canonical protocol ledgers into one deterministic Agent view."""
    protocol_root = Path(protocol_root)
    contracts = _load_json(protocol_root / "endpoint-contracts.yaml")
    workflows = _load_json(protocol_root / "workflows.yaml")
    gaps = _parse_gaps((protocol_root / "gaps-and-conflicts.md").read_text(encoding="utf-8"))
    protocol_claims = _parse_protocol_claims(
        (protocol_root / "tingyun-capability-protocol.md").read_text(encoding="utf-8")
    )
    promotions = promotion_matrix()

    endpoint_rows = list(contracts.get("endpoints", []))
    capability_rows = list(workflows.get("capabilities", []))
    workflow_rows = list(workflows.get("recipes", []))
    endpoint_by_id = {str(row.get("id")): row for row in endpoint_rows}
    capability_by_id = {str(row.get("id")): row for row in capability_rows}
    workflows_by_capability: Dict[str, List[str]] = defaultdict(list)
    for workflow in workflow_rows:
        for step in workflow.get("steps", []):
            capability_id = step.get("capability")
            if capability_id:
                workflows_by_capability[str(capability_id)].append(str(workflow.get("id")))
    gaps_by_capability: Dict[str, List[str]] = defaultdict(list)
    gaps_by_endpoint: Dict[str, List[str]] = defaultdict(list)
    for gap in gaps:
        for capability_id in gap["capability_ids"]:
            gaps_by_capability[capability_id].append(gap["id"])
        for endpoint_id in gap["endpoint_ids"]:
            gaps_by_endpoint[endpoint_id].append(gap["id"])
    capabilities_by_endpoint: Dict[str, List[str]] = defaultdict(list)
    for capability in capability_rows:
        for endpoint_id in capability.get("uses", []):
            capabilities_by_endpoint[str(endpoint_id)].append(str(capability.get("id")))
    promotion_by_protocol: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in promotions.values():
        protocol_capability = str(row.get("protocol_capability") or row.get("capability"))
        promotion_by_protocol[protocol_capability].append(dict(row))

    endpoints = []
    for row in endpoint_rows:
        endpoint_id = str(row.get("id"))
        compact = {
            "id": endpoint_id,
            "method": row.get("method"),
            "path": row.get("path"),
            "access": row.get("access"),
            "role": row.get("role"),
            "verification": row.get("verification"),
            "variant_count": len(row.get("variants", [])),
            "variant_ids": sorted(str(item.get("id")) for item in row.get("variants", [])),
            "capability_ids": sorted(set(capabilities_by_endpoint.get(endpoint_id, []))),
            "gap_ids": sorted(set(gaps_by_endpoint.get(endpoint_id, []))),
            "fingerprint": _fingerprint(row),
        }
        endpoints.append(compact)

    capabilities = []
    for row in capability_rows:
        capability_id = str(row.get("id"))
        runtime_rows = sorted(
            promotion_by_protocol.get(capability_id, []), key=lambda item: str(item.get("capability"))
        )
        capabilities.append({
            "id": capability_id,
            "title": row.get("title"),
            "verification": row.get("verification"),
            "runtime_status": _aggregate_runtime_status(runtime_rows),
            "runtime_promotions": runtime_rows,
            "endpoint_ids": sorted(str(value) for value in row.get("uses", [])),
            "workflow_ids": sorted(set(workflows_by_capability.get(capability_id, []))),
            "gap_ids": sorted(set(gaps_by_capability.get(capability_id, []))),
            "fingerprint": _fingerprint(row),
        })

    generated_workflows = []
    for row in workflow_rows:
        generated_workflows.append({
            "id": str(row.get("id")),
            "title": row.get("title"),
            "verification": row.get("verification"),
            "capability_ids": [str(step.get("capability")) for step in row.get("steps", [])],
            "required_capability_ids": [
                str(step.get("capability")) for step in row.get("steps", []) if step.get("required")
            ],
            "fingerprint": _fingerprint(row),
        })

    variant_count = sum(len(row.get("variants", [])) for row in endpoint_rows)
    view: Dict[str, Any] = {
        "schema_version": 1,
        "kind": "tingyun_research_view",
        "canonical_sources": [
            {"path": name, "sha256": _sha256(protocol_root / name)} for name in CANONICAL_FILES
        ],
        "summary": {
            "endpoint_count": len(endpoint_rows),
            "variant_count": variant_count,
            "capability_count": len(capability_rows),
            "workflow_count": len(workflow_rows),
            "gap_count": len(gaps),
            "runtime_promotion_count": len(promotions),
        },
        "distributions": {
            "endpoint_access": _distribution(row.get("access") for row in endpoint_rows),
            "endpoint_role": _distribution(row.get("role") for row in endpoint_rows),
            "endpoint_verification": _distribution(row.get("verification") for row in endpoint_rows),
            "capability_verification": _distribution(row.get("verification") for row in capability_rows),
            "gap_status": _distribution(row.get("status") for row in gaps),
            "runtime_status": _distribution(
                row.get("runtime_status") for row in promotions.values()
            ),
        },
        "endpoints": sorted(endpoints, key=lambda item: item["id"]),
        "capabilities": sorted(capabilities, key=lambda item: item["id"]),
        "workflows": sorted(generated_workflows, key=lambda item: item["id"]),
        "gaps": gaps,
        "protocol_claims": protocol_claims,
        "orphans": {
            "endpoint_ids": sorted(set(endpoint_by_id) - set(capabilities_by_endpoint)),
            "capability_ids": sorted(set(capability_by_id) - set(workflows_by_capability)),
        },
    }
    view["health"] = _health(
        view, contracts, endpoint_rows, endpoint_by_id, capability_by_id, promotions, protocol_claims
    )
    schema_issues = validate_schema(view, _load_json(RESEARCH_VIEW_SCHEMA_PATH))
    if schema_issues:
        view["health"]["status"] = "FAIL"
        view["health"]["issues"] = sorted(
            view["health"]["issues"]
            + [_issue("RESEARCH_VIEW_SCHEMA_VIOLATION", "ERROR", json.dumps(issue, sort_keys=True)) for issue in schema_issues],
            key=lambda item: (item["severity"], item["code"], item["message"]),
        )
    return view


def diff_research_views(before: Mapping[str, Any], after: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a small structural diff between two generated Research Views."""
    before_endpoints = _index(before.get("endpoints", []))
    after_endpoints = _index(after.get("endpoints", []))
    before_capabilities = _index(before.get("capabilities", []))
    after_capabilities = _index(after.get("capabilities", []))
    before_gaps = _index(before.get("gaps", []))
    after_gaps = _index(after.get("gaps", []))

    endpoint_ids_before, endpoint_ids_after = set(before_endpoints), set(after_endpoints)
    modified = sorted(
        item_id for item_id in endpoint_ids_before & endpoint_ids_after
        if before_endpoints[item_id].get("fingerprint") != after_endpoints[item_id].get("fingerprint")
    )
    maturity = []
    for capability_id in sorted(set(before_capabilities) & set(after_capabilities)):
        old, new = before_capabilities[capability_id], after_capabilities[capability_id]
        if (old.get("verification"), old.get("runtime_status")) != (
            new.get("verification"), new.get("runtime_status")
        ):
            maturity.append({
                "id": capability_id,
                "before_verification": old.get("verification"),
                "after_verification": new.get("verification"),
                "before_runtime_status": old.get("runtime_status"),
                "after_runtime_status": new.get("runtime_status"),
            })
    gap_changes = []
    for gap_id in sorted(set(before_gaps) & set(after_gaps)):
        old, new = before_gaps[gap_id].get("status"), after_gaps[gap_id].get("status")
        if old != new:
            gap_changes.append({"id": gap_id, "before": old, "after": new})
    result = {
        "schema_version": 1,
        "kind": "tingyun_research_diff",
        "status": "SUCCESS",
        "endpoints": {
            "added": sorted(endpoint_ids_after - endpoint_ids_before),
            "removed": sorted(endpoint_ids_before - endpoint_ids_after),
            "modified": modified,
        },
        "capability_maturity_changes": maturity,
        "gap_status_changes": gap_changes,
    }
    violations = validate_schema(result, _load_json(RESEARCH_DIFF_SCHEMA_PATH))
    if violations:
        raise ValueError(f"RESEARCH_DIFF_SCHEMA_VIOLATION: {json.dumps(violations, sort_keys=True)}")
    return result


def render_research_markdown(view: Mapping[str, Any]) -> str:
    summary = view["summary"]
    health = view["health"]
    lines = [
        "# Generated Research Overview",
        "",
        "> Generated from the four canonical files in `research/protocol/`; do not edit by hand.",
        "",
        f"Health: **{health['status']}**. Endpoints: **{summary['endpoint_count']}**; variants: **{summary['variant_count']}**; capabilities: **{summary['capability_count']}**; workflows: **{summary['workflow_count']}**; gaps: **{summary['gap_count']}**.",
        "",
        "## Capability maturity and Runtime status",
        "",
        "| Capability | Verification | Runtime | Workflows | Gaps |",
        "|---|---|---|---:|---:|",
    ]
    for capability in view["capabilities"]:
        lines.append(
            f"| `{capability['id']}` | {capability.get('verification') or 'UNKNOWN'} | {capability.get('runtime_status') or 'NOT_PROMOTED'} | {len(capability['workflow_ids'])} | {len(capability['gap_ids'])} |"
        )
    lines.extend(["", "## Health issues", ""])
    if health["issues"]:
        for issue in health["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    else:
        lines.append("No health issues.")
    lines.extend([
        "",
        "## Navigation",
        "",
        "Use `research-index.json` for endpoint, workflow, gap, promotion, distribution, orphan, and source-hash detail. Use `research/tools/research_views.py diff` to compare two generated JSON views.",
        "",
    ])
    return "\n".join(lines)


def _health(view, contracts, endpoint_rows, endpoint_by_id, capability_by_id, promotions, protocol_claims):
    issues: List[Dict[str, Any]] = []
    advertised = contracts.get("coverage", {})
    actual_endpoints = view["summary"]["endpoint_count"]
    actual_variants = view["summary"]["variant_count"]
    if advertised.get("catalogued_endpoint_entries") != actual_endpoints:
        issues.append(_issue(
            "ENDPOINT_COUNT_DRIFT", "ERROR",
            f"coverage advertises {advertised.get('catalogued_endpoint_entries')} endpoints; generated count is {actual_endpoints}",
        ))
    if advertised.get("identified_variants") != actual_variants:
        issues.append(_issue(
            "VARIANT_COUNT_DRIFT", "ERROR",
            f"coverage advertises {advertised.get('identified_variants')} variants; generated count is {actual_variants}",
        ))
    _duplicate_issues(view["endpoints"], "DUPLICATE_ENDPOINT_ID", issues)
    _duplicate_issues(view["capabilities"], "DUPLICATE_CAPABILITY_ID", issues)
    _duplicate_issues(view["workflows"], "DUPLICATE_WORKFLOW_ID", issues)
    _duplicate_issues(view["gaps"], "DUPLICATE_GAP_ID", issues)
    method_paths = Counter(
        (str(row.get("method") or "").upper(), str(row.get("path") or ""))
        for row in endpoint_rows
    )
    for (method, path), count in sorted(method_paths.items()):
        if count > 1:
            issues.append(_issue("DUPLICATE_ENDPOINT_METHOD_PATH", "ERROR", f"{method} {path} appears {count} times"))
    for endpoint in endpoint_rows:
        endpoint_id = str(endpoint.get("id"))
        variants = [item for item in endpoint.get("variants", []) if isinstance(item, Mapping)]
        variant_ids = Counter(str(item.get("id")) for item in variants)
        for variant_id, count in sorted(variant_ids.items()):
            if count > 1:
                issues.append(_issue("DUPLICATE_VARIANT_ID", "ERROR", f"{endpoint_id}:{variant_id} appears {count} times"))
        discriminants = Counter(_fingerprint(_variant_discriminant(item)) for item in variants)
        for fingerprint, count in sorted(discriminants.items()):
            if count > 1:
                issues.append(_issue("DUPLICATE_VARIANT_DISCRIMINANT", "ERROR", f"{endpoint_id}:{fingerprint} appears {count} times"))
    for capability in view["capabilities"]:
        for endpoint_id in capability["endpoint_ids"]:
            if endpoint_id not in endpoint_by_id:
                issues.append(_issue("UNKNOWN_ENDPOINT_REFERENCE", "ERROR", f"{capability['id']} references {endpoint_id}"))
        for workflow_id in capability["workflow_ids"]:
            if not any(item["id"] == workflow_id for item in view["workflows"]):
                issues.append(_issue("UNKNOWN_WORKFLOW_REFERENCE", "ERROR", f"{capability['id']} references {workflow_id}"))
    for workflow in view["workflows"]:
        for capability_id in workflow["capability_ids"]:
            if capability_id not in capability_by_id:
                issues.append(_issue("UNKNOWN_CAPABILITY_REFERENCE", "ERROR", f"{workflow['id']} references {capability_id}"))
    for gap in view["gaps"]:
        for capability_id in gap["capability_ids"]:
            if capability_id not in capability_by_id:
                issues.append(_issue("UNKNOWN_GAP_CAPABILITY_REFERENCE", "ERROR", f"{gap['id']} references {capability_id}"))
        for endpoint_id in gap["endpoint_ids"]:
            if endpoint_id not in endpoint_by_id:
                issues.append(_issue("UNKNOWN_GAP_ENDPOINT_REFERENCE", "ERROR", f"{gap['id']} references {endpoint_id}"))
    for row in promotions.values():
        protocol_capability = row.get("protocol_capability")
        if protocol_capability not in capability_by_id:
            issues.append(_issue("UNMAPPED_RUNTIME_CAPABILITY", "ERROR", f"{row.get('capability')} has no valid protocol_capability"))
        endpoint_id = row.get("endpoint_id")
        if endpoint_id and endpoint_id not in endpoint_by_id:
            issues.append(_issue("UNKNOWN_RUNTIME_ENDPOINT", "ERROR", f"{row.get('capability')} references {endpoint_id}"))
        if endpoint_id and row.get("runtime_status") in {"CORE_LIVE_VALIDATED", "ADVANCED_READ_ONLY"}:
            if endpoint_by_id.get(endpoint_id, {}).get("access") != "READ":
                issues.append(_issue("UNSAFE_RUNTIME_PROMOTION", "ERROR", f"{row.get('capability')} promotes non-READ {endpoint_id}"))
            protocol_row = capability_by_id.get(str(protocol_capability), {})
            if protocol_row.get("verification") != "VERIFIED":
                issues.append(_issue("RUNTIME_VERIFICATION_CONFLICT", "ERROR", f"{row.get('capability')} is promoted but {protocol_capability} is {protocol_row.get('verification')}"))
    for claim in protocol_claims:
        capability_id = claim["capability_id"]
        canonical = capability_by_id.get(capability_id)
        if canonical is None:
            issues.append(_issue("UNKNOWN_PROTOCOL_CAPABILITY", "ERROR", f"protocol matrix references {capability_id}"))
        elif claim["status"] == "VERIFIED" and canonical.get("verification") != "VERIFIED":
            issues.append(_issue("PROTOCOL_STATUS_CONFLICT", "ERROR", f"protocol claims {capability_id} VERIFIED but workflow ledger is {canonical.get('verification')}"))
    issues = sorted(issues, key=lambda item: (item["severity"], item["code"], item["message"]))
    return {"status": "FAIL" if any(item["severity"] == "ERROR" for item in issues) else "PASS", "issues": issues}


def _parse_gaps(text: str) -> List[Dict[str, Any]]:
    headings = list(re.finditer(r"^##\s+(gap_[a-zA-Z0-9_]+):\s*(.+)$", text, re.MULTILINE))
    gaps = []
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[match.end():end]
        title = match.group(2).strip()
        gaps.append({
            "id": match.group(1),
            "title": title,
            "status": _gap_status(title),
            "capability_ids": _related_ids(section, "related_capabilities"),
            "endpoint_ids": _related_ids(section, "related_endpoints"),
            "workflow_ids": _related_ids(section, "related_recipes"),
            "fingerprint": _fingerprint({"title": title, "section": section.strip()}),
        })
    return sorted(gaps, key=lambda item: item["id"])


def _parse_protocol_claims(text: str) -> List[Dict[str, str]]:
    claims: List[Dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) != 6 or columns[2] in {"状态", "---"}:
            continue
        capability_ids = re.findall(r"`([^`]+)`", columns[3])
        for capability_id in capability_ids:
            claims.append({
                "category": columns[0],
                "branch": columns[1],
                "status": columns[2],
                "capability_id": capability_id,
            })
    return sorted(claims, key=lambda item: (item["capability_id"], item["category"], item["branch"], item["status"]))


def _variant_discriminant(variant: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in variant.items()
        if key not in {"id", "observed_count", "evidence"}
    }


def _related_ids(section: str, field: str) -> List[str]:
    match = re.search(rf"^- {re.escape(field)}:(.*?)(?=^- [a-zA-Z_][a-zA-Z0-9_ -]*:|\n\n|\Z)", section, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    return sorted(set(re.findall(r"`([^`]+)`", match.group(1))))


def _gap_status(title: str) -> str:
    upper = title.upper()
    if "CLOSED" in upper:
        return "CLOSED"
    if "SPLIT" in upper:
        return "SPLIT"
    return "OPEN"


def _aggregate_runtime_status(rows: Sequence[Mapping[str, Any]]) -> str:
    statuses = sorted(set(str(row.get("runtime_status")) for row in rows if row.get("runtime_status")))
    if not statuses:
        return "NOT_PROMOTED"
    return statuses[0] if len(statuses) == 1 else "+".join(statuses)


def _distribution(values: Iterable[Any]) -> Dict[str, int]:
    return dict(sorted(Counter(str(value or "UNKNOWN") for value in values).items()))


def _duplicate_issues(rows, code, issues):
    counts = Counter(str(row.get("id")) for row in rows)
    for item_id, count in sorted(counts.items()):
        if count > 1:
            issues.append(_issue(code, "ERROR", f"{item_id} appears {count} times"))


def _issue(code: str, severity: str, message: str) -> Dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _index(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    return {str(row.get("id")): row for row in rows}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
