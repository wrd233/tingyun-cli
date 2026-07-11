from __future__ import annotations

from typing import Any, Dict, List, Mapping

from .source_normalization import classify_exception_signal


def adapt_evidence(evidence: Any, view: str) -> Any:
    """Expose bounded primitive views without mutating Runs or making HTTP calls."""
    if view == "candidate_items":
        if isinstance(evidence, list):
            return [dict(item) for item in evidence if isinstance(item, Mapping)]
        data = evidence.get("data") if isinstance(evidence, Mapping) else None
        items = data.get("items") if isinstance(data, Mapping) else evidence.get("items") if isinstance(evidence, Mapping) else None
        if not isinstance(items, list):
            raise ValueError("candidate evidence must contain data.items")
        return [dict(item) for item in items if isinstance(item, Mapping)]
    if view == "performance_windows":
        return _performance_windows(evidence)
    if view == "error_events":
        data = evidence.get("data") if isinstance(evidence, Mapping) else None
        events = data.get("exceptions") if isinstance(data, Mapping) else evidence
        if not isinstance(events, list):
            raise ValueError("trace evidence must contain data.exceptions")
        output = []
        for event in events:
            if isinstance(event, Mapping):
                normalized = dict(event)
                normalized["signal_type"] = classify_exception_signal(event)
                output.append(normalized)
        return output
    if view == "call_tree":
        data = evidence.get("data") if isinstance(evidence, Mapping) else None
        call_tree = data.get("call_tree") if isinstance(data, Mapping) else evidence
        if not isinstance(call_tree, Mapping):
            raise ValueError("call tree evidence must contain data.call_tree")
        return _call_tree(call_tree, evidence)
    raise ValueError(f"unsupported Evidence Envelope view: {view}")


def _performance_windows(evidence: Any) -> List[Dict[str, Any]]:
    if isinstance(evidence, list):
        return [dict(item) for item in evidence if isinstance(item, Mapping)]
    if not isinstance(evidence, Mapping):
        raise ValueError("performance evidence must be an object")
    data = evidence.get("data")
    metrics = data.get("metrics") if isinstance(data, Mapping) else None
    if not isinstance(metrics, Mapping):
        raise ValueError("performance evidence must contain data.metrics")
    selected = None
    for name in ("p99", "p95", "response_avg"):
        metric = metrics.get(name)
        if isinstance(metric, Mapping) and isinstance(metric.get("series"), list):
            selected = (name, metric)
            break
    if selected is None:
        raise ValueError("performance evidence has no supported series")
    name, metric = selected
    points = [point for point in metric["series"] if isinstance(point, Mapping) and point.get("timestamp") is not None]
    source_refs = list(evidence.get("derived_from") or [])
    windows = []
    for index, point in enumerate(points):
        start = point["timestamp"]
        end = points[index + 1]["timestamp"] if index + 1 < len(points) else start + 60_000
        windows.append({"from": start, "to": end, "reported_max_metric": point.get("value"), name: point.get("value"), "source_refs": source_refs})
    return windows


def _call_tree(call_tree: Mapping[str, Any], evidence: Any) -> Dict[str, Any]:
    """Translate Tingyun treeNode/nodeMap into the generic recursive tree view."""
    roots = call_tree.get("treeNode")
    node_map = call_tree.get("nodeMap")
    if not isinstance(roots, list) or not isinstance(node_map, Mapping):
        return dict(call_tree)

    def expand(ref: Mapping[str, Any]) -> Dict[str, Any]:
        node_id = ref.get("id")
        details = node_map.get(node_id, {}) if node_id is not None else {}
        details = details if isinstance(details, Mapping) else {}
        total_time = details.get("totalTime")
        node = {
            "id": node_id,
            "name": details.get("metricName") or ref.get("metricName") or ref.get("method") or "<unnamed>",
            "duration_ms": total_time,
            "metric_type": details.get("metricType") or ref.get("metricType"),
            "children": [expand(child) for child in (ref.get("child") or []) if isinstance(child, Mapping)],
        }
        for field in ("exclTime", "sql", "param"):
            if field in details:
                node[field] = details[field]
        return node

    expanded_roots = [expand(root) for root in roots if isinstance(root, Mapping)]
    if len(expanded_roots) == 1:
        output = expanded_roots[0]
    else:
        output = {"name": "<synthetic-root>", "children": expanded_roots}
    output["treeNode"] = list(roots)
    output["nodeMap"] = dict(node_map)
    if isinstance(evidence, Mapping):
        output["source_refs"] = list(evidence.get("derived_from") or evidence.get("source_refs") or [])
    return output
