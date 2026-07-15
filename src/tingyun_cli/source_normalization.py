from __future__ import annotations

from typing import Any, Dict, List, Mapping, Tuple

from .candidates import candidate_semantic_kind
from .action_contracts import apply_action_contracts


def normalize_source(kind: str, response: Mapping[str, Any], source: Mapping[str, Any], *, run_id: str, raw_ref: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _extract_rows(response)
    if kind == "alarm_events":
        return _alarm_events(rows, source, run_id, raw_ref), {"completeness": _bounded_completeness(response, len(rows))}
    if kind == "alarm_detail":
        return _alarm_detail(rows, source, run_id, raw_ref), {}
    if kind == "recent_requests":
        return _recent_requests(rows, source, run_id, raw_ref), {"completeness": _bounded_completeness(response, len(rows))}
    if kind == "instance_context":
        nodes = _graph_nodes(response)
        items = _instances(nodes, source, run_id, raw_ref)
        return items, {"instance_count": len(items), "node_count": len(nodes), "completeness": "UNKNOWN"}
    if kind == "external_calls":
        return _external(rows, source, run_id, raw_ref), {"completeness": _bounded_completeness(response, len(rows))}
    if kind == "trace_exceptions":
        return _exceptions(rows, source, run_id, raw_ref), {"completeness": _bounded_completeness(response, len(rows))}
    if kind == "trace_stack":
        frames = response.get("data")
        if not isinstance(frames, list) or not all(isinstance(frame, str) for frame in frames):
            return [], {
                "completeness": "UNKNOWN",
                "protocol_mismatch": {
                    "reason_code": "PROTOCOL_SHAPE_MISMATCH",
                    "expected": "data: array[string]",
                    "actual_data_type": type(frames).__name__,
                },
            }
        items = _trace_stack(response, source, run_id, raw_ref)
        return items, {"completeness": "BOUNDED" if items else "UNKNOWN"}
    if kind in {"performance_error_series", "performance_throughput_series", "alarm_metric_series"}:
        series = _series(response)
        metric = source.get("metric")
        unit = source.get("unit")
        items = [{"item_ref": f"series-point-{index:04d}", "item_type": "metric_series_point", "source_run_id": run_id, "source_refs": [raw_ref], **dict(point)} for index, point in enumerate(series, 1)]
        return items, {"metric": {"semantic": metric, "unit": unit, "aggregation": source.get("aggregation", "series"), "semantic_status": source.get("semantic_status", "UNKNOWN")}, "completeness": "BOUNDED" if items else "UNKNOWN"}
    return [], {"completeness": "UNKNOWN"}


def _alarm_events(rows, source, run_id, raw_ref):
    items = []
    for index, row in enumerate(rows, 1):
        alarm_id = row.get("id") or row.get("eventId") or row.get("eventTraceId")
        parent = _parent_group(row.get("parentGroup"))
        business_id = parent.get("$biz_system_id") or parent.get("bizSystemId")
        application_id = parent.get("$application_id") or parent.get("applicationId")
        items.append(apply_action_contracts({"item_ref": f"alarm-event-{index:04d}", "item_type": "alarm_event", "kind": "alarm_event", "name": _target_name(row, alarm_id), "source_run_id": run_id, "source_refs": [raw_ref], "scope": {"type": "alarm", "alarm_id": alarm_id}, "source": {"capability": source["capability"]}, "identity": {"alarm_id": alarm_id, "business_system_id": business_id, "application_id": application_id}, "wire_identity": {"alarmEventId": alarm_id, "bizSystemId": business_id, "applicationId": application_id}}))
    return items


def _alarm_detail(rows, source, run_id, raw_ref):
    items = []
    item_index = 0
    for row in rows:
        parent = _parent_group(row.get("parentGroup"))
        alarm_id = row.get("id") or source.get("alarm_id")
        business_id = parent.get("$biz_system_id") or parent.get("bizSystemId") or source.get("business_system_id")
        application_id = parent.get("$application_id") or parent.get("applicationId") or source.get("application_id")
        event_items = row.get("eventItems") or row.get("alarmEventItems") or []
        event_trace_ids = [item.get("eventTraceId") for item in event_items if isinstance(item, Mapping) and item.get("eventTraceId") not in (None, "")]
        target = row.get("target") if isinstance(row.get("target"), Mapping) else {}
        metrics = [metric for metric in row.get("metrics", []) if isinstance(metric, Mapping)] or [row]
        for metric in metrics:
            item_index += 1
            wire = {"alarmEventId": alarm_id, "bizSystemId": business_id, "applicationId": application_id}
            for field in ("metric", "codeIndex"):
                if metric.get(field) not in (None, ""):
                    wire[field] = metric[field]
            for field in ("policyId", "policyCheckMode", "product"):
                if row.get(field) not in (None, ""):
                    wire[field] = row[field]
            if target.get("key") not in (None, ""):
                wire["targetType"] = target["key"]
            elif row.get("targetType") not in (None, ""):
                wire["targetType"] = row["targetType"]
            if target.get("key") == "$$transaction" and target.get("value") not in (None, ""):
                wire["actionId"] = target["value"]
            if event_items:
                wire["eventItems"] = event_items
            items.append(apply_action_contracts({"item_ref": f"alarm-detail-{item_index:04d}", "item_type": "alarm_detail", "kind": "alarm_detail", "name": _target_name(row, alarm_id), "source_run_id": run_id, "source_refs": [raw_ref], "scope": {"type": "alarm", "alarm_id": alarm_id}, "source": {"capability": source["capability"]}, "identity": {"alarm_id": alarm_id, "business_system_id": business_id, "application_id": application_id, "action_id": wire.get("actionId"), "event_trace_ids": event_trace_ids}, "wire_identity": wire}))
    return items


def _recent_requests(rows, source, run_id, raw_ref):
    items = []
    for index, row in enumerate(rows, 1):
        identity = {field: row[field] for field in ("applicationId", "actionId", "systemId", "requestType") if row.get(field) not in (None, "")}
        identity["bizSystemId"] = source["business_system_id"]
        name = row.get("actionName") or row.get("name") or ""
        semantic_kind = candidate_semantic_kind(str(name), str(row.get("requestType") or ""))
        metrics = _candidate_metrics(row, source["ranking"])
        ranking_metric = {"response": ("ranking_response", "response"), "error": ("ranking_error", "error"), "throughput": ("ranking_throughput", "throught")}[source["ranking"]]
        ranking_value = metrics.get(ranking_metric[0], {}).get("value")
        selection_provenance = {"strategy": f"{source['ranking']}_rank", "rank": index, "candidate_count": len(rows)}
        if ranking_value is not None:
            selection_provenance.update({"ranking_value": ranking_value, "wire_field": ranking_metric[1]})
        item = {"item_ref": f"request-candidate-{index:04d}", "item_type": "request_candidate", "kind": "candidate", "name": name, "semantic_kind": semantic_kind, "source_run_id": run_id, "source_refs": [raw_ref], "labels": {"applicationName": row.get("applicationName"), "requestType": row.get("requestType")}, "scope": _recent_scope(identity), "source": {"capability": source["capability"], "ranking": source["ranking"]}, "selection_provenance": selection_provenance, "metrics": metrics, "identity": _friendly_identity(identity), "wire_identity": identity}
        apply_action_contracts(item)
        if source["ranking"] != "response":
            item["available_actions"] = []
            item["action_contracts"] = []
            item["action_blockers"] = [{**blocker, "reason_code": "RANKING_LINEAGE_NOT_INHERITED"} for blocker in item["action_blockers"]] or [{"action": "investigate_trace", "surface": "CORE_LIVE", "status": "BLOCKED", "reason_code": "RANKING_LINEAGE_NOT_INHERITED", "missing_identity_fields": [], "cli": {"command": "investigate", "action": "investigate_trace"}, "input": {"source_run_id": run_id, "source_item_ref": item["item_ref"]}}]
        items.append(item)
    return items


def _instances(nodes, source, run_id, raw_ref):
    items = []
    for node in nodes:
        node_type = str(node.get("type") or node.get("nodeType") or "").upper()
        if "INSTANCE" not in node_type and not any(node.get(field) not in (None, "") for field in ("instanceId", "serverName", "agentId")):
            continue
        instance_id = node.get("instanceId") or node.get("id")
        items.append({"item_ref": f"instance-{len(items)+1:04d}", "item_type": "instance", "kind": "instance", "name": node.get("name") or str(instance_id), "source_run_id": run_id, "source_refs": [raw_ref], "scope": {"type": "instance", "business_system_id": source["business_system_id"], "application_id": source["application_id"], "instance_id": instance_id}, "source": {"capability": source["capability"]}, "identity": {"business_system_id": source["business_system_id"], "application_id": source["application_id"], "instance_id": instance_id}, "wire_identity": {"bizSystemId": source["business_system_id"], "applicationId": source["application_id"], "instanceId": instance_id}, "available_actions": []})
    return items


def _external(rows, source, run_id, raw_ref):
    items = []
    for index, row in enumerate(rows, 1):
        name = row.get("name") or row.get("text") or row.get("host") or row.get("domain") or row.get("value")
        dependency_uri = row.get("uri") or row.get("url") or row.get("value")
        dependency = name or dependency_uri
        items.append({"item_ref": f"external-dependency-{index:04d}", "item_type": "external_dependency", "kind": "external_dependency", "name": str(name or ""), "dependency_uri": dependency_uri, "source_run_id": run_id, "source_refs": [raw_ref], "scope": {"type": "external_dependency", "business_system_id": source["business_system_id"], "application_id": source["application_id"], "dependency": dependency}, "source": {"capability": source["capability"]}, "identity": {"business_system_id": source["business_system_id"], "application_id": source["application_id"], "dependency": dependency}, "wire_identity": {"text": row.get("text"), "value": row.get("value")}, "metrics": _external_metrics(row), "available_actions": []})
    return items


def _exceptions(rows, source, run_id, raw_ref):
    items = []
    for index, row in enumerate(rows, 1):
        exception_class = row.get("exceptionClass") or row.get("exception_class") or row.get("class") or row.get("type")
        items.append({"item_ref": f"trace-exception-{index:04d}", "item_type": "trace_exception", "kind": "trace_exception", "source_run_id": run_id, "source_refs": [raw_ref], "scope": {"type": "trace_node", "trace_id": source["trace_id"], "tree_id": source["tree_id"]}, "source": {"capability": source["capability"]}, "identity": {"business_system_id": source["business_system_id"], "trace_id": source["trace_id"], "tree_id": source["tree_id"], "query_timestamp": source["query_timestamp"], "exception_class": exception_class}, "message": row.get("message") or row.get("errorMessage") or row.get("msg"), "stack": row.get("stack") or [], "signal_type": classify_exception_signal(row), "wire_signal": dict(row), "available_actions": []})
    return items


def _trace_stack(response, source, run_id, raw_ref):
    frames = response.get("data")
    if not isinstance(frames, list) or not all(isinstance(frame, str) for frame in frames):
        return []
    return [{
        "item_ref": "trace-stack-0001",
        "item_type": "trace_stack",
        "kind": "trace_stack",
        "source_run_id": run_id,
        "source_refs": [raw_ref],
        "scope": {"type": "trace_node", "trace_id": source["trace_id"], "tree_id": source["tree_id"]},
        "source": {"capability": source["capability"]},
        "identity": {"business_system_id": source["business_system_id"], "trace_id": source["trace_id"], "tree_id": source["tree_id"], "query_timestamp": source["query_timestamp"]},
        "frames": list(frames),
        "frame_count": len(frames),
        "available_actions": [],
        "action_contracts": [],
        "action_blockers": [],
    }] if frames else []


def _extract_rows(response):
    data = response.get("data")
    if isinstance(data, list):
        return [dict(item) for item in data if isinstance(item, Mapping)]
    if isinstance(data, Mapping):
        for key in ("content", "items", "rows", "data"):
            if isinstance(data.get(key), list):
                return [dict(item) for item in data[key] if isinstance(item, Mapping)]
        return [dict(data)] if data else []
    return []


def _series(response):
    data = response.get("data")
    if isinstance(data, Mapping) and isinstance(data.get("series"), list):
        return [dict(point) for point in data["series"] if isinstance(point, Mapping)]
    chart = data.get("chart") if isinstance(data, Mapping) and isinstance(data.get("chart"), Mapping) else None
    if isinstance(chart, Mapping) and isinstance(chart.get("series"), list):
        points = []
        for series in chart["series"]:
            if not isinstance(series, Mapping):
                continue
            series_points = series.get("data") or series.get("points") or []
            if isinstance(series_points, list):
                for point in series_points:
                    if isinstance(point, Mapping):
                        points.append({"series_name": series.get("name"), **dict(point)})
            if not series_points:
                points.append(dict(series))
        return points
    return _extract_rows(response)


def _parent_group(value):
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, list):
        return {str(item["key"]): item.get("value") for item in value if isinstance(item, Mapping) and item.get("key") not in (None, "")}
    return {}


