from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from .candidates import resolve_verified_trace_action_type


def trace_candidates_from_rows(rows: Iterable[Mapping[str, Any]], *, scope: Mapping[str, Any], source: Mapping[str, Any], time_window: Mapping[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        trace_id = row.get("traceId") or row.get("trace_id") or row.get("id")
        duration = row.get("duration_ms")
        duration_metric = {"value": duration, "unit": "ms", "semantic_status": "VERIFIED"} if duration is not None else {"raw": {"field": "duration", "value": row.get("duration"), "unit": row.get("duration_unit")}, "semantic_status": "UNKNOWN"}
        wire_identity = _wire_identity(row, scope)
        item: Dict[str, Any] = {
            "item_ref": f"trace-candidate-{index:04d}",
            "item_type": "trace_candidate",
            "trace_id": str(trace_id) if trace_id is not None else None,
            "timestamp": row.get("timestamp") or row.get("time") or row.get("startTime"),
            "duration_ms": duration_metric,
            "error": bool(row.get("error") or row.get("hasError") or row.get("errorStatus")),
            "identity": {"trace_id": str(trace_id) if trace_id is not None else None, "instance_id": row.get("instanceId") or row.get("instance_id"), "action_id": row.get("actionId") or row.get("action_id")},
            "wire_identity": wire_identity,
            "scope": {"type": "trace", "trace_id": str(trace_id) if trace_id is not None else None},
            "parent_scope": dict(scope),
            "source": dict(source),
            "source_run_id": source.get("source_run_id"),
            "source_item_ref": source.get("source_item_ref"),
            "time_window": dict(time_window),
            "available_actions": [],
        }
        if _trace_action_eligible(wire_identity):
            item["available_actions"] = ["investigate_trace"]
        candidates.append(item)
    return candidates


def select_trace(candidates: List[Mapping[str, Any]], *, strategy: str, trace_id: Optional[str] = None) -> Dict[str, Any]:
    if not candidates:
        raise ValueError("no trace candidates")
    ranked = _rank(candidates, strategy=strategy, trace_id=trace_id)
    selected = dict(ranked[0])
    selected["selection"] = {"strategy": strategy, "ordering": _ordering(strategy), "tie_behavior": "trace_id_desc" if strategy in {"slowest", "error"} else "stable_string_order", "candidate_count": len(candidates), "rank": 1, "filters": _filters(selected, trace_id=trace_id), "source_dataset": {"source_run_id": selected.get("source_run_id"), "source_item_ref": selected.get("source_item_ref")}}
    return selected


def _rank(candidates: List[Mapping[str, Any]], *, strategy: str, trace_id: Optional[str]) -> List[Mapping[str, Any]]:
    if strategy == "slowest":
        return sorted(candidates, key=lambda item: (_duration(item), str(item.get("trace_id"))), reverse=True)
    if strategy == "error":
        errors = [item for item in candidates if item.get("error")]
        if not errors:
            raise ValueError("no error trace candidates")
        return sorted(errors, key=lambda item: (_duration(item), str(item.get("trace_id"))), reverse=True)
    if strategy == "exact":
        exact = [item for item in candidates if item.get("trace_id") == trace_id]
        if not exact:
            raise ValueError(f"trace not found: {trace_id}")
        return exact
    if strategy == "newest":
        return sorted(candidates, key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    if strategy == "oldest":
        return sorted(candidates, key=lambda item: str(item.get("timestamp") or ""))
    raise ValueError(f"unsupported trace selection strategy: {strategy}")


def _duration(item: Mapping[str, Any]) -> float:
    metric = item.get("duration_ms")
    return float(metric.get("value") or 0) if isinstance(metric, Mapping) else 0.0


def _ordering(strategy: str) -> str:
    return {"slowest": "duration_ms_desc", "error": "error_only_duration_ms_desc", "exact": "trace_id_exact", "newest": "timestamp_desc", "oldest": "timestamp_asc"}[strategy]


def _filters(selected: Mapping[str, Any], *, trace_id: Optional[str]) -> Dict[str, Any]:
    filters: Dict[str, Any] = {}
    if trace_id:
        filters["trace_id"] = trace_id
    if selected.get("parent_scope"):
        filters["scope"] = selected["parent_scope"]
    if selected.get("time_window"):
        filters["time_window"] = selected["time_window"]
    return filters


def _wire_identity(row: Mapping[str, Any], scope: Mapping[str, Any]) -> Dict[str, Any]:
    names = {"business_system_id": "bizSystemId", "application_id": "applicationId", "action_id": "actionId"}
    identity = {field: row[field] for field in ("bizSystemId", "applicationId", "actionId", "requestType") if row.get(field) not in (None, "")}
    for source_name, wire_name in names.items():
        if wire_name not in identity and scope.get(source_name) not in (None, ""):
            identity[wire_name] = scope[source_name]
    return identity


def _trace_action_eligible(identity: Mapping[str, Any]) -> bool:
    required = ("bizSystemId", "applicationId", "actionId", "requestType")
    return all(identity.get(field) not in (None, "") for field in required) and resolve_verified_trace_action_type(str(identity["requestType"])) is not None
