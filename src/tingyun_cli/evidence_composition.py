from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .evidence_extraction import extract_call_tree
from .investigation_selection import trace_target_check
from .manifest_schema import validate_investigation_manifest
from .trace_sample_assessment import assess_trace_sample


INCIDENT_KINDS = {
    "TEMPORAL_INCIDENT", "CALL_CHAIN_INCIDENT", "SERVICE_FAMILY_CLUSTER",
    "RECURRING_ALARM_CLUSTER", "INSTANCE_CLUSTER", "OTHER",
}
SOURCE_ROLES = {
    "external_calls", "recent_requests_response", "recent_requests_error",
    "recent_requests_throughput", "performance_error_series",
    "performance_throughput_series", "application_instances",
    "trace_exceptions", "alarm_detail", "alarm_metric_series", "other",
}
SOURCE_ARTIFACT_KINDS = {
    "external_calls": "external_calls",
    "recent_requests_response": "recent_requests",
    "recent_requests_error": "recent_requests",
    "recent_requests_throughput": "recent_requests",
    "performance_error_series": "performance_error_series",
    "performance_throughput_series": "performance_throughput_series",
    "application_instances": "instance_context",
    "trace_exceptions": "trace_exceptions",
    "alarm_detail": "alarm_detail",
    "alarm_metric_series": "alarm_metric_series",
}
VERIFIED_LINK_PROOFS = {"LIVE_OBSERVED", "DERIVED_FROM_VERIFIED_ROUTE"}


class CompositionError(Exception):
    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(message or code)
        self.code = code


