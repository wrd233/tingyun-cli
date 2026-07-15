from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from .candidates import is_inspect_call_tree_eligible, resolve_verified_trace_action_type


def action_contracts_for_item(item: Mapping[str, Any], *, source_run_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Describe executable next actions and withheld branches for one Evidence Item."""
    source_run_id = source_run_id or item.get("source_run_id")
    item_ref = item.get("item_ref")
    action_input = {"source_run_id": source_run_id, "source_item_ref": item_ref}
    kind = str(item.get("kind") or item.get("item_type") or "")
    identity = item.get("wire_identity") if isinstance(item.get("wire_identity"), Mapping) else {}
    available: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []

    if kind == "candidate":
        required = ["bizSystemId", "applicationId", "actionId", "requestType"]
        missing = _missing(identity, required)
        action_type = resolve_verified_trace_action_type(
            str(item.get("semantic_kind") or ""), str(identity.get("requestType") or "")
        )
        if not missing and action_type:
            available.append(_available("investigate_trace", "CORE_LIVE", action_input))
        else:
            reason = "ACTION_IDENTITY_INCOMPLETE" if missing else "UNRESOLVED_TRACE_ACTION_TYPE"
            blocked.append(_blocked("investigate_trace", "CORE_LIVE", action_input, reason, missing))
    elif kind == "trace":
        required = ["bizSystemId", "applicationId", "actionGuid", "traceId"]
        missing = _missing(identity, required)
        if is_inspect_call_tree_eligible(dict(item)):
            available.append(_available("inspect_call_tree", "CORE_LIVE", action_input))
        else:
            blocked.append(_blocked("inspect_call_tree", "CORE_LIVE", action_input, "ACTION_IDENTITY_INCOMPLETE", missing))
    elif kind == "trace_tree_node":
        required = ["bizSystemId", "treeId", "traceId", "queryTimestamp"]
        missing = _missing(identity, required)
        for action in ("source_trace_exceptions", "source_trace_stack"):
            if not missing:
                available.append(_available(action, "ADVANCED_READ_ONLY", action_input))
            else:
                blocked.append(_blocked(action, "ADVANCED_READ_ONLY", action_input, "SOURCE_IDENTITY_INCOMPLETE", missing))
    elif kind == "alarm_event":
        missing = _missing(identity, ["alarmEventId"])
        if not missing:
            available.append(_available("source_alarm_detail", "ADVANCED_READ_ONLY", action_input))
        else:
            blocked.append(_blocked("source_alarm_detail", "ADVANCED_READ_ONLY", action_input, "SOURCE_IDENTITY_INCOMPLETE", missing))
    elif kind == "alarm_detail":
        metric_fields = ["alarmEventId", "metric", "codeIndex", "policyId", "policyCheckMode", "product", "targetType", "eventItems"]
        metric_missing = _missing(identity, metric_fields)
        if not metric_missing:
            available.append(_available("source_alarm_metric_series", "ADVANCED_READ_ONLY", action_input))
        else:
            blocked.append(_blocked("source_alarm_metric_series", "ADVANCED_READ_ONLY", action_input, "SOURCE_IDENTITY_INCOMPLETE", metric_missing))
        trace_missing = _missing(identity, ["bizSystemId", "applicationId", "actionId", "requestType"])
        blocked.append(_blocked("investigate_trace", "CORE_LIVE", action_input, "TRACE_CANDIDATE_REQUIRED", trace_missing))

    return {
        "available_actions": [row["action"] for row in available],
        "action_contracts": available,
        "action_blockers": blocked,
    }


def apply_action_contracts(item: Dict[str, Any], *, source_run_id: Optional[str] = None) -> Dict[str, Any]:
    contracts = action_contracts_for_item(item, source_run_id=source_run_id)
    if contracts["available_actions"]:
        item["available_actions"] = contracts["available_actions"]
    else:
        item.pop("available_actions", None)
    item["action_contracts"] = contracts["action_contracts"]
    item["action_blockers"] = contracts["action_blockers"]
    return item


def _available(action: str, surface: str, action_input: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "action": action,
        "surface": surface,
        "status": "AVAILABLE",
        "logical_request_budget": 1,
        "cli": _cli_invocation(action),
        "input": dict(action_input),
    }


def _blocked(action: str, surface: str, action_input: Mapping[str, Any], reason: str, missing: List[str]) -> Dict[str, Any]:
    return {
        "action": action,
        "surface": surface,
        "status": "BLOCKED",
        "reason_code": reason,
        "missing_identity_fields": missing,
        "cli": _cli_invocation(action),
        "input": dict(action_input),
    }


def _missing(identity: Mapping[str, Any], fields: List[str]) -> List[str]:
    return [field for field in fields if identity.get(field) in (None, "", [])]


def _cli_invocation(action: str) -> Dict[str, str]:
    if action in {"investigate_trace", "inspect_call_tree"}:
        return {"command": "investigate", "action": action}
    capability = {
        "source_alarm_detail": "alarm-detail",
        "source_alarm_metric_series": "alarm-metric-series",
        "source_trace_exceptions": "trace-exceptions",
        "source_trace_stack": "trace-stack",
    }.get(action)
    return {"command": "source", "capability": capability or action}
