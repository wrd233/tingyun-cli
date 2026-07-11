from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .source_normalization import classify_exception_signal


def assess_trace_sample(candidate: Mapping[str, Any], trace: Mapping[str, Any], *, alarm_metric: Optional[str] = None) -> Dict[str, Any]:
    metrics = candidate.get("metrics") if isinstance(candidate.get("metrics"), Mapping) else {}
    trace_data = trace.get("data") if isinstance(trace.get("data"), Mapping) else trace
    summary = trace_data.get("summary") if isinstance(trace_data.get("summary"), Mapping) else trace.get("summary") if isinstance(trace.get("summary"), Mapping) else {}
    duration = _number(summary.get("duration") or summary.get("respTime") or trace.get("duration") or trace.get("duration_ms"))
    exceptions = trace_data.get("exceptions") if isinstance(trace_data.get("exceptions"), list) else []
    signal_types = sorted({classify_exception_signal(item) for item in exceptions if isinstance(item, Mapping)})
    explicit_error = _explicit_error(trace_data, exceptions)
    p50 = _metric(metrics, "p50")
    p95 = _metric(metrics, "p95")
    p99 = _metric(metrics, "p99")
    error_count = _metric(metrics, "error_count")
    slow_count = _metric(metrics, "slow_count")
    contexts = _contexts(alarm_metric, slow_count=slow_count, error_count=error_count)
    duration_position = _duration_position(duration, p50=p50, p95=p95, p99=p99)

    reasons = []
    if "LATENCY" in contexts and duration is not None and p95 is not None and duration >= p95:
        reasons.append("trace_duration_at_or_above_candidate_p95")
    if "ERROR" in contexts and (explicit_error or "THROWN_EXCEPTION" in signal_types):
        reasons.append("trace_has_explicit_error_or_thrown_exception")
    if reasons:
        assessment = "ABNORMAL_ALIGNED"
    else:
        contrast_reasons = []
        if "LATENCY" in contexts and duration is not None and p50 is not None and duration <= p50 and (slow_count or 0) > 0:
            contrast_reasons.append("trace_at_or_below_p50_while_aggregate_has_slow_requests")
        if "ERROR" in contexts and (error_count or 0) > 0 and not explicit_error and "THROWN_EXCEPTION" not in signal_types:
            contrast_reasons.append("trace_has_no_error_while_aggregate_has_errors")
        if contrast_reasons:
            assessment = "NORMAL_CONTRAST"
            reasons = contrast_reasons
        else:
            assessment = "UNKNOWN"
            reasons = ["insufficient_or_nonaligning_evidence"]

    exception_metric = metrics.get("exception_count") if isinstance(metrics.get("exception_count"), Mapping) else {}
    return {
        "schema_version": 1,
        "trace_duration": duration,
        "candidate_p50": p50,
        "candidate_p95": p95,
        "candidate_p99": p99,
        "candidate_error_count": error_count,
        "candidate_error_rate": _metric(metrics, "error_rate"),
        "candidate_slow_count": slow_count,
        "candidate_exception_count": _metric(metrics, "exception_count"),
        "candidate_exception_count_semantic_status": exception_metric.get("semantic_status", "UNKNOWN"),
        "trace_error_signal": explicit_error,
        "trace_exception_signal_types": signal_types,
        "alarm_context": contexts,
        "duration_position": duration_position,
        "sample_assessment": assessment,
        "reasons": reasons,
    }


def candidate_from_evidence(evidence: Mapping[str, Any], item_ref: Optional[str] = None) -> Dict[str, Any]:
    data = evidence.get("data") if isinstance(evidence.get("data"), Mapping) else None
    items = data.get("items") if isinstance(data, Mapping) else None
    if isinstance(items, list):
        selected = [item for item in items if isinstance(item, Mapping) and (item_ref is None or item.get("item_ref") == item_ref)]
        if len(selected) != 1:
            raise ValueError("candidate evidence must select exactly one item")
        return dict(selected[0])
    return dict(evidence)


def _metric(metrics: Mapping[str, Any], name: str) -> Optional[float]:
    value = metrics.get(name)
    if isinstance(value, Mapping):
        value = value.get("value")
    return _number(value)


def _number(value: Any) -> Optional[float]:
    if isinstance(value, Mapping):
        value = value.get("value")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _duration_position(duration: Optional[float], *, p50: Optional[float], p95: Optional[float], p99: Optional[float]) -> str:
    if duration is None:
        return "UNAVAILABLE"
    if p99 is not None and duration >= p99:
        return "AT_OR_ABOVE_P99"
    if p95 is not None and duration >= p95 and (p99 is None or duration < p99):
        return "P95_TO_P99"
    if p50 is not None and duration > p50 and (p95 is None or duration < p95):
        return "P50_TO_P95"
    if p50 is not None and duration <= p50:
        return "AT_OR_BELOW_P50"
    return "UNAVAILABLE"


def _contexts(alarm_metric: Optional[str], *, slow_count: Optional[float], error_count: Optional[float]):
    contexts = []
    lowered = (alarm_metric or "").lower()
    if any(token in lowered for token in ("response", "latency", "slow", "duration")) or (not lowered and (slow_count or 0) > 0):
        contexts.append("LATENCY")
    if any(token in lowered for token in ("error", "exception")) or (not lowered and (error_count or 0) > 0):
        contexts.append("ERROR")
    return contexts


def _explicit_error(trace_data: Mapping[str, Any], exceptions) -> bool:
    for key in ("error", "hasError", "errorStatus"):
        if trace_data.get(key) is True:
            return True
    return any(classify_exception_signal(item) == "THROWN_EXCEPTION" for item in exceptions if isinstance(item, Mapping))