def compile_evidence(manifest_path: Path, *, data_root: Path, output_dir: Path) -> Dict[str, Any]:
    manifest_path = Path(manifest_path)
    data_root = Path(data_root)
    output_dir = Path(output_dir)
    _prepare_output(output_dir)
    try:
        loaded_manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise CompositionError("INVALID_INVESTIGATION_MANIFEST", str(exc)) from exc

    manifest = dict(loaded_manifest) if isinstance(loaded_manifest, Mapping) else {}
    issues = [
        _issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", validator="draft_2020_12_subset", **violation)
        for violation in validate_investigation_manifest(loaded_manifest)
    ]
    issues.extend(_validate_manifest(manifest))
    reader = _RunReader(data_root, issues)
    incident_ids = {item.get("incident_id") for item in manifest.get("incidents", []) if isinstance(item, Mapping)}
    seed_by_id = {item.get("alarm_seed_id"): dict(item) for item in manifest.get("alarm_seeds", []) if isinstance(item, Mapping) and item.get("alarm_seed_id")}
    incidents = {item.get("incident_id"): dict(item) for item in manifest.get("incidents", []) if isinstance(item, Mapping) and item.get("incident_id")}
    windows = {item.get("window_id"): dict(item) for item in manifest.get("windows", []) if isinstance(item, Mapping) and item.get("window_id")}
    candidate_binding_registry = {item.get("binding_id"): dict(item) for item in manifest.get("candidate_bindings", []) if isinstance(item, Mapping) and item.get("binding_id")}

    canonical_windows = []
    for window_id in sorted(windows):
        window = windows[window_id]
        run_manifest = reader.manifest(str(window.get("collect_run_id") or ""))
        actual_time = run_manifest.get("time_context") if run_manifest else None
        expected = window.get("expected_time_context")
        context_status = "SUCCESS"
        if not run_manifest or run_manifest.get("run_type") != "COLLECT" or not isinstance(actual_time, Mapping):
            context_status = "REJECTED"
            issues.append(_issue("INVALID_WINDOW_CONTEXT", "ERROR", window_id=window_id, collect_run_id=window.get("collect_run_id")))
        if expected is not None and actual_time is not None and not _contains(actual_time, expected):
            context_status = "REJECTED"
            issues.append(_issue("WINDOW_TIME_CONTEXT_MISMATCH", "ERROR", window_id=window_id, collect_run_id=window.get("collect_run_id")))
        canonical_windows.append({
            "window_id": window_id,
            "collect_run_id": window.get("collect_run_id"),
            "incident_ids": sorted(window.get("incident_ids") or []),
            "alarm_seed_ids": sorted(window.get("alarm_seed_ids") or []),
            "time_context": actual_time,
            "context_status": context_status,
        })

    accepted_candidates: Dict[str, Dict[str, Any]] = {}
    candidate_extractions: Dict[str, Dict[str, Any]] = {}
    for binding_id in sorted(candidate_binding_registry):
        binding = candidate_binding_registry[binding_id]
        incident_id = binding.get("incident_id")
        window = windows.get(binding.get("window_id"))
        if incident_id not in incident_ids:
            issues.append(_issue("NONCANONICAL_INCIDENT_ID", "ERROR", binding_type="candidate", binding_id=binding_id, incident_id=incident_id))
            continue
        if window is None:
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", binding_id=binding_id, field="window_id"))
            continue
        incident = incidents.get(incident_id) or {}
        if incident_id not in (window.get("incident_ids") or []) or binding.get("alarm_seed_id") not in (window.get("alarm_seed_ids") or []) or binding.get("alarm_seed_id") not in (incident.get("alarm_seed_ids") or []):
            issues.append(_issue("NONCANONICAL_INCIDENT_ID", "ERROR", binding_type="candidate", binding_id=binding_id, incident_id=incident_id, window_id=binding.get("window_id"), alarm_seed_id=binding.get("alarm_seed_id")))
            continue
        if binding.get("collect_run_id") != window.get("collect_run_id"):
            issues.append(_issue("CROSS_WINDOW_EVIDENCE_REJECTED", "ERROR", binding_id=binding_id, window_id=binding.get("window_id"), binding_collect_run_id=binding.get("collect_run_id"), window_collect_run_id=window.get("collect_run_id")))
            continue
        artifact = reader.artifact(str(binding.get("collect_run_id") or ""), kind="candidates")
        if artifact and not _artifact_status_usable(artifact):
            issues.append(_issue("UNUSABLE_ARTIFACT", "ERROR", run_id=binding.get("collect_run_id"), kind="candidates", status=artifact.get("status")))
            continue
        item = _find_item(artifact, str(binding.get("item_ref") or ""), str(binding.get("collect_run_id") or ""))
        if item is None:
            issues.append(_issue("ITEM_REF_NOT_FOUND", "ERROR", binding_id=binding_id, collect_run_id=binding.get("collect_run_id"), item_ref=binding.get("item_ref")))
            continue
        links = _verified_links(item)
        if (item.get("navigation") or {}).get("status") == "SUCCESS" and not links:
            issues.append(_issue("URL_PROPAGATION_FAILURE", "ERROR", binding_id=binding_id))
        extraction = {
            "schema_version": 1,
            "binding_id": binding_id,
            "alarm_seed_id": binding.get("alarm_seed_id"),
            "incident_id": incident_id,
            "window_id": binding.get("window_id"),
            "collect_run_id": binding.get("collect_run_id"),
            "item_ref": binding.get("item_ref"),
            "match_level": binding.get("match_level"),
            "match_basis": binding.get("match_basis"),
            "name": item.get("name"),
            "semantic_kind": item.get("semantic_kind", "UNKNOWN"),
            "metrics": dict(item.get("metrics") or {}),
            "available_actions": list(item.get("available_actions") or []),
            "links": links,
            "navigation": dict(item.get("navigation") or {}),
            "wire_identity": dict(item.get("wire_identity") or {}),
            "source_refs": list(item.get("source_refs") or artifact.get("derived_from") or []),
        }
        accepted_candidates[binding_id] = {"binding": binding, "item": item, "extraction": extraction}
        candidate_extractions[f"extractions/candidates/{binding_id}.json"] = extraction

    accepted_traces: Dict[str, Dict[str, Any]] = {}
    rejected_traces: List[Dict[str, Any]] = []
    trace_extractions: Dict[str, Dict[str, Any]] = {}
    for binding in sorted((item for item in manifest.get("trace_bindings", []) if isinstance(item, Mapping)), key=lambda item: str(item.get("trace_run_id"))):
        trace_run_id = str(binding.get("trace_run_id") or "")
        incident_id = binding.get("incident_id")
        candidate = accepted_candidates.get(binding.get("candidate_binding_id"))
        if incident_id not in incident_ids:
            issues.append(_issue("NONCANONICAL_INCIDENT_ID", "ERROR", binding_type="trace", trace_run_id=trace_run_id, incident_id=incident_id))
            continue
        if candidate is None:
            continue
        if incident_id != candidate["binding"].get("incident_id"):
            issues.append(_issue("NONCANONICAL_INCIDENT_ID", "ERROR", binding_type="trace", trace_run_id=trace_run_id, incident_id=incident_id, candidate_incident_id=candidate["binding"].get("incident_id")))
            continue
        trace_manifest = reader.manifest(trace_run_id)
        trace_artifact = reader.artifact(trace_run_id, kind="trace")
        if not trace_manifest or not trace_artifact:
            continue
        target = trace_target_check(candidate["binding"], trace_manifest)
        audit = {"trace_run_id": trace_run_id, "candidate_binding_id": binding.get("candidate_binding_id"), "incident_id": incident_id, "declared_target_match": binding.get("target_match"), "target_check": target}
        if target["status"] not in {"EXACT_TARGET", "STRONG_TARGET"}:
            audit["status"] = "REJECTED_WRONG_TARGET"
            rejected_traces.append(audit)
            issues.append(_issue("WRONG_TARGET_TRACE_REJECTED", "WARNING", trace_run_id=trace_run_id, candidate_binding_id=binding.get("candidate_binding_id"), observed=target["observed"], expected=target["expected"]))
            continue
        data = trace_artifact.get("data") if isinstance(trace_artifact.get("data"), Mapping) else {}
        items = data.get("items") if isinstance(data.get("items"), list) else []
        if not _artifact_status_usable(trace_artifact) or not items:
            audit["status"] = "REJECTED_UNUSABLE_ARTIFACT"
            audit["artifact_status"] = trace_artifact.get("status")
            rejected_traces.append(audit)
            issues.append(_issue("UNUSABLE_ARTIFACT", "ERROR", run_id=trace_run_id, kind="trace", status=trace_artifact.get("status")))
            continue
        matching_trace_items = [dict(item) for item in items if isinstance(item, Mapping) and trace_target_check(candidate["binding"], item)["status"] == "EXACT_TARGET"]
        if len(matching_trace_items) != 1:
            artifact_target = trace_target_check(candidate["binding"], items[0] if items and isinstance(items[0], Mapping) else {})
            audit["status"] = "REJECTED_WRONG_TARGET"
            audit["artifact_target_check"] = artifact_target
            rejected_traces.append(audit)
            issues.append(_issue("WRONG_TARGET_TRACE_REJECTED", "WARNING", trace_run_id=trace_run_id, candidate_binding_id=binding.get("candidate_binding_id"), evidence_layer="trace_artifact", observed=artifact_target["observed"], expected=artifact_target["expected"]))
            continue
        trace_item = matching_trace_items[0]
        alarm_metric = seed_by_id.get(candidate["binding"].get("alarm_seed_id"), {}).get("metric")
        assessment = assess_trace_sample(candidate["item"], trace_artifact, alarm_metric=alarm_metric)
        extraction = {
            "schema_version": 1,
            "trace_run_id": trace_run_id,
            "candidate_binding_id": binding.get("candidate_binding_id"),
            "incident_id": incident_id,
            "target_match": target["status"],
            "duration": assessment.get("trace_duration"),
            "error_signals": assessment.get("trace_error_signal"),
            "exception_signal_types": assessment.get("trace_exception_signal_types"),
            "timeline": data.get("timeline") or {},
            "topology": data.get("trace_topology") or {},
            "service_flow": data.get("service_flow") or {},
            "request_service_flow": data.get("request_service_flow") or {},
            "links": list(trace_item.get("links") or []),
            "sample_assessment": assessment,
            "wire_identity": dict(trace_item.get("wire_identity") or {}),
            "source_refs": list(trace_item.get("source_refs") or trace_artifact.get("derived_from") or []),
        }
        accepted_traces[trace_run_id] = {"binding": dict(binding), "artifact": trace_artifact, "extraction": extraction}
        trace_extractions[f"extractions/traces/{trace_run_id}.json"] = extraction

    accepted_call_trees: Dict[str, Dict[str, Any]] = {}
    call_tree_extractions: Dict[str, Dict[str, Any]] = {}
    for binding in sorted((item for item in manifest.get("call_tree_bindings", []) if isinstance(item, Mapping)), key=lambda item: str(item.get("call_tree_run_id"))):
        run_id = str(binding.get("call_tree_run_id") or "")
        incident_id = binding.get("incident_id")
        trace_run_id = str(binding.get("trace_run_id") or "")
        if incident_id not in incident_ids:
            issues.append(_issue("NONCANONICAL_INCIDENT_ID", "ERROR", binding_type="call_tree", call_tree_run_id=run_id, incident_id=incident_id))
            continue
        if trace_run_id not in accepted_traces:
            issues.append(_issue("BROKEN_CALL_TREE_LINEAGE", "ERROR", call_tree_run_id=run_id, trace_run_id=trace_run_id, reason="trace_not_target_correct"))
            continue
        trace_incident_id = accepted_traces[trace_run_id]["binding"].get("incident_id")
        if incident_id != trace_incident_id:
            issues.append(_issue("NONCANONICAL_INCIDENT_ID", "ERROR", binding_type="call_tree", call_tree_run_id=run_id, incident_id=incident_id, trace_incident_id=trace_incident_id))
            continue
        run_manifest = reader.manifest(run_id)
        artifact = reader.artifact(run_id, kind="call_tree")
        if not run_manifest or not artifact:
            continue
        source = run_manifest.get("source") if isinstance(run_manifest.get("source"), Mapping) else {}
        data = artifact.get("data") if isinstance(artifact.get("data"), Mapping) else {}
        artifact_source = data.get("source_item") if isinstance(data.get("source_item"), Mapping) else {}
        if not _artifact_status_usable(artifact) or not isinstance(data.get("call_tree"), Mapping) or not data.get("call_tree"):
            issues.append(_issue("UNUSABLE_ARTIFACT", "ERROR", run_id=run_id, kind="call_tree", status=artifact.get("status")))
            continue
        if source.get("run_id") != trace_run_id or artifact_source.get("run_id") != trace_run_id:
            issues.append(_issue("BROKEN_CALL_TREE_LINEAGE", "ERROR", call_tree_run_id=run_id, trace_run_id=trace_run_id, observed_manifest_source=source.get("run_id"), observed_artifact_source=artifact_source.get("run_id")))
            continue
        call_tree = data.get("call_tree") if isinstance(data.get("call_tree"), Mapping) else {}
        extraction = extract_call_tree(call_tree, evidence_ref=f"{run_id}/evidence/call_tree.json")
        extraction.update({"call_tree_run_id": run_id, "trace_run_id": trace_run_id, "incident_id": incident_id})
        accepted_call_trees[run_id] = {"binding": dict(binding), "extraction": extraction}
        call_tree_extractions[f"extractions/call-trees/{run_id}.json"] = extraction

    accepted_sources: Dict[str, Dict[str, Any]] = {}
    source_extractions: Dict[str, Dict[str, Any]] = {}
    for binding in sorted((item for item in manifest.get("source_bindings", []) if isinstance(item, Mapping)), key=lambda item: (str(item.get("role")), str(item.get("source_run_id")))):
        incident_id = binding.get("incident_id")
        run_id = str(binding.get("source_run_id") or "")
        role = str(binding.get("role") or "")
        if incident_id not in incident_ids:
            issues.append(_issue("NONCANONICAL_INCIDENT_ID", "ERROR", binding_type="source", source_run_id=run_id, incident_id=incident_id))
            continue
        if role not in SOURCE_ROLES:
            issues.append(_issue("NONCANONICAL_SOURCE_BINDING", "ERROR", source_run_id=run_id, role=role))
            continue
        expected_kind = SOURCE_ARTIFACT_KINDS.get(role)
        run_manifest = reader.manifest(run_id)
        artifact_kinds = {record.get("kind") for record in (run_manifest or {}).get("artifacts", []) if isinstance(record, Mapping)}
        if expected_kind is not None and expected_kind not in artifact_kinds:
            issues.append(_issue("NONCANONICAL_SOURCE_BINDING", "ERROR", source_run_id=run_id, role=role, expected_artifact_kind=expected_kind, observed_artifact_kinds=sorted(str(kind) for kind in artifact_kinds)))
            continue
        artifact = reader.artifact(run_id, kind=expected_kind)
        if not artifact:
            continue
        if not _artifact_status_usable(artifact):
            issues.append(_issue("UNUSABLE_ARTIFACT", "ERROR", run_id=run_id, kind=expected_kind, status=artifact.get("status")))
            continue
        expected_ranking = {"recent_requests_response": "response", "recent_requests_error": "error", "recent_requests_throughput": "throughput"}.get(role)
        artifact_source = artifact.get("source") if isinstance(artifact.get("source"), Mapping) else {}
        if expected_ranking is not None and artifact_source.get("ranking") != expected_ranking:
            issues.append(_issue("NONCANONICAL_SOURCE_BINDING", "ERROR", source_run_id=run_id, role=role, expected_ranking=expected_ranking, observed_ranking=artifact_source.get("ranking")))
            continue
        data = artifact.get("data") if isinstance(artifact.get("data"), Mapping) else {}
        extraction = {"schema_version": 1, "incident_id": incident_id, "source_run_id": run_id, "role": role, "items": list(data.get("items") or []), "source_refs": list(artifact.get("derived_from") or [])}
        accepted_sources[run_id] = {"binding": dict(binding), "extraction": extraction}
        directory = _source_directory(role)
        source_extractions[f"extractions/{directory}/{run_id}.json"] = extraction

    evidence_map = _build_evidence_map(incidents, canonical_windows, accepted_candidates, accepted_traces, accepted_call_trees, accepted_sources, rejected_traces)
    counts = {
        "alarm_seed_count": len(seed_by_id),
        "incident_count": len(incidents),
        "window_count": len(windows),
        "collect_run_count": len({item.get("collect_run_id") for item in windows.values()}),
        "trace_run_count": len({item.get("trace_run_id") for item in manifest.get("trace_bindings", []) if isinstance(item, Mapping)}),
        "target_correct_trace_count": len(accepted_traces),
        "call_tree_run_count": len({item.get("call_tree_run_id") for item in manifest.get("call_tree_bindings", []) if isinstance(item, Mapping)}),
        "target_correct_call_tree_count": len(accepted_call_trees),
        "source_run_count": len({item.get("source_run_id") for item in manifest.get("source_bindings", []) if isinstance(item, Mapping)}),
    }
    source_of_truth = {
        "schema_version": 1,
        "investigation_id": manifest.get("investigation_id"),
        "manifest_hash": _hash_object(loaded_manifest),
        "run_refs": sorted(reader.run_hashes),
        "run_manifest_hashes": {key: reader.run_hashes[key] for key in sorted(reader.run_hashes)},
        "counts": counts,
        "canonical_alarm_seeds": [seed_by_id[key] for key in sorted(seed_by_id)],
        "canonical_incidents": [incidents[key] for key in sorted(incidents)],
        "canonical_windows": canonical_windows,
    }
    coverage = _build_coverage(evidence_map)
    readiness = _build_readiness(evidence_map, accepted_candidates, accepted_traces, accepted_call_trees, accepted_sources)

    all_outputs = {
        "source-of-truth.json": source_of_truth,
        "evidence-map.json": evidence_map,
        "coverage.json": coverage,
        "report-readiness.json": readiness,
        **candidate_extractions,
        **trace_extractions,
        **call_tree_extractions,
        **source_extractions,
    }
    issues = _dedupe_issues(issues)
    status = "FAILED" if any(issue["severity"] == "ERROR" for issue in issues) else "SUCCESS"
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=str(output_dir.parent)))
    try:
        for relative, payload in sorted(all_outputs.items()):
            _write_json(staging / relative, payload)
        compiled_hashes = {relative: _sha256(staging / relative) for relative in sorted(all_outputs)}
        validation = {"schema_version": 1, "status": status, "issue_count": len(issues), "issues": issues, "compiled_hashes": compiled_hashes}
        _write_json(staging / "validation.json", validation)
        os.replace(staging, output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"schema_version": 1, "command": "depth evidence-compile", "status": status, "output_dir": str(output_dir), "validation": validation}


