from __future__ import annotations

import json
import operator
from pathlib import Path
from typing import Any, Dict, List


ALLOWED_CANDIDATE_METRICS = {
    "response_avg",
    "p50",
    "p75",
    "p95",
    "p99",
    "throughput",
    "total_count",
    "error_rate",
    "error_count",
    "slow_count",
    "exception_count",
    "apdex",
}

_FIELD_TO_METRIC = {
    "responseTimeMillisecondAvg": ("response_avg", "ms"),
    "responseP50": ("p50", "ms"),
    "responseP75": ("p75", "ms"),
    "responseP95": ("p95", "ms"),
    "responseP99": ("p99", "ms"),
    "throughput": ("throughput", "per_second"),
    "totalCount": ("total_count", "count"),
    "errorRate": ("error_rate", "percent"),
    "errorTotalCount": ("error_count", "count"),
    "slowCount": ("slow_count", "count"),
    "exceptionCountTotal": ("exception_count", "count"),
    "apdex": ("apdex", "score"),
}


def normalize_candidates(
    *,
    response: Dict[str, Any],
    source_run_id: str,
    scope: Dict[str, Any],
    time_context: Dict[str, Any],
    raw_ref: str,
) -> Dict[str, Any]:
    rows = _extract_rows(response)
    items = [_candidate_item(index + 1, row, source_run_id, scope, raw_ref) for index, row in enumerate(rows)]
    return {
        "schema_version": 1,
        "kind": "candidates",
        "status": "SUCCESS" if rows else "EMPTY",
        "scope": scope,
        "time_context": time_context,
        "derived_from": [raw_ref],
        "data": {
            "source": {
                "endpoint": "POST /server-api/graph/query/overview?request_overview",
                "source_format": "json",
            },
            "row_count": len(rows),
            "completeness": _completeness(response, len(rows)),
            "items": items,
        },
    }


def inspect_candidates_all(run_path: Path) -> Dict[str, Any]:
    artifact = _load_candidates(run_path)
    return {
        "schema_version": 1,
        "run_id": Path(run_path).name,
        "items": artifact["data"]["items"],
    }


def inspect_candidates_top(run_path: Path, *, metric: str, limit: int) -> Dict[str, Any]:
    _validate_metric(metric)
    artifact = _load_candidates(run_path)
    _ensure_metric_available(artifact["data"]["items"], metric)
    items = sorted(
        artifact["data"]["items"],
        key=lambda item: _metric_value(item, metric),
        reverse=True,
    )
    return {"schema_version": 1, "run_id": Path(run_path).name, "metric": metric, "items": items[:limit]}


def inspect_candidates_filter(run_path: Path, *, metric: str, operator: str, value: float) -> Dict[str, Any]:
    _validate_metric(metric)
    ops = {
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    if operator not in ops:
        raise ValueError(f"unsupported operator: {operator}")
    artifact = _load_candidates(run_path)
    _ensure_metric_available(artifact["data"]["items"], metric)
    items = [item for item in artifact["data"]["items"] if ops[operator](_metric_value(item, metric), value)]
    return {"schema_version": 1, "run_id": Path(run_path).name, "metric": metric, "operator": operator, "value": value, "items": items}


_PROVEN_TRACE_REQUEST_TYPES = {"WEB", "TX", "BG"}
_PROVEN_URL_REQUEST_TYPES = {"WEB", "TX", "BG"}


def _split_request_types(request_type: str):
    return [t.strip() for t in request_type.split(",") if t.strip()]


def _first_proven_type(request_type: str, proven: set) -> str:
    for t in _split_request_types(request_type):
        if t in proven:
            return t
    return ""


def _candidate_item(index: int, row: Dict[str, Any], source_run_id: str, scope: Dict[str, Any], raw_ref: str) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "item_ref": f"item-{index:04d}",
        "source_run_id": source_run_id,
        "kind": "candidate",
        "name": row.get("actionName") or row.get("name") or "",
        "labels": {
            "applicationName": row.get("applicationName"),
            "requestType": row.get("requestType"),
        },
        "metrics": _metrics(row),
        "wire_identity": _wire_identity(row, scope),
        "source_refs": [raw_ref],
    }
    if is_investigate_trace_eligible(item):
        item["available_actions"] = ["investigate_trace"]
    if _is_url_eligible(item):
        item["links"] = [_candidate_detail_link(item["wire_identity"])]
        item["navigation"] = {"status": "SUCCESS", "verification": "DERIVED_FROM_VERIFIED_ROUTE"}
    else:
        item["navigation"] = {"status": "MISSING", "reason": "URL_NOT_VERIFIED"}
    return item