def _graph_nodes(response):
    data = response.get("data")
    return [dict(node) for node in data.get("nodes", []) if isinstance(node, Mapping)] if isinstance(data, Mapping) else []


def _target_name(row, fallback):
    target = row.get("target")
    return str(target.get("value") if isinstance(target, Mapping) else fallback)


def _recent_scope(identity):
    if identity.get("applicationId") and identity.get("actionId"):
        return {"type": "transaction", "business_system_id": identity.get("bizSystemId"), "application_id": identity.get("applicationId"), "action_id": identity.get("actionId")}
    return {"type": "business_system", "business_system_id": identity.get("bizSystemId")}


def _friendly_identity(identity):
    names = {"bizSystemId": "business_system_id", "applicationId": "application_id", "actionId": "action_id", "requestType": "request_type"}
    return {names[key]: value for key, value in identity.items() if key in names}


def _candidate_metrics(row, ranking):
    mapping = {"responseTimeMillisecondAvg": ("response_avg", "ms"), "responseP95": ("p95", "ms"), "responseP99": ("p99", "ms"), "throughput": ("throughput", "per_second"), "totalCount": ("total_count", "count"), "errorRate": ("error_rate", "percent"), "errorTotalCount": ("error_count", "count")}
    metrics = {metric: {"value": row[field], "unit": unit} for field, (metric, unit) in mapping.items() if row.get(field) is not None}
    ranking_fields = {"response": ("response", "ranking_response"), "error": ("error", "ranking_error"), "throughput": ("throught", "ranking_throughput")}
    wire_field, metric = ranking_fields[ranking]
    if row.get(wire_field) is not None:
        metrics[metric] = {"value": row[wire_field], "unit": "UNKNOWN", "semantic_status": "UNKNOWN", "wire_field": wire_field}
    return metrics