class _RunReader:
    def __init__(self, data_root: Path, issues: List[Dict[str, Any]]):
        self.data_root = data_root
        self.issues = issues
        self.manifests: Dict[str, Dict[str, Any]] = {}
        self.artifacts: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.run_hashes: Dict[str, str] = {}

    def manifest(self, run_id: str) -> Optional[Dict[str, Any]]:
        if not run_id:
            self.issues.append(_issue("MISSING_RUN", "ERROR", run_id=run_id))
            return None
        if run_id in self.manifests:
            return self.manifests[run_id]
        runs_root = (self.data_root / "runs").resolve()
        run_root = (runs_root / run_id).resolve()
        if run_root.parent != runs_root:
            self.issues.append(_issue("UNSAFE_PATH_REF", "ERROR", run_id=run_id, path="manifest.json"))
            return None
        path = run_root / "manifest.json"
        if not _is_within(run_root, path):
            self.issues.append(_issue("UNSAFE_PATH_REF", "ERROR", run_id=run_id, path="manifest.json"))
            return None
        if not path.is_file():
            self.issues.append(_issue("MISSING_RUN", "ERROR", run_id=run_id))
            return None
        try:
            manifest = _load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            self.issues.append(_issue("MISSING_ARTIFACT", "ERROR", run_id=run_id, path="manifest.json", detail=str(exc)))
            return None
        self.manifests[run_id] = manifest
        self.run_hashes[run_id] = _sha256(path)
        return manifest

    def artifact(self, run_id: str, kind: Optional[str] = None) -> Optional[Dict[str, Any]]:
        cache_key = (run_id, kind or "*")
        if cache_key in self.artifacts:
            return self.artifacts[cache_key]
        manifest = self.manifest(run_id)
        if not manifest:
            return None
        records = [record for record in manifest.get("artifacts", []) if isinstance(record, Mapping) and (kind is None or record.get("kind") == kind)]
        if not records:
            self.issues.append(_issue("MISSING_ARTIFACT", "ERROR", run_id=run_id, kind=kind))
            return None
        relative = records[0].get("path")
        run_root = (self.data_root / "runs" / run_id).resolve()
        path = (run_root / str(relative)).resolve()
        if not _is_within(run_root, path):
            self.issues.append(_issue("UNSAFE_PATH_REF", "ERROR", run_id=run_id, path=relative))
            return None
        if not path.is_file():
            self.issues.append(_issue("MISSING_ARTIFACT", "ERROR", run_id=run_id, path=relative))
            return None
        try:
            artifact = _load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            self.issues.append(_issue("MISSING_ARTIFACT", "ERROR", run_id=run_id, path=relative, detail=str(exc)))
            return None
        declared_status = records[0].get("status")
        if declared_status != artifact.get("status"):
            self.issues.append(_issue("ARTIFACT_STATUS_MISMATCH", "ERROR", run_id=run_id, kind=kind, declared_status=declared_status, artifact_status=artifact.get("status")))
            artifact["_manifest_status_mismatch"] = True
        self._check_raw_refs(run_id, artifact)
        self.artifacts[cache_key] = artifact
        return artifact

    def _check_raw_refs(self, run_id: str, artifact: Mapping[str, Any]) -> None:
        refs = list(artifact.get("derived_from") or [])
        data = artifact.get("data") if isinstance(artifact.get("data"), Mapping) else {}
        for item in data.get("items") or []:
            if isinstance(item, Mapping):
                refs.extend(item.get("source_refs") or [])
        for ref in sorted({str(ref) for ref in refs if str(ref).startswith("raw/")}):
            run_root = (self.data_root / "runs" / run_id).resolve()
            path = (run_root / ref).resolve()
            if not _is_within(run_root / "raw", path):
                self.issues.append(_issue("UNSAFE_PATH_REF", "ERROR", run_id=run_id, path=ref))
            elif not path.is_file():
                self.issues.append(_issue("MISSING_RAW_REF", "ERROR", run_id=run_id, path=ref))