def is_investigate_trace_eligible(item: Dict[str, Any]) -> bool:
    identity = item.get("wire_identity", {})
    if not all(identity.get(field) not in (None, "") for field in ("bizSystemId", "applicationId", "actionId", "requestType")):
        return False
    request_type = identity.get("requestType", "")
    if request_type in _PROVEN_TRACE_REQUEST_TYPES:
        return True
    return bool(_first_proven_type(request_type, _PROVEN_TRACE_REQUEST_TYPES))


def _is_url_eligible(item: Dict[str, Any]) -> bool:
    identity = item.get("wire_identity", {})
    if not all(identity.get(field) not in (None, "") for field in ("bizSystemId", "applicationId", "actionId")):
        return False
    request_type = identity.get("requestType", "")
    if request_type in _PROVEN_URL_REQUEST_TYPES:
        return True
    return bool(_first_proven_type(request_type, _PROVEN_URL_REQUEST_TYPES))


def is_inspect_call_tree_eligible(item: Dict[str, Any]) -> bool:
    identity = item.get("wire_identity", {})
    return all(identity.get(field) not in (None, "") for field in ("bizSystemId", "applicationId", "actionGuid", "traceId"))


def _candidate_detail_link(identity: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rel": "detail",
        "url": f"/web/server/action/overview/{identity['bizSystemId']}/{identity['applicationId']}/{identity['actionId']}",
        "verification": "DERIVED_FROM_VERIFIED_ROUTE",
        "route_id": "web_server_action_overview",
    }


def _metrics(row: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    metrics: Dict[str, Dict[str, Any]] = {}
    for field, (metric, unit) in _FIELD_TO_METRIC.items():
        if field in row and row[field] is not None:
            metrics[metric] = {"value": row[field], "unit": unit}
    return metrics


def _wire_identity(row: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:
    identity: Dict[str, Any] = {}
    for field in ("actionId", "applicationId", "systemId", "requestType"):
        if row.get(field) not in (None, ""):
            identity[field] = row[field]
    if scope.get("bizSystemId") not in (None, ""):
        identity["bizSystemId"] = scope["bizSystemId"]
    return identity


def _extract_rows(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = response.get("data", [])
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ("content", "items", "rows", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _completeness(response: Dict[str, Any], row_count: int) -> str:
    data = response.get("data")
    total = data.get("total") if isinstance(data, dict) else response.get("total")
    if isinstance(total, int) and row_count >= total:
        return "FULL"
    if row_count >= 1000:
        return "BOUNDED"
    return "UNKNOWN"


def _load_candidates(run_path: Path) -> Dict[str, Any]:
    return json.loads((Path(run_path) / "evidence" / "candidates.json").read_text(encoding="utf-8"))


def _validate_metric(metric: str) -> None:
    if metric not in ALLOWED_CANDIDATE_METRICS:
        raise ValueError(f"unsupported metric: {metric}")


def _ensure_metric_available(items: List[Dict[str, Any]], metric: str) -> None:
    if items and all(metric not in item.get("metrics", {}) for item in items):
        raise ValueError(f"unavailable metric: {metric}")


def _metric_value(item: Dict[str, Any], metric: str) -> float:
    value = item.get("metrics", {}).get(metric, {}).get("value")
    if value is None:
        return float("-inf")
    return float(value)
