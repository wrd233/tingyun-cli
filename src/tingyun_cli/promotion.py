from __future__ import annotations

from typing import Any, Dict


def promotion_matrix() -> Dict[str, Dict[str, Any]]:
    rows = [
        _core("read_response_timeseries", "ep_post_server_api_application_charts_response"),
        _advanced("read_error_timeseries", "ep_post_server_api_application_charts_error"),
        _advanced("read_throughput_timeseries", "ep_post_server_api_application_charts_throught"),
        _advanced("list_alarm_events", "ep_post_nalarm_api_event_tracelist"),
        _advanced("read_alarm_event_detail", "ep_post_nalarm_api_event_trace"),
        _advanced("read_alarm_metric_series", "ep_post_nalarm_api_event_metric_chart"),
        _advanced("read_application_overview", "ep_post_server_api_graph_information"),
        _advanced("list_recent_request_response", "ep_post_server_api_webaction_list_responselist"),
        _advanced("list_recent_request_error", "ep_post_server_api_webaction_list_errorlist", lineage="NOT_INHERITED"),
        _advanced("list_recent_request_throughput", "ep_post_server_api_webaction_list_throughtlist", lineage="NOT_INHERITED"),
        _advanced("list_external_calls", "ep_post_server_api_application_ext_urilist"),
        _advanced("list_trace_exceptions", "ep_post_server_api_action_trace_detail_exceptions"),
        _research("list_component_operations", "uneven DB/NoSQL/MQ evidence depth", safety="READ"),
        _research("overview.max", "unit and aggregation semantics are not confirmed", safety="READ"),
        _rejected("manage_alarm_rules", "Tingyun mutation is forbidden", safety="WRITE"),
    ]
    return {row["capability"]: row for row in rows}


def _core(capability: str, endpoint_id: str) -> Dict[str, Any]:
    return {"capability": capability, "runtime_status": "CORE_LIVE_VALIDATED", "promotion_status": "SUPERSEDED_BY_MAIN", "endpoint_id": endpoint_id, "access": "READ"}


def _advanced(capability: str, endpoint_id: str, *, lineage: str = "SCOPED") -> Dict[str, Any]:
    return {"capability": capability, "runtime_status": "ADVANCED_READ_ONLY", "promotion_status": "PORTED_ADVANCED_READ_ONLY", "endpoint_id": endpoint_id, "access": "READ", "verification": "EXISTING_PROTOCOL_EVIDENCE", "lineage": lineage}


def _research(capability: str, reason: str, *, safety: str) -> Dict[str, Any]:
    return {"capability": capability, "runtime_status": "RESEARCH_ONLY", "promotion_status": "PORTED_RESEARCH_ONLY", "reason": reason, "access": safety}


def _rejected(capability: str, reason: str, *, safety: str) -> Dict[str, Any]:
    return {"capability": capability, "runtime_status": "REJECTED", "promotion_status": "REJECTED_WITH_REASON", "reason": reason, "access": safety}