def _build_evidence_map(incidents, canonical_windows, candidates, traces, call_trees, sources, rejected_traces):
    output = []
    for incident_id in sorted(incidents):
        candidate_rows = [value["extraction"] for value in candidates.values() if value["extraction"]["incident_id"] == incident_id]
        trace_rows = [value["extraction"] for value in traces.values() if value["extraction"]["incident_id"] == incident_id]
        tree_rows = [value["extraction"] for value in call_trees.values() if value["extraction"]["incident_id"] == incident_id]
        source_rows = [value["extraction"] for value in sources.values() if value["extraction"]["incident_id"] == incident_id]
        links = _unique_objects(link for row in candidate_rows for link in row.get("links") or [])
        window_rows = [item for item in canonical_windows if incident_id in item.get("incident_ids", [])]
        windows = [item["window_id"] for item in window_rows]
        valid_windows = [item["window_id"] for item in window_rows if item.get("context_status") == "SUCCESS"]
        gaps = []
        if windows and not valid_windows:
            gaps.append("historical_window_rejected")
        if not candidate_rows:
            gaps.append("candidate_evidence_missing")
        if not trace_rows:
            gaps.append("target_correct_trace_missing")
        if trace_rows and not tree_rows:
            gaps.append("target_correct_call_tree_missing")
        if not links:
            gaps.append("verified_url_missing")
        output.append({
            "incident_id": incident_id,
            "alarm_seed_ids": sorted(incidents[incident_id].get("alarm_seed_ids") or []),
            "window_ids": sorted(windows),
            "valid_window_ids": sorted(valid_windows),
            "window_contexts": [{"window_id": row["window_id"], "status": row.get("context_status", "REJECTED")} for row in window_rows],
            "candidate_bindings": [{"binding_id": row["binding_id"], "collect_run_id": row["collect_run_id"], "item_ref": row["item_ref"], "extraction_ref": f"extractions/candidates/{row['binding_id']}.json"} for row in candidate_rows],
            "trace_runs": [{"trace_run_id": row["trace_run_id"], "candidate_binding_id": row["candidate_binding_id"], "target_match": row["target_match"], "extraction_ref": f"extractions/traces/{row['trace_run_id']}.json"} for row in trace_rows],
            "call_tree_runs": [{"call_tree_run_id": row["call_tree_run_id"], "trace_run_id": row["trace_run_id"], "extraction_ref": f"extractions/call-trees/{row['call_tree_run_id']}.json"} for row in tree_rows],
            "source_runs": [{"source_run_id": row["source_run_id"], "role": row["role"], "extraction_ref": f"extractions/{_source_directory(row['role'])}/{row['source_run_id']}.json"} for row in source_rows],
            "links": links,
            "evidence_gaps": gaps,
            "has_evidence": bool(candidate_rows or trace_rows or tree_rows or source_rows),
        })
    return {"schema_version": 1, "incidents": output, "rejected_trace_runs": rejected_traces}


