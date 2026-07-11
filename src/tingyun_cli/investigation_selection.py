from __future__ import annotations

from typing import Any, Dict, Mapping


def trace_target_check(candidate_binding: Mapping[str, Any], trace_record: Mapping[str, Any]) -> Dict[str, Any]:
    expected = {
        "source_run_id": candidate_binding.get("collect_run_id") or candidate_binding.get("source_run_id"),
        "source_item_ref": candidate_binding.get("item_ref") or candidate_binding.get("source_item_ref"),
    }
    source = trace_record.get("source") if isinstance(trace_record.get("source"), Mapping) else {}
    observed = {
        "source_run_id": source.get("run_id") or trace_record.get("source_run_id"),
        "source_item_ref": source.get("item_ref") or trace_record.get("source_item_ref"),
    }
    if not all(expected.values()) or not any(observed.values()):
        status = "UNVERIFIABLE"
    elif observed == expected:
        status = "EXACT_TARGET"
    elif observed["source_run_id"] == expected["source_run_id"] and observed["source_item_ref"] in (None, ""):
        status = "STRONG_TARGET"
    else:
        status = "WRONG_TARGET"
    return {"status": status, "expected": expected, "observed": observed}
