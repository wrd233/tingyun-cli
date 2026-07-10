from __future__ import annotations

from typing import Any, Dict, List, Mapping


def workflow_plan(workflow: str, *, source: Mapping[str, Any], max_live_requests: int) -> Dict[str, Any]:
    if workflow == "alarm_to_trace":
        identity = source.get("identity", {})
        if not (source.get("alarm_id") or identity.get("alarm_id") or identity.get("event_id")):
            return _blocked(workflow, source, max_live_requests, "MISSING_ALARM_IDENTITY")
        steps = [
            _advanced("list_alarm_events", "alarm-events"),
            _advanced("read_alarm_event_detail", "alarm-detail"),
            _advanced("read_alarm_metric_series", "alarm-metric-series", required=False),
            _research("affected_object_context", "resolve_action_context"),
            _advanced("trace_candidates", "recent-requests-response", required=False),
            _local("select_trace", selection={"strategy": "time_window_match"}, required=False),
        ]
    elif workflow == "slow_transaction":
        steps = [_advanced("trace_candidates", "recent-requests-response"), _local("select_trace", selection={"strategy": "slowest"}), _core("get_trace_detail", "investigate_trace"), _core("get_trace_call_tree", "inspect_call_tree"), _advanced("list_trace_exceptions", "trace-exceptions", required=False), _local("trace_diff", required=False)]
    elif workflow == "external_dependency_timeout":
        steps = [_advanced("list_external_calls", "external-calls"), _advanced("trace_candidates", "recent-requests-response"), _local("select_trace", selection={"strategy": "slowest"}), _core("get_trace_call_tree", "inspect_call_tree"), _local("trace_diff", required=False), _local("duration_cluster", rule="fixed_duration_cluster_candidate")]
    elif workflow == "instance_anomaly":
        steps = [_advanced("complete_instance_list", "application-instances"), _local("instance_compare"), _advanced("alarm_context", "alarm-events", required=False), _advanced("trace_candidates", "recent-requests-response", required=False)]
    elif workflow == "transaction_error":
        steps = [_advanced("recent_error_ranking", "recent-requests-error"), _local("error_triage"), _local("error_signature_cluster"), _local("select_trace", selection={"strategy": "error"}), _core("get_trace_detail", "investigate_trace"), _core("get_trace_call_tree", "inspect_call_tree", required=False)]
    else:
        raise ValueError(f"unsupported workflow: {workflow}")
    return _ready(workflow, source, max_live_requests, steps)


def _local(primitive: str, **values: Any) -> Dict[str, Any]:
    return {"primitive": primitive, "availability": "LOCAL_ONLY", "request_cost": 0, **values}


def _advanced(primitive: str, capability: str, **values: Any) -> Dict[str, Any]:
    return {"primitive": primitive, "source_capability": capability, "availability": "ADVANCED_READ_ONLY", "request_cost": 1, **values}


def _core(primitive: str, capability: str, **values: Any) -> Dict[str, Any]:
    return {"primitive": primitive, "source_capability": capability, "availability": "CORE_LIVE_VALIDATED", "request_cost": 1, **values}


def _research(primitive: str, capability: str) -> Dict[str, Any]:
    return {"primitive": primitive, "source_capability": capability, "availability": "RESEARCH_ONLY", "request_cost": 0, "required": False}


def _ready(workflow: str, source: Mapping[str, Any], max_live_requests: int, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    expected = sum(step["request_cost"] for step in steps)
    status = "READY" if expected <= max_live_requests else "BLOCKED"
    blockers = [] if status == "READY" else [{"reason_code": "REQUEST_BUDGET_EXCEEDED"}]
    return {"schema_version": 1, "workflow": workflow, "status": status, "source": dict(source), "expected_live_request_count": expected, "expected_logical_request_count": expected, "actual_request_count": 0, "request_budget": _budget(max_live_requests), "blockers": blockers, "steps": steps}


def _blocked(workflow: str, source: Mapping[str, Any], max_live_requests: int, reason: str) -> Dict[str, Any]:
    return {"schema_version": 1, "workflow": workflow, "status": "BLOCKED", "source": dict(source), "expected_live_request_count": 0, "expected_logical_request_count": 0, "actual_request_count": 0, "request_budget": _budget(max_live_requests), "blockers": [{"reason_code": reason}], "steps": []}


def _budget(max_live_requests: int) -> Dict[str, Any]:
    return {"max_live_requests": max_live_requests, "concurrency": 1, "max_narrowing_steps": 3}