def _build_coverage(evidence_map):
    incidents = []
    for item in evidence_map["incidents"]:
        has_trace = bool(item["trace_runs"])
        has_tree = bool(item["call_tree_runs"])
        has_source = bool(item["source_runs"])
        deep_count = sum((has_trace, has_tree, has_source))
        incidents.append({
            "incident_id": item["incident_id"],
            "inventory": {"status": "SUCCESS" if item["alarm_seed_ids"] else "MISSING"},
            "context": {"status": "SUCCESS" if item.get("valid_window_ids") else "REJECTED" if item["window_ids"] else "MISSING"},
            "candidate": {"status": "SUCCESS" if item["candidate_bindings"] else "MISSING"},
            "deep_evidence": {"status": "SUCCESS" if deep_count == 3 else "PARTIAL" if deep_count else "MISSING"},
        })
    return {"schema_version": 1, "incidents": incidents}


def _build_readiness(evidence_map, candidates, traces, call_trees, sources):
    output = []
    for item in evidence_map["incidents"]:
        incident_id = item["incident_id"]
        candidate_rows = [value["extraction"] for value in candidates.values() if value["extraction"]["incident_id"] == incident_id]
        trace_rows = [value["extraction"] for value in traces.values() if value["extraction"]["incident_id"] == incident_id]
        tree_rows = [value["extraction"] for value in call_trees.values() if value["extraction"]["incident_id"] == incident_id]
        source_rows = [value["extraction"] for value in sources.values() if value["extraction"]["incident_id"] == incident_id]
        has_metrics = any(row.get("metrics") for row in candidate_rows)
        has_alarm_inventory = bool(item["alarm_seed_ids"])
        has_valid_context = bool(item.get("valid_window_ids"))
        has_trace = bool(trace_rows)
        has_tree = bool(tree_rows)
        has_verified_url = bool(item["links"])
        has_upstream_downstream = any(row.get("major_downstream_spans") for row in tree_rows) or any(row.get("topology") or row.get("service_flow") or row.get("request_service_flow") for row in trace_rows) or any(row.get("role") == "external_calls" for row in source_rows)
        has_gap_accounting = isinstance(item.get("evidence_gaps"), list)
        simple_requirements = {
            "alarm_inventory": has_alarm_inventory,
            "alarm_distribution": has_alarm_inventory,
            "important_incident": bool(incident_id),
            "incident_summary": bool(incident_id),
            "candidate_metrics": has_metrics,
            "key_trace": has_trace,
            "important_upstream_downstream": has_upstream_downstream,
            "verified_url": has_verified_url,
            "key_links": has_verified_url,
            "evidence_gap_accounting": has_gap_accounting,
            "evidence_gaps": has_gap_accounting,
        }
        simple_status = _readiness_status(simple_requirements)
        deep_spans = any(row.get("all_spans") for row in tree_rows)
        sql_or_external = any(row.get("database_spans") or row.get("http_spans") for row in tree_rows) or bool(source_rows)
        counter_signals = any("ERROR_FLAG_FALSE_LOG_EVENT" in (row.get("exception_signal_types") or []) or row.get("sample_assessment", {}).get("sample_assessment") == "NORMAL_CONTRAST" for row in trace_rows)
        unknowns = bool(item["evidence_gaps"]) or any((row.get("metrics", {}).get("exception_count") or {}).get("semantic_status") == "UNKNOWN" for row in candidate_rows)
        raw_lineage = any(row.get("source_refs") for row in candidate_rows) and any(row.get("source_refs") for row in trace_rows) and any(span.get("evidence_ref") for row in tree_rows for span in row.get("all_spans") or [])
        evidence_chain = has_alarm_inventory and has_valid_context and bool(candidate_rows) and has_trace and has_tree and raw_lineage
        deep_requirements = {
            "alarm_seed": has_alarm_inventory,
            "historical_context": has_valid_context,
            "candidate_aggregate": has_metrics,
            "trace_sample": bool(trace_rows),
            "sample_assessment": any(row.get("sample_assessment") for row in trace_rows),
            "call_tree": bool(tree_rows),
            "deep_spans": deep_spans,
            "sql_or_external": sql_or_external,
            "counter_signals": counter_signals,
            "unknowns": unknowns,
            "evidence_chain": evidence_chain,
        }
        output.append({"incident_id": incident_id, "simple": {"status": simple_status, "requirements": simple_requirements}, "deep": {"status": _readiness_status(deep_requirements), "requirements": deep_requirements}})
    return {"schema_version": 1, "incidents": output}


