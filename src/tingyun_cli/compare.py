from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


def compare_windows(*, before: Mapping[str, Any], incident: Mapping[str, Any]) -> Dict[str, Any]:
    metrics: Dict[str, Dict[str, Any]] = {}
    before_metrics = before.get("metrics", {})
    incident_metrics = incident.get("metrics", {})
    for name in sorted(set(before_metrics) | set(incident_metrics)):
        before_value = before_metrics.get(name)
        incident_value = incident_metrics.get(name)
        delta = incident_value - before_value if before_value is not None and incident_value is not None else None
        metrics[name] = {"before": before_value, "incident": incident_value, "delta": delta, "unit": _unit_from_metric(name), "completeness": "FULL" if delta is not None else "PARTIAL"}
    return {"schema_version": 1, "scope": dict(incident.get("scope") or before.get("scope") or {}), "source_refs": _source_refs(before, incident), "metrics": metrics}


def compare_instances(items: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    output = []
    complete = True
    for item in items:
        metrics = dict(item.get("metrics", {}))
        complete = complete and not any(value is None for value in metrics.values())
        output.append({"scope": {"type": "instance", "instance_id": item.get("instance_id")}, "source_refs": _source_refs(item), "metrics": metrics})
    return {"schema_version": 1, "completeness": "FULL" if complete else "PARTIAL", "items": output}


def diff_call_trees(baseline: Mapping[str, Any], abnormal: Mapping[str, Any]) -> Dict[str, Any]:
    baseline_nodes = _flatten(baseline)
    abnormal_nodes = _flatten(abnormal)
    common_keys = [key for key in abnormal_nodes if key in baseline_nodes]
    abnormal_only = [dict(node) for key, node in abnormal_nodes.items() if key not in baseline_nodes]
    baseline_only = [dict(node) for key, node in baseline_nodes.items() if key not in abnormal_nodes]
    amplification = {}
    for key in common_keys:
        before = float(baseline_nodes[key].get("duration_ms") or 0)
        after = float(abnormal_nodes[key].get("duration_ms") or 0)
        label = str(abnormal_nodes[key].get("name") or key)
        amplification[label if label not in amplification else key] = None if before == 0 else after / before
    return {"schema_version": 1, "source_refs": _source_refs(baseline, abnormal), "common_path": [str(abnormal_nodes[key].get("name") or key) for key in common_keys], "abnormal_only": abnormal_only, "baseline_only": baseline_only, "duration_amplification": amplification}


def _flatten(node: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    found: Dict[str, Mapping[str, Any]] = {}

    def visit(current: Mapping[str, Any], path: str) -> None:
        name = str(current.get("name") or "<unnamed>")
        key = f"{path}/{name}"
        found[key] = current
        for index, child in enumerate(current.get("children") or []):
            if isinstance(child, Mapping):
                visit(child, f"{key}[{index}]")

    visit(node, "root")
    return found


def _source_refs(*items: Mapping[str, Any]) -> List[str]:
    refs: List[str] = []
    for item in items:
        values = [item.get("source_run_id"), *(item.get("source_refs") or [])]
        for value in values:
            if value and value not in refs:
                refs.append(str(value))
    return refs


def _unit_from_metric(name: str) -> str:
    if name.endswith("_ms"):
        return "ms"
    if name.endswith("_pct"):
        return "percent"
    if name.endswith("_count"):
        return "count"
    return "unknown"
