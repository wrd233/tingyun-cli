from __future__ import annotations

from typing import Any, Dict, List, Mapping


def performance_timeseries_requests(biz_system_id: str, time_context: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [
        _business_chart_request("ep_post_server_api_application_charts_response", "/server-api/application/charts/response", biz_system_id, time_context, advanced=False),
        _business_chart_request("ep_post_server_api_application_charts_error", "/server-api/application/charts/error", biz_system_id, time_context),
        _business_chart_request("ep_post_server_api_application_charts_throught", "/server-api/application/charts/throught", biz_system_id, time_context),
    ]


def alarm_events_request(time_context: Mapping[str, Any], *, page_number: int = 1, page_size: int = 20) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return _advanced({"endpoint_id": "ep_post_nalarm_api_event_tracelist", "method": "POST", "path": "/nalarm-api/event/traceList", "body_kind": "form", "body": {"pageNumber": str(page_number), "pageSize": str(page_size), "timePeriod": str(endpoint["timePeriod"]), "endTime": endpoint["endTime"], "eventType": "", "frequent": "false", "lang": "zh_CN"}})


def alarm_event_detail_request(alarm_event_id: str, time_context: Mapping[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return _advanced({"endpoint_id": "ep_post_nalarm_api_event_trace", "method": "POST", "path": "/nalarm-api/event/trace", "body_kind": "form", "body": {"id": str(alarm_event_id), "timePeriod": str(endpoint["timePeriod"]), "endTime": endpoint["endTime"], "lang": "zh_CN"}})


def alarm_metric_series_request(identity: Mapping[str, Any], time_context: Mapping[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    body = {field: identity.get(field) for field in ("metric", "codeIndex", "policyId", "policyCheckMode", "product", "targetType", "eventItems")}
    body.update({"id": identity.get("alarmEventId") or identity.get("id"), "timePeriod": endpoint["timePeriod"], "endTime": endpoint["endTime"]})
    return _advanced({"endpoint_id": "ep_post_nalarm_api_event_metric_chart", "method": "POST", "path": "/nalarm-api/event/metric/chart", "body_kind": "json", "body": body})


def application_instances_request(biz_system_id: str, application_id: str, time_context: Mapping[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return _advanced({"endpoint_id": "ep_post_server_api_graph_information", "method": "POST", "path": "/server-api/graph/information", "body_kind": "form", "body": {"bizSystemId": biz_system_id, "applicationId": application_id, "timePeriod": str(endpoint["timePeriod"]), "endTime": endpoint["endTime"], "lang": "zh_CN"}})


def recent_request_ranking_request(biz_system_id: str, time_context: Mapping[str, Any], *, ranking: str) -> Dict[str, Any]:
    endpoints = {
        "response": ("ep_post_server_api_webaction_list_responselist", "/server-api/webaction/list/responseList"),
        "error": ("ep_post_server_api_webaction_list_errorlist", "/server-api/webaction/list/errorList"),
        "throughput": ("ep_post_server_api_webaction_list_throughtlist", "/server-api/webaction/list/throughtList"),
    }
    if ranking not in endpoints:
        raise ValueError("UNSUPPORTED_SOURCE_VARIANT")
    endpoint_id, path = endpoints[ranking]
    endpoint = time_context["endpoint"]
    return _advanced({"endpoint_id": endpoint_id, "variant_id": f"ranking_{ranking}", "method": "POST", "path": path, "body_kind": "form", "body": {"bizSystemId": biz_system_id, "timePeriod": str(endpoint["timePeriod"]), "endTime": endpoint["endTime"], "lang": "zh_CN"}})


def external_uri_request(biz_system_id: str, application_id: str, time_context: Mapping[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return _advanced({"endpoint_id": "ep_post_server_api_application_ext_urilist", "method": "POST", "path": "/server-api/application/ext/uriList", "body_kind": "form", "body": {"bizSystemId": biz_system_id, "applicationId": application_id, "timePeriod": str(endpoint["timePeriod"]), "endTime": endpoint["endTime"], "lang": "zh_CN"}})


def trace_exceptions_request(identity: Mapping[str, Any], time_context: Mapping[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return _advanced({"endpoint_id": "ep_post_server_api_action_trace_detail_exceptions", "method": "POST", "path": "/server-api/action/trace/detail/exceptions", "body_kind": "form", "body": {"treeId": identity.get("treeId"), "traceId": identity.get("traceId"), "bizSystemId": identity.get("bizSystemId"), "queryTimestamp": identity.get("queryTimestamp"), "timePeriod": str(endpoint["timePeriod"]), "endTime": endpoint["endTime"], "lang": "zh_CN"}})


def trace_stack_request(identity: Mapping[str, Any], time_context: Mapping[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return _advanced({"endpoint_id": "ep_post_server_api_action_trace_detail_stacktraces", "method": "POST", "path": "/server-api/action/trace/detail/stackTraces", "body_kind": "form", "body": {"treeId": identity.get("treeId"), "traceId": identity.get("traceId"), "bizSystemId": identity.get("bizSystemId"), "queryTimestamp": identity.get("queryTimestamp"), "timePeriod": str(endpoint["timePeriod"]), "endTime": endpoint["endTime"], "lang": "zh_CN"}})


def _business_chart_request(endpoint_id: str, path: str, biz_system_id: str, time_context: Mapping[str, Any], *, advanced: bool = True) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    request = {"endpoint_id": endpoint_id, "method": "POST", "path": path, "body_kind": "form", "body": {"bizSystemId": biz_system_id, "businessType": "BIZ_SYSTEM", "timePeriod": str(endpoint["timePeriod"]), "endTime": endpoint["endTime"], "lang": "zh_CN"}}
    return _advanced(request) if advanced else request


def _advanced(request: Dict[str, Any]) -> Dict[str, Any]:
    request["runtime_surface"] = "ADVANCED_SOURCE"
    return request