def classify_exception_signal(row: Mapping[str, Any]) -> str:
    stack = row.get("stack") or row.get("stackTrace") or row.get("stack_trace")
    exception_class = row.get("exceptionClass") or row.get("exception_class") or row.get("class")
    exception_object = row.get("exception")
    explicit_error = row.get("error")
    message = row.get("message") or row.get("errorMessage") or row.get("msg")
    signal_name = str(row.get("type") or row.get("name") or row.get("eventType") or "").lower()
    if explicit_error is False and message and not (exception_class or stack or exception_object):
        return "ERROR_FLAG_FALSE_LOG_EVENT"
    if exception_class or stack or exception_object or explicit_error is True:
        return "THROWN_EXCEPTION"
    if "logged error" in signal_name and message:
        return "LOGGED_ERROR_EVENT"
    return "UNKNOWN_EXCEPTION_SIGNAL"


def _external_metrics(row):
    mapping = {"callCount": ("call_count", "count"), "count": ("call_count", "count"), "errorCount": ("error_count", "count"), "errorTotalCount": ("error_count", "count"), "errorRate": ("error_rate", "percent"), "responseTimeMillisecondAvg": ("response_avg", "ms"), "avgResponseTime": ("response_avg", "ms"), "responseP95": ("p95", "ms"), "responseP99": ("p99", "ms")}
    metrics = {}
    for field, (metric, unit) in mapping.items():
        if row.get(field) is not None and metric not in metrics:
            metrics[metric] = {"value": row[field], "unit": unit}
    return metrics


def _bounded_completeness(response, count):
    data = response.get("data")
    total = data.get("totalElements", data.get("total")) if isinstance(data, Mapping) else None
    if isinstance(total, int) and count >= total:
        return "FULL"
    return "BOUNDED" if count else "UNKNOWN"