def _readiness_status(requirements):
    count = sum(bool(value) for value in requirements.values())
    if count == len(requirements):
        return "READY"
    return "PARTIAL" if count else "NOT_READY"


def _validate_manifest(manifest: Mapping[str, Any]) -> List[Dict[str, Any]]:
    issues = []
    if manifest.get("schema_version") != 1 or not manifest.get("investigation_id"):
        issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", field="schema_version_or_investigation_id"))
    for field in ("alarm_seeds", "incidents", "windows", "candidate_bindings", "trace_bindings", "call_tree_bindings", "source_bindings"):
        if not isinstance(manifest.get(field), list):
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", field=field))
    if issues:
        return issues
    seeds = _unique_ids(manifest["alarm_seeds"], "alarm_seed_id", issues)
    incidents = _unique_ids(manifest["incidents"], "incident_id", issues)
    windows = _unique_ids(manifest["windows"], "window_id", issues)
    bindings = _unique_ids(manifest["candidate_bindings"], "binding_id", issues)
    for item in manifest["alarm_seeds"]:
        if not isinstance(item, Mapping) or not all(item.get(field) not in (None, "") for field in ("alarm_seed_id", "occurred_at", "business_system_name", "object_name")):
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", registry="alarm_seeds", item=item.get("alarm_seed_id") if isinstance(item, Mapping) else None))
    for item in manifest["incidents"]:
        if not isinstance(item, Mapping) or item.get("kind") not in INCIDENT_KINDS or not isinstance(item.get("alarm_seed_ids"), list) or any(seed not in seeds for seed in item.get("alarm_seed_ids") or []):
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", registry="incidents", item=item.get("incident_id") if isinstance(item, Mapping) else None))
    for item in manifest["windows"]:
        if not isinstance(item, Mapping) or not item.get("collect_run_id") or not isinstance(item.get("incident_ids"), list) or not isinstance(item.get("alarm_seed_ids"), list) or any(value not in incidents for value in item.get("incident_ids") or []) or any(value not in seeds for value in item.get("alarm_seed_ids") or []):
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", registry="windows", item=item.get("window_id") if isinstance(item, Mapping) else None))
    for item in manifest["candidate_bindings"]:
        if not isinstance(item, Mapping) or item.get("incident_id") not in incidents or item.get("window_id") not in windows or item.get("alarm_seed_id") not in seeds or not item.get("collect_run_id") or not item.get("item_ref") or item.get("match_level") not in {"EXACT", "STRONG"}:
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", registry="candidate_bindings", item=item.get("binding_id") if isinstance(item, Mapping) else None))
    for item in manifest["trace_bindings"]:
        if not isinstance(item, Mapping) or not item.get("trace_run_id") or item.get("incident_id") not in incidents or item.get("candidate_binding_id") not in bindings or item.get("target_match") not in {"EXACT", "STRONG"}:
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", registry="trace_bindings", item=item.get("trace_run_id") if isinstance(item, Mapping) else None))
    for item in manifest["call_tree_bindings"]:
        if not isinstance(item, Mapping) or not all(item.get(field) not in (None, "") for field in ("incident_id", "trace_run_id", "call_tree_run_id")) or item.get("incident_id") not in incidents:
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", registry="call_tree_bindings", item=item.get("call_tree_run_id") if isinstance(item, Mapping) else None))
    for item in manifest["source_bindings"]:
        if not isinstance(item, Mapping) or not all(item.get(field) not in (None, "") for field in ("incident_id", "source_run_id", "role")) or item.get("incident_id") not in incidents or item.get("role") not in SOURCE_ROLES:
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", registry="source_bindings", item=item.get("source_run_id") if isinstance(item, Mapping) else None))
    return issues


