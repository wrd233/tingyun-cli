from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional


_STATIC_EXTENSIONS = (".ico", ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".map", ".xml", ".woff", ".woff2")


def classify_request_path(path: str) -> Dict[str, str]:
    lowered = path.lower().split("?", 1)[0]
    if lowered.endswith(_STATIC_EXTENSIONS):
        return {"class": "static_resource", "reason_code": "KNOWN_STATIC_EXTENSION"}
    if "/api/" in lowered or lowered.startswith("/api/") or "/v1/" in lowered:
        return {"class": "business_request", "reason_code": "API_PATH_PATTERN"}
    return {"class": "unknown", "reason_code": "NO_MATCHING_RULE"}


def cluster_error_signatures(events: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for event in events:
        grouped.setdefault(_signature(event), []).append(event)
    clusters = []
    for signature, members in grouped.items():
        representative = dict(members[0])
        representative["selection"] = {"strategy": "representative_signature", "ordering": "input_order", "candidate_count": len(members), "rank": 1}
        clusters.append({"signature": signature, "count": len(members), "representative": representative, "members": [dict(member) for member in members], "rule": "http_status|exception_class|action_id|normalized_message"})
    return sorted(clusters, key=lambda cluster: (-cluster["count"], cluster["signature"]))


def analyze_external_dependencies(events: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for event in events:
        grouped.setdefault(_dependency_name(event), []).append(event)
    dependencies = [_external_dependency_summary(name, members) for name, members in grouped.items()]
    return {"schema_version": 1, "analysis": "external_dependency", "actual_request_count": 0, "dependencies": sorted(dependencies, key=lambda item: (not item["fixed_timeout_signature_candidate"], -item["sample_count"], item["dependency"]))}


def _signature(event: Mapping[str, Any]) -> str:
    action = event.get("action_id")
    message = re.sub(r"\d+", "?", str(event.get("message") or "").strip().lower())
    if event.get("http_status") is not None:
        return f"http_status={event['http_status']}|action={action}|message={message}"
    if event.get("exception_class"):
        return f"exception={event['exception_class']}|action={action}|message={message}"
    return f"unknown|action={action}|message={message}"


def _external_dependency_summary(name: str, members: List[Mapping[str, Any]]) -> Dict[str, Any]:
    durations = sorted(value for member in members if (value := _duration_ms(member)) is not None)
    cluster = _fixed_duration_cluster(durations)
    sorted_members = sorted(members, key=lambda member: (_duration_ms(member) or 0, str(member.get("trace_id"))), reverse=True)
    return {"dependency": name, "sample_count": len(members), "affected_transactions": _unique_sorted(member.get("action_id") for member in members), "affected_instances": _unique_sorted(member.get("instance_id") for member in members), "observed_duration_cluster": cluster, "fixed_timeout_signature_candidate": cluster is not None, "interpretation": "candidate_signal_only", "representative_abnormal_trace": dict(sorted_members[0]) if sorted_members else None, "members": [dict(member) for member in members]}


def _dependency_name(event: Mapping[str, Any]) -> str:
    scope = event.get("scope")
    if isinstance(scope, Mapping) and scope.get("dependency"):
        return str(scope["dependency"])
    return str(event.get("dependency") or event.get("host") or event.get("uri") or event.get("name") or "unknown")


def _duration_ms(event: Mapping[str, Any]) -> Optional[float]:
    duration = event.get("duration_ms")
    if isinstance(duration, Mapping):
        duration = duration.get("value")
    if duration is None and isinstance(event.get("metrics"), Mapping):
        response = event["metrics"].get("response_avg")
        if isinstance(response, Mapping) and response.get("unit") == "ms":
            duration = response.get("value")
    return float(duration) if duration is not None else None


def _fixed_duration_cluster(durations: List[float]) -> Optional[Dict[str, Any]]:
    if len(durations) < 3:
        return None
    for start in range(len(durations) - 2):
        window = durations[start:]
        if window[0] >= 100_000 and window[-1] - window[0] <= 5_000:
            return {"from_ms": int(window[0]), "to_ms": int(window[-1]), "count": len(window)}
    return None


def _unique_sorted(values) -> List[Any]:
    return sorted({value for value in values if value not in (None, "")})
