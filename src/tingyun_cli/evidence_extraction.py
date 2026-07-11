from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple


def extract_call_tree(call_tree: Mapping[str, Any], *, evidence_ref: str) -> Dict[str, Any]:
    spans, non_leaf_ids = _flatten_call_tree(call_tree, evidence_ref=evidence_ref)
    leaves = [span for span in spans if span["node_id"] not in non_leaf_ids]
    ranked = sorted(spans, key=_rank_key, reverse=True)
    leaf_ranked = sorted(leaves, key=_rank_key, reverse=True)
    database = [span for span in spans if _is_database(span)]
    http = [span for span in spans if _is_http(span)]
    dubbo = [span for span in spans if _is_dubbo(span)]
    redis = [span for span in spans if _is_redis(span)]
    errors = [span for span in spans if span.get("error") or _status_is_error(span.get("status"))]
    exceptions = [span for span in spans if span.get("exception") or span.get("stack_info")]
    logged = [span for span in spans if span.get("signal_type") in {"LOGGED_ERROR_EVENT", "ERROR_FLAG_FALSE_LOG_EVENT"}]
    return {
        "schema_version": 1,
        "root": spans[0] if spans else None,
        "major_downstream_spans": [span for span in ranked if span.get("depth", 0) > 0][:20],
        "database_spans": sorted(database, key=_rank_key, reverse=True),
        "http_spans": sorted(http, key=_rank_key, reverse=True),
        "dubbo_spans": sorted(dubbo, key=_rank_key, reverse=True),
        "redis_spans": sorted(redis, key=_rank_key, reverse=True),
        "top_exclusive_leaf_spans": leaf_ranked[:20],
        "error_nodes": errors,
        "exception_nodes": exceptions,
        "logged_error_events": logged,
        "all_spans": spans,
    }


def _flatten_call_tree(call_tree: Mapping[str, Any], *, evidence_ref: str) -> Tuple[List[Dict[str, Any]], set]:
    node_map = call_tree.get("nodeMap") if isinstance(call_tree.get("nodeMap"), Mapping) else {}
    roots = call_tree.get("treeNode")
    if isinstance(roots, Mapping):
        roots = [roots]
    if not isinstance(roots, list):
        roots = [call_tree]
    spans: List[Dict[str, Any]] = []
    non_leaf_ids = set()

    def visit(node: Mapping[str, Any], parent: Optional[str], depth: int) -> None:
        node_id = str(node.get("id") or node.get("nodeId") or f"synthetic-node-{len(spans)+1:04d}")
        detail = node_map.get(node_id) if isinstance(node_map.get(node_id), Mapping) else {}
        merged = {**dict(node), **dict(detail)}
        children = merged.get("child") if isinstance(merged.get("child"), list) else merged.get("children") if isinstance(merged.get("children"), list) else []
        exclusive = _number(merged.get("exclTime") if merged.get("exclTime") is not None else merged.get("exclusive_time"))
        total = _number(merged.get("totalTime") if merged.get("totalTime") is not None else merged.get("duration_ms") if merged.get("duration_ms") is not None else merged.get("total_time"))
        metric_type = str(merged.get("metricType") or merged.get("type") or "UNKNOWN")
        param = merged.get("param") if isinstance(merged.get("param"), Mapping) else {}
        span = {
            "node_id": node_id,
            "type": metric_type,
            "name": str(merged.get("metricName") or merged.get("name") or merged.get("method") or node_id),
            "total_time": total,
            "exclusive_time": exclusive,
            "parent": parent,
            "depth": depth,
            "evidence_ref": evidence_ref,
            "overlap_warning": exclusive is None and total is not None,
        }
        optional = {
            "method": merged.get("method"),
            "sql": merged.get("sql"),
            "vendor": param.get("vendor") or merged.get("vendor"),
            "protocol": param.get("protocol") or merged.get("protocol"),
            "operation": param.get("operation") or merged.get("operation"),
            "status": merged.get("status") or param.get("statusCode"),
            "error": merged.get("error") or merged.get("abnormal"),
            "exception": merged.get("exception") or merged.get("abnormal"),
            "stack_info": merged.get("stackInfo") or merged.get("stack"),
            "signal_type": merged.get("signal_type"),
        }
        span.update({key: value for key, value in optional.items() if value not in (None, "", [], {})})
        spans.append(span)
        if children:
            non_leaf_ids.add(node_id)
        for child in children:
            if isinstance(child, Mapping):
                visit(child, node_id, depth + 1)

    for root in roots:
        if isinstance(root, Mapping):
            visit(root, None, 0)
    return spans, non_leaf_ids


def _rank_key(span: Mapping[str, Any]):
    value = span.get("exclusive_time")
    if value is None:
        value = span.get("total_time")
    return (float(value or 0), str(span.get("node_id")))


def _is_database(span: Mapping[str, Any]) -> bool:
    text = " ".join(str(span.get(key) or "") for key in ("type", "name", "vendor")).lower()
    return any(token in text for token in ("database", "sql", "oracle", "postgres", "mysql"))


def _is_http(span: Mapping[str, Any]) -> bool:
    text = " ".join(str(span.get(key) or "") for key in ("type", "name", "protocol")).lower()
    return "external" in text or "http" in text


def _is_dubbo(span: Mapping[str, Any]) -> bool:
    return "dubbo" in (str(span.get("type") or "") + " " + str(span.get("name") or "")).lower()


def _is_redis(span: Mapping[str, Any]) -> bool:
    return "redis" in (str(span.get("type") or "") + " " + str(span.get("name") or "")).lower()


def _status_is_error(status: Any) -> bool:
    try:
        return int(status) >= 400
    except (TypeError, ValueError):
        return False


def _number(value: Any) -> Optional[float]:
    if isinstance(value, Mapping):
        value = value.get("value")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