def _unique_ids(items, field, issues):
    values = []
    for item in items:
        value = item.get(field) if isinstance(item, Mapping) else None
        if not value or value in values:
            issues.append(_issue("INVALID_INVESTIGATION_MANIFEST", "ERROR", registry=field, item=value, reason="missing_or_duplicate"))
        else:
            values.append(value)
    return set(values)


def _find_item(artifact, item_ref, source_run_id):
    if not isinstance(artifact, Mapping):
        return None
    data = artifact.get("data") if isinstance(artifact.get("data"), Mapping) else {}
    for item in data.get("items") or []:
        if isinstance(item, Mapping) and item.get("item_ref") == item_ref and item.get("source_run_id") == source_run_id:
            return dict(item)
    return None


def _verified_links(item):
    if (item.get("navigation") or {}).get("status") != "SUCCESS":
        return []
    return [dict(link) for link in item.get("links") or [] if isinstance(link, Mapping) and link.get("verification") in VERIFIED_LINK_PROOFS]


def _artifact_status_usable(artifact):
    return isinstance(artifact, Mapping) and artifact.get("status") == "SUCCESS" and not artifact.get("_manifest_status_mismatch")


def _source_directory(role):
    if role == "external_calls":
        return "external"
    if role.startswith("recent_requests"):
        return "recent-requests"
    if role.startswith("performance_") or role == "alarm_metric_series":
        return "timeseries"
    if role == "application_instances":
        return "topology"
    return "external"


def _prepare_output(output_dir):
    if output_dir.exists():
        if not output_dir.is_dir() or any(output_dir.iterdir()):
            raise CompositionError("OUTPUT_DIR_NOT_EMPTY")
        output_dir.rmdir()


def _is_within(root: Path, candidate: Path) -> bool:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    return resolved_candidate == resolved_root or resolved_root in resolved_candidate.parents


def _contains(actual, expected):
    if isinstance(expected, Mapping):
        return isinstance(actual, Mapping) and all(key in actual and _contains(actual[key], value) for key, value in expected.items())
    return actual == expected


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _hash_object(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _issue(code, severity, **context):
    return {"code": code, "severity": severity, "context": context}


def _dedupe_issues(issues):
    unique = {}
    for item in issues:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        unique[key] = item
    order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    return sorted(unique.values(), key=lambda item: (order.get(item["severity"], 9), item["code"], json.dumps(item.get("context") or {}, sort_keys=True)))


def _unique_objects(values):
    unique = {}
    for value in values:
        unique[json.dumps(value, ensure_ascii=False, sort_keys=True)] = dict(value)
    return [unique[key] for key in sorted(unique)]
