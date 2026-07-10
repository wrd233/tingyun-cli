from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


def adaptive_window_narrow(windows: Iterable[Mapping[str, Any]], *, signal: str, min_window_minutes: int, max_steps: int, request_budget: int) -> Dict[str, Any]:
    steps: List[Dict[str, Any]] = []
    limit = min(max_steps, request_budget)
    for index, window in enumerate(list(windows)[:limit], 1):
        size = float(window["to"]) - float(window["from"])
        reason = "min_window_reached" if size <= min_window_minutes else _reason(signal)
        steps.append({"step": index, "input_window": {"from": window["from"], "to": window["to"]}, "metric": {"signal": signal, "value": _score(window, signal)}, "selection_reason": reason, "source_refs": list(window.get("source_refs") or [])})
        if reason == "min_window_reached":
            break
    return {"schema_version": 1, "status": "SUCCESS" if steps else "BLOCKED", "recommended_window": steps[-1]["input_window"] if steps else None, "steps": steps, "actual_request_count": 0, "inspected_window_count": len(steps), "stop_condition": steps[-1]["selection_reason"] if steps else "no_steps"}


def locate_peak(*, windows: Iterable[Mapping[str, Any]], metric_semantic_status: str, candidates: Iterable[Mapping[str, Any]], request_budget: int) -> Dict[str, Any]:
    if metric_semantic_status not in {"VERIFIED", "AMBIGUOUS", "UNKNOWN"}:
        raise ValueError("unsupported metric semantic status")
    steps = []
    best = None
    for index, window in enumerate(list(windows)[:request_budget], 1):
        current = {"step": index, "window": {"from": window["from"], "to": window["to"]}, "reported_max_metric": window.get("reported_max_metric"), "source_refs": list(window.get("source_refs") or [])}
        steps.append(current)
        if best is None or float(current["reported_max_metric"] or 0) > float(best["reported_max_metric"] or 0):
            best = current
    candidate_match = _match_candidate(best, candidates)
    return {"schema_version": 1, "status": "SUCCESS" if candidate_match["status"] == "FOUND" else "UNRESOLVED", "metric": {"name": "reported_max_metric", "semantic_status": metric_semantic_status, "caveat": "reported max semantics are not confirmed" if metric_semantic_status != "VERIFIED" else None}, "steps": steps, "peak_window": best["window"] if best else None, "candidate_match": candidate_match, "actual_request_count": 0, "inspected_window_count": len(steps)}


def _score(window: Mapping[str, Any], signal: str) -> float:
    if signal in {"error_rate", "slow_rate"}:
        requests = float(window.get("request_count") or 0)
        numerator = window.get("error_count" if signal == "error_rate" else "slow_count") or 0
        return 0.0 if requests == 0 else float(numerator) / requests
    return float(window.get(signal) or 0)


def _reason(signal: str) -> str:
    return {"error_rate": "highest_error_rate", "slow_rate": "highest_slow_rate"}.get(signal, f"highest_{signal}")


def _match_candidate(best: Mapping[str, Any], candidates: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    if not best:
        return {"status": "NOT_FOUND"}
    target = best.get("reported_max_metric")
    for candidate in candidates:
        duration = candidate.get("duration_ms")
        if isinstance(duration, Mapping):
            duration = duration.get("value")
        if duration == target:
            return {"status": "FOUND", "candidate": dict(candidate)}
    return {"status": "NOT_FOUND"}
