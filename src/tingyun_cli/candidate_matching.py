from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


_LEVEL_ORDER = {"EXACT": 0, "STRONG": 1, "WEAK": 2}


def match_candidates(
    artifact: Mapping[str, Any],
    *,
    run_id: str,
    name: str,
    application: Optional[str] = None,
    route_fragment: Optional[str] = None,
    request_type: Optional[str] = None,
) -> Dict[str, Any]:
    query = {"name": name}
    if application is not None:
        query["application"] = application
    if route_fragment is not None:
        query["route_fragment"] = route_fragment
    if request_type is not None:
        query["request_type"] = request_type
    data = artifact.get("data") if isinstance(artifact, Mapping) else None
    items = data.get("items") if isinstance(data, Mapping) else None
    if not isinstance(items, list):
        raise ValueError("candidate artifact must contain data.items")

    matches = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        evaluated = _match_item(item, name=name, application=application, route_fragment=route_fragment, request_type=request_type)
        if evaluated is not None:
            matches.append(evaluated)
    matches.sort(key=lambda item: (_LEVEL_ORDER[item["match_level"]], str(item.get("source_run_id")), str(item.get("item_ref"))))
    overall = matches[0]["match_level"] if matches else "NOT_FOUND"
    return {
        "schema_version": 1,
        "run_id": run_id,
        "time_context": artifact.get("time_context"),
        "query": query,
        "overall_match_level": overall,
        "matches": matches,
    }


def _match_item(item: Mapping[str, Any], *, name: str, application: Optional[str], route_fragment: Optional[str], request_type: Optional[str]) -> Optional[Dict[str, Any]]:
    candidate_name = str(item.get("name") or "")
    labels = item.get("labels") if isinstance(item.get("labels"), Mapping) else {}
    matched_fields = []
    mismatched_fields = []

    exact_name = candidate_name == name
    exact_route = route_fragment is not None and _route_fragment(candidate_name) == route_fragment
    service_signature = _service_signature(candidate_name)
    exact_signature = service_signature is not None and service_signature == name
    weak_name = bool(name) and (name in candidate_name or _basename(name) == _basename(candidate_name))
    if not (exact_name or exact_route or exact_signature or weak_name):
        return None
    if exact_name:
        matched_fields.append("name")
    elif exact_route:
        matched_fields.append("route_fragment")
    elif exact_signature:
        matched_fields.append("service_method_signature")
    else:
        matched_fields.append("partial_name")

    constraints = {
        "application": (application, labels.get("applicationName")),
        "request_type": (request_type, labels.get("requestType")),
    }
    for field, (expected, observed) in constraints.items():
        if expected is None:
            continue
        if observed == expected:
            matched_fields.append(field)
        else:
            mismatched_fields.append(field)

    if mismatched_fields:
        level = "WEAK"
        basis = "constraint_mismatch"
    elif exact_name:
        level = "EXACT"
        basis = "full_name_exact"
    elif exact_route:
        level = "STRONG"
        basis = "exact_route_fragment"
    elif exact_signature:
        level = "STRONG"
        basis = "exact_service_method_signature"
    else:
        level = "WEAK"
        basis = "partial_substring"

    result = {
        "item_ref": item.get("item_ref"),
        "source_run_id": item.get("source_run_id"),
        "name": candidate_name,
        "semantic_kind": item.get("semantic_kind", "UNKNOWN"),
        "match_level": level,
        "match_basis": basis,
        "matched_fields": sorted(matched_fields),
        "mismatched_fields": sorted(mismatched_fields),
        "metrics": dict(item.get("metrics") or {}),
        "available_actions": list(item.get("available_actions") or []),
        "links": list(item.get("links") or []),
        "navigation": dict(item.get("navigation") or {}),
    }
    result["execution_eligible"] = level == "EXACT" and "investigate_trace" in result["available_actions"]
    return result


def _route_fragment(name: str) -> str:
    for prefix in ("SpringController", "URI", "WebAction"):
        marker = prefix + "/"
        if name.startswith(marker):
            route = name[len(prefix):]
            return route.split(" (", 1)[0]
    return name.split(" (", 1)[0]


def _service_signature(name: str) -> Optional[str]:
    for prefix in ("DubboProvider/", "DubboConsumer/"):
        if name.startswith(prefix):
            return name[len(prefix):]
    return None


def _basename(value: str) -> str:
    return value.rstrip("/").rsplit("/", 1)[-1]
