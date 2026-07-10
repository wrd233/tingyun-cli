from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class Scope:
    type: str
    values: Mapping[str, Any]

    @classmethod
    def business_system(cls, *, business_system_id: Any) -> "Scope":
        return cls("business_system", {"business_system_id": business_system_id})

    @classmethod
    def application(cls, *, business_system_id: Any, application_id: Any) -> "Scope":
        return cls("application", {"business_system_id": business_system_id, "application_id": application_id})

    @classmethod
    def instance(cls, *, instance_id: Any, application_id: Optional[Any] = None) -> "Scope":
        values = {"instance_id": instance_id}
        if application_id is not None:
            values["application_id"] = application_id
        return cls("instance", values)

    @classmethod
    def transaction(cls, *, business_system_id: Any, application_id: Any, action_id: Any) -> "Scope":
        return cls("transaction", {"business_system_id": business_system_id, "application_id": application_id, "action_id": action_id})

    @classmethod
    def trace(cls, *, trace_id: Any) -> "Scope":
        return cls("trace", {"trace_id": trace_id})

    def as_dict(self) -> Dict[str, Any]:
        return {"type": self.type, **dict(self.values)}


_METRIC_CONTRACTS: Dict[str, Dict[str, Any]] = {
    "response_avg": {"stable_normalized_name": "avg_response_time_ms", "unit": "ms", "scope": "business_system|application|transaction", "aggregation": "average", "semantic_status": "VERIFIED", "caveats": []},
    "p50": {"stable_normalized_name": "p50_ms", "unit": "ms", "scope": "business_system|application|transaction", "aggregation": "percentile_p50", "semantic_status": "VERIFIED", "caveats": []},
    "p95": {"stable_normalized_name": "p95_ms", "unit": "ms", "scope": "business_system|application|transaction", "aggregation": "percentile_p95", "semantic_status": "VERIFIED", "caveats": []},
    "p99": {"stable_normalized_name": "p99_ms", "unit": "ms", "scope": "business_system|application|transaction", "aggregation": "percentile_p99", "semantic_status": "VERIFIED", "caveats": []},
    "error_count": {"stable_normalized_name": "error_count", "unit": "count", "scope": "business_system|application|transaction", "aggregation": "sum", "semantic_status": "VERIFIED", "caveats": []},
    "exception_count": {"stable_normalized_name": None, "unit": "count", "scope": "business_system|application|transaction", "aggregation": "platform_specific_count", "semantic_status": "AMBIGUOUS", "caveats": ["not equivalent to Java exception count without endpoint-specific verification"]},
    "overview.max": {"stable_normalized_name": None, "unit": None, "scope": "business_system", "aggregation": "reported_max_metric", "semantic_status": "UNKNOWN", "caveats": ["exact max semantics are not confirmed; do not call it single-request duration"]},
}


def duration_metric(field: str, raw_value: Any, *, raw_unit: Optional[str]) -> Dict[str, Any]:
    if raw_unit == "ms":
        return {"name": field if field.endswith("_ms") else f"{field}_ms", "value": raw_value, "unit": "ms", "raw": {"field": field, "value": raw_value, "unit": raw_unit}, "semantic_status": "VERIFIED"}
    return {"name": field, "raw": {"field": field, "value": raw_value, "unit": raw_unit}, "semantic_status": "UNKNOWN"}


def metric_contract(name: str) -> Dict[str, Any]:
    contract = _METRIC_CONTRACTS.get(name)
    if contract is None:
        return {"metric": name, "stable_normalized_name": None, "semantic_status": "UNKNOWN", "caveats": ["metric is not in the bounded semantic registry"]}
    return {"metric": name, **contract}


def scoped_item(*, item_ref: str, item_type: str, scope: Scope, metrics: Mapping[str, Any], identity: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    item = {"item_ref": item_ref, "item_type": item_type, "scope": scope.as_dict(), "metrics": dict(metrics)}
    if identity:
        item["identity"] = dict(identity)
    return item


def url_evidence(*, object_type: str, object_id: Any, url: str, source_type: str, verification: Optional[Mapping[str, Any]] = None, evidence_path: Optional[str] = None) -> Dict[str, Any]:
    verification_data = dict(verification or {"status": "NOT_ATTEMPTED"})
    if verification_data.get("status") == "SUCCESS" and verification_data.get("http_status") != 200:
        verification_data["status"] = "FAILED"
    evidence = {"object_type": object_type, "object_id": str(object_id), "url": url, "source_type": source_type, "verification": verification_data}
    if evidence_path:
        evidence["evidence_path"] = evidence_path
    return evidence
