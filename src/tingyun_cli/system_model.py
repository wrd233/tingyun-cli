from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .evidence_extraction import extract_call_tree
from .manifest_schema import validate_schema


SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"
SCHEMA_PATH = SCHEMA_ROOT / "system-model-manifest.schema.json"
SNAPSHOT_SCHEMA_PATH = SCHEMA_ROOT / "system-model-snapshot.schema.json"
VALIDATION_SCHEMA_PATH = SCHEMA_ROOT / "system-model-validation.schema.json"
DIFF_SCHEMA_PATH = SCHEMA_ROOT / "system-model-diff.schema.json"
MODELED_ARTIFACTS = {
    "targets", "topology", "performance", "candidates", "trace", "call_tree",
    "alarm_events", "alarm_detail", "alarm_metric_series", "instance_context",
    "external_calls", "trace_exceptions", "trace_stack",
}
ARTIFACT_DEPENDENCY_ORDER = {
    "targets": 0,
    "topology": 1,
    "candidates": 2,
    "performance": 3,
    "trace": 4,
    "call_tree": 5,
    "external_calls": 6,
    "instance_context": 6,
    "alarm_events": 6,
    "alarm_detail": 7,
    "alarm_metric_series": 8,
    "trace_exceptions": 8,
    "trace_stack": 8,
}


class SystemModelError(Exception):
    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(message or code)
        self.code = code


def compile_system_model(manifest_path: Path, *, data_root: Path, output_dir: Path) -> Dict[str, Any]:
    """Compile explicit immutable Runs into one deterministic system snapshot."""
    manifest_path, data_root, output_dir = Path(manifest_path), Path(data_root), Path(output_dir)
    _prepare_output(output_dir, data_root)
    manifest = _read_json_or_error(manifest_path, "INVALID_SYSTEM_MODEL_MANIFEST")
    schema = _read_json_or_error(SCHEMA_PATH, "SYSTEM_MODEL_SCHEMA_UNAVAILABLE")
    violations = validate_schema(manifest, schema)
    if violations:
        raise SystemModelError("INVALID_SYSTEM_MODEL_MANIFEST", json.dumps(violations, sort_keys=True))
    builder = _ModelBuilder(manifest, data_root)
    snapshot, issues = builder.compile()
    issues.extend(_schema_issues(snapshot, SNAPSHOT_SCHEMA_PATH, "SNAPSHOT_SCHEMA_VIOLATION"))
    issues = _sorted_issues(issues)
    _write_json(output_dir / "snapshot.json", snapshot)
    snapshot_hash = _sha256(output_dir / "snapshot.json")
    validation = {
        "schema_version": 1,
        "kind": "system_model_validation",
        "status": "FAIL" if _has_errors(issues) else "PASS",
        "snapshot_sha256": snapshot_hash,
        "issues": issues,
    }
    validation_schema_issues = _schema_issues(validation, VALIDATION_SCHEMA_PATH, "VALIDATION_SCHEMA_VIOLATION")
    if validation_schema_issues:
        validation["status"] = "FAIL"
        validation["issues"] = _sorted_issues(validation["issues"] + validation_schema_issues)
    _write_json(output_dir / "validation.json", validation)
    status = "FAILED" if _has_errors(validation["issues"]) else "SUCCESS"
    return {
        "schema_version": 1,
        "command": "system-model compile",
        "status": status,
        "actual_request_count": 0,
        "snapshot_path": str(output_dir / "snapshot.json"),
        "validation_path": str(output_dir / "validation.json"),
        "entity_count": len(snapshot["entities"]),
        "relation_count": len(snapshot["relations"]),
    }


def validate_system_model(compiled_dir: Path) -> Dict[str, Any]:
    root = Path(compiled_dir)
    issues: List[Dict[str, Any]] = []
    try:
        snapshot = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema_version": 1, "status": "FAIL", "issues": [_issue("INVALID_SNAPSHOT_JSON", "ERROR", detail=str(exc))]}
    try:
        validation = json.loads((root / "validation.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        validation = {}
        issues.append(_issue("INVALID_VALIDATION_JSON", "ERROR", detail=str(exc)))
    expected_hash = validation.get("snapshot_sha256") if isinstance(validation, Mapping) else None
    if not expected_hash or _sha256(root / "snapshot.json") != expected_hash:
        issues.append(_issue("SNAPSHOT_HASH_MISMATCH", "ERROR"))
    issues.extend(_schema_issues(snapshot, SNAPSHOT_SCHEMA_PATH, "SNAPSHOT_SCHEMA_VIOLATION"))
    issues.extend(_schema_issues(validation, VALIDATION_SCHEMA_PATH, "VALIDATION_SCHEMA_VIOLATION"))
    issues.extend(_snapshot_integrity_issues(snapshot))
    validation_issues = validation.get("issues", []) if isinstance(validation, Mapping) else []
    if any(isinstance(item, Mapping) and item.get("severity") == "ERROR" for item in validation_issues):
        issues.append(_issue("COMPILED_SYSTEM_MODEL_VALIDATION_ERROR", "ERROR"))
    issues = _sorted_issues(issues)
    return {"schema_version": 1, "status": "FAIL" if _has_errors(issues) else "PASS", "issues": issues}


def diff_system_models(before_path: Path, after_path: Path) -> Dict[str, Any]:
    before, after = _read_json_or_error(Path(before_path), "INVALID_SYSTEM_MODEL_SNAPSHOT"), _read_json_or_error(Path(after_path), "INVALID_SYSTEM_MODEL_SNAPSHOT")
    before_violations = _schema_issues(before, SNAPSHOT_SCHEMA_PATH, "INVALID_BEFORE_SNAPSHOT")
    after_violations = _schema_issues(after, SNAPSHOT_SCHEMA_PATH, "INVALID_AFTER_SNAPSHOT")
    before_violations.extend(
        _issue("INVALID_BEFORE_SNAPSHOT_INTEGRITY", "ERROR", issue=issue)
        for issue in _snapshot_integrity_issues(before)
        if issue.get("severity") == "ERROR"
    )
    after_violations.extend(
        _issue("INVALID_AFTER_SNAPSHOT_INTEGRITY", "ERROR", issue=issue)
        for issue in _snapshot_integrity_issues(after)
        if issue.get("severity") == "ERROR"
    )
    if before_violations or after_violations:
        raise SystemModelError("INVALID_SYSTEM_MODEL_SNAPSHOT", json.dumps(_sorted_issues(before_violations + after_violations), sort_keys=True))
    before_entities, after_entities = _index(before.get("entities", []), "entity_id"), _index(after.get("entities", []), "entity_id")
    before_relations, after_relations = _index(before.get("relations", []), "relation_id"), _index(after.get("relations", []), "relation_id")
    entity_before, entity_after = set(before_entities), set(after_entities)
    relation_before, relation_after = set(before_relations), set(after_relations)
    result = {
        "schema_version": 1,
        "kind": "system_model_diff",
        "status": "SUCCESS",
        "actual_request_count": 0,
        "before_snapshot_id": before.get("snapshot_id"),
        "after_snapshot_id": after.get("snapshot_id"),
        "entities": {
            "added": sorted(entity_after - entity_before),
            "not_observed": sorted(entity_before - entity_after),
            "not_observed_interpretation": "NOT_OBSERVED_IN_AFTER_INPUTS",
            "changed": sorted(item_id for item_id in entity_before & entity_after if before_entities[item_id] != after_entities[item_id]),
        },
        "relations": {
            "added": sorted(relation_after - relation_before),
            "not_observed": sorted(relation_before - relation_after),
            "not_observed_interpretation": "NOT_OBSERVED_IN_AFTER_INPUTS",
            "changed": sorted(item_id for item_id in relation_before & relation_after if before_relations[item_id] != after_relations[item_id]),
        },
        "coverage_change": {"before": before.get("coverage"), "after": after.get("coverage")},
        "new_conflicts": [item for item in after.get("conflicts", []) if item not in before.get("conflicts", [])],
    }
    violations = _schema_issues(result, DIFF_SCHEMA_PATH, "DIFF_SCHEMA_VIOLATION")
    if violations:
        raise SystemModelError("INVALID_SYSTEM_MODEL_DIFF", json.dumps(violations, sort_keys=True))
    return result


class _ModelBuilder:
    def __init__(self, manifest: Mapping[str, Any], data_root: Path):
        self.manifest = dict(manifest)
        self.data_root = data_root
        self.issues: List[Dict[str, Any]] = []
        self.run_manifests: Dict[str, Dict[str, Any]] = {}
        self.artifacts: List[Tuple[str, str, Dict[str, Any]]] = []
        self.items: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.relations: Dict[str, Dict[str, Any]] = {}
        self.conflicts: List[Dict[str, Any]] = []
        self.artifact_statuses: Dict[str, int] = {}
        self.unmodeled: set = set()

    def compile(self) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        self._load_runs()
        self._index_items()
        ordered_artifacts = sorted(
            self.artifacts,
            key=lambda record: (
                ARTIFACT_DEPENDENCY_ORDER.get(str(record[2].get("kind") or Path(record[1]).stem), 99),
                record[0],
                record[1],
            ),
        )
        for run_id, artifact_path, artifact in ordered_artifacts:
            kind = str(artifact.get("kind") or Path(artifact_path).stem)
            if kind not in MODELED_ARTIFACTS:
                self.unmodeled.add(kind)
                continue
            if artifact.get("status") != "SUCCESS":
                continue
            handler = getattr(self, f"_consume_{kind}", None)
            if handler:
                handler(run_id, artifact_path, artifact)
            else:
                self.unmodeled.add(kind)
        entities = [self._final_entity(item) for item in self.entities.values()]
        relations = [self._final_relation(item) for item in self.relations.values()]
        source_runs = []
        for run_id in sorted(self.run_manifests):
            manifest_path = self.data_root / "runs" / run_id / "manifest.json"
            source_runs.append({
                "run_id": run_id,
                "run_type": self.run_manifests[run_id].get("run_type"),
                "overall": self.run_manifests[run_id].get("overall"),
                "manifest_sha256": _sha256(manifest_path),
                "time_context": self._run_time_context(run_id),
            })
        snapshot = {
            "schema_version": 1,
            "model_version": "v0",
            "kind": "evidence_backed_living_system_model",
            "snapshot_id": self.manifest["snapshot_id"],
            "as_of": self.manifest["as_of"],
            "freshness_threshold_seconds": self.manifest["freshness_threshold_seconds"],
            "source_manifest_sha256": _fingerprint(self.manifest),
            "source_runs": source_runs,
            "entities": sorted(entities, key=lambda item: item["entity_id"]),
            "relations": sorted(relations, key=lambda item: item["relation_id"]),
            "coverage": {
                "status": "PARTIAL",
                "declared_run_count": len(self.manifest["run_refs"]),
                "accepted_run_count": len(self.run_manifests),
                "artifact_statuses": dict(sorted(self.artifact_statuses.items())),
                "modeled_entity_types": sorted(set(item["entity_type"] for item in entities)),
                "modeled_relation_types": sorted(set(item["relation_type"] for item in relations)),
                "unmodeled_artifact_kinds": sorted(self.unmodeled),
                "interpretation": "Explicit input coverage only; absent evidence means NOT_OBSERVED, not deleted or nonexistent.",
            },
            "conflicts": sorted(self.conflicts, key=lambda item: _fingerprint(item)),
            "boundaries": {
                "http_requests": 0,
                "llm_calls": 0,
                "generates_rca": False,
                "generates_report": False,
                "infers_identity_from_name_or_ip": False,
            },
        }
        self.issues.extend(_snapshot_integrity_issues(snapshot))
        return snapshot, _sorted_issues(self.issues)

    def _load_runs(self) -> None:
        for run_ref in sorted(self.manifest["run_refs"], key=lambda item: item["run_id"]):
            run_id = str(run_ref["run_id"])
            run_path = self.data_root / "runs" / run_id
            manifest_path = run_path / "manifest.json"
            if not _within(self.data_root / "runs", manifest_path) or not manifest_path.is_file():
                self.issues.append(_issue("MISSING_SOURCE_RUN", "ERROR", run_id=run_id))
                continue
            actual_hash = _sha256(manifest_path)
            if run_ref.get("expected_manifest_sha256") and run_ref["expected_manifest_sha256"] != actual_hash:
                self.issues.append(_issue("SOURCE_RUN_HASH_MISMATCH", "ERROR", run_id=run_id))
                continue
            try:
                run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self.issues.append(_issue("INVALID_SOURCE_RUN_MANIFEST", "ERROR", run_id=run_id, detail=str(exc)))
                continue
            if run_manifest.get("run_id") != run_id:
                self.issues.append(_issue("SOURCE_RUN_ID_MISMATCH", "ERROR", run_id=run_id))
                continue
            self.run_manifests[run_id] = run_manifest
            for declared in run_manifest.get("artifacts", []):
                artifact_path = str(declared.get("path") or "")
                target = run_path / artifact_path
                if not artifact_path or not _within(run_path, target) or not target.is_file():
                    self.issues.append(_issue("MISSING_SOURCE_ARTIFACT", "ERROR", run_id=run_id, artifact_path=artifact_path))
                    continue
                try:
                    artifact = json.loads(target.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    self.issues.append(_issue("INVALID_SOURCE_ARTIFACT", "ERROR", run_id=run_id, artifact_path=artifact_path, detail=str(exc)))
                    continue
                if declared.get("status") != artifact.get("status"):
                    self.issues.append(_issue("ARTIFACT_STATUS_MISMATCH", "ERROR", run_id=run_id, artifact_path=artifact_path))
                    continue
                status_key = f"{artifact.get('kind') or declared.get('kind')}:{artifact.get('status')}"
                self.artifact_statuses[status_key] = self.artifact_statuses.get(status_key, 0) + 1
                status = str(artifact.get("status") or "")
                raw_valid = status in {"BLOCKED", "SKIPPED"} or self._validate_raw_refs(run_id, artifact_path, artifact)
                if raw_valid:
                    self.artifacts.append((run_id, artifact_path, artifact))

    def _validate_raw_refs(self, run_id: str, artifact_path: str, artifact: Mapping[str, Any]) -> bool:
        run_path = self.data_root / "runs" / run_id
        refs = list(artifact.get("derived_from") or [])
        for item in _artifact_items(artifact):
            refs.extend(item.get("source_refs") or [])
        if not refs:
            self.issues.append(_issue("MISSING_RAW_EVIDENCE", "ERROR", run_id=run_id, artifact_path=artifact_path, reason="NO_RAW_REFERENCE"))
            return False
        valid = True
        for raw_ref in sorted(set(str(value) for value in refs)):
            target = run_path / raw_ref
            if not _within(run_path, target) or not target.is_file():
                self.issues.append(_issue("MISSING_RAW_EVIDENCE", "ERROR", run_id=run_id, artifact_path=artifact_path, raw_ref=raw_ref))
                valid = False
        return valid

    def _index_items(self) -> None:
        for run_id, _, artifact in self.artifacts:
            for item in _artifact_items(artifact):
                if item.get("item_ref"):
                    self.items[(run_id, str(item["item_ref"]))] = item

    def _consume_targets(self, run_id, path, artifact):
        for item in _artifact_items(artifact):
            biz_id = _identity(item).get("bizSystemId")
            if biz_id not in (None, ""):
                self._entity(_biz_id(biz_id), "BUSINESS_SYSTEM", {"business_system_id": str(biz_id)}, {"name": item.get("display_name")}, self._evidence(run_id, path, item), self._run_time_context(run_id))

    def _consume_candidates(self, run_id, path, artifact):
        for item in _artifact_items(artifact):
            identity = _identity(item)
            biz, app, action = identity.get("bizSystemId"), identity.get("applicationId"), identity.get("actionId")
            evidence, time_context = self._evidence(run_id, path, item), artifact.get("time_context") or self._run_time_context(run_id)
            if biz in (None, ""):
                continue
            self._entity(_biz_id(biz), "BUSINESS_SYSTEM", {"business_system_id": str(biz)}, {}, evidence, time_context)
            if app in (None, ""):
                continue
            app_id = _app_id(biz, app)
            self._entity(app_id, "APPLICATION", {"business_system_id": str(biz), "application_id": str(app)}, {"name": (item.get("labels") or {}).get("applicationName")}, evidence, time_context)
            self._relation(_biz_id(biz), "CONTAINS", app_id, "STABLE_OWNERSHIP_OBSERVATION", evidence, time_context)
            if action in (None, ""):
                continue
            action_id = _action_id(biz, app, action)
            observation = {"time_context": time_context, "metrics": item.get("metrics") or {}, "evidence_ref": evidence}
            self._entity(action_id, "ACTION", {"business_system_id": str(biz), "application_id": str(app), "action_id": str(action)}, {"name": item.get("name")}, evidence, time_context, observation=observation)
            self._relation(app_id, "OWNS", action_id, "STABLE_OWNERSHIP_OBSERVATION", evidence, time_context)

    def _consume_trace(self, run_id, path, artifact):
        for item in _artifact_items(artifact):
            identity = _identity(item)
            trace_id = identity.get("traceId")
            if trace_id in (None, ""):
                continue
            evidence, time_context = self._evidence(run_id, path, item), self._run_time_context(run_id)
            entity_id = _trace_id(trace_id)
            self._entity(entity_id, "TRACE", {"trace_id": str(trace_id)}, {"name": (item.get("summary") or {}).get("actionName")}, evidence, time_context, observation={"time_context": time_context, "summary": item.get("summary") or {}, "evidence_ref": evidence})
            source = self.run_manifests.get(run_id, {}).get("source") or {}
            candidate = self.items.get((str(source.get("run_id")), str(source.get("item_ref"))))
            if candidate:
                source_identity = _identity(candidate)
                if all(source_identity.get(field) not in (None, "") for field in ("bizSystemId", "applicationId", "actionId")):
                    action_id = _action_id(source_identity["bizSystemId"], source_identity["applicationId"], source_identity["actionId"])
                    if action_id in self.entities:
                        self._relation(action_id, "OBSERVED_TRACE", entity_id, "WINDOWED_RUNTIME_OBSERVATION", evidence, time_context)

    def _consume_call_tree(self, run_id, path, artifact):
        call_tree = (artifact.get("data") or {}).get("call_tree") or {}
        extracted = extract_call_tree(call_tree, evidence_ref=f"{run_id}:{path}")
        evidence, time_context = self._evidence(run_id, path, None, artifact), self._run_time_context(run_id)
        source = self.run_manifests.get(run_id, {}).get("source") or {}
        trace_item = self.items.get((str(source.get("run_id")), str(source.get("item_ref"))))
        trace_id = _identity(trace_item or {}).get("traceId")
        trace_entity_id = _trace_id(trace_id) if trace_id not in (None, "") else None
        for span in extracted["all_spans"]:
            node_id = f"trace_node:{run_id}:{span['node_id']}"
            observation = {"time_context": time_context, "metrics": {key: span.get(key) for key in ("total_time", "exclusive_time")}, "evidence_ref": evidence}
            self._entity(node_id, "TRACE_NODE", {"run_id": run_id, "node_id": span["node_id"]}, {"name": span.get("name"), "type": span.get("type")}, evidence, time_context, observation=observation)
        for span in extracted["all_spans"]:
            node_id = f"trace_node:{run_id}:{span['node_id']}"
            if span.get("parent"):
                parent_id = f"trace_node:{run_id}:{span['parent']}"
                self._relation(parent_id, "CALLS", node_id, "WINDOWED_RUNTIME_OBSERVATION", evidence, time_context)
            elif trace_entity_id and trace_entity_id in self.entities:
                self._relation(trace_entity_id, "CONTAINS_NODE", node_id, "WINDOWED_RUNTIME_OBSERVATION", evidence, time_context)

    def _consume_external_calls(self, run_id, path, artifact):
        source = self.run_manifests.get(run_id, {}).get("source") or {}
        candidate = self.items.get((str(source.get("run_id")), str(source.get("item_ref"))))
        candidate_identity = _identity(candidate or {})
        if not all(candidate_identity.get(field) not in (None, "") for field in ("bizSystemId", "applicationId")):
            return
        app_id = _app_id(candidate_identity["bizSystemId"], candidate_identity["applicationId"])
        for item in _artifact_items(artifact):
            evidence, time_context = self._evidence(run_id, path, item), self._run_time_context(run_id)
            external_id = f"external:{run_id}:{item.get('item_ref')}"
            self._entity(external_id, "EXTERNAL_SERVICE", {"source_run_id": run_id, "source_item_ref": item.get("item_ref")}, {"name": item.get("name"), "uri": item.get("dependency_uri")}, evidence, time_context, observation={"time_context": time_context, "metrics": item.get("metrics") or {}, "evidence_ref": evidence})
            if app_id in self.entities:
                self._relation(app_id, "OBSERVED_EXTERNAL_CALL", external_id, "WINDOWED_RUNTIME_OBSERVATION", evidence, time_context)

    def _consume_instance_context(self, run_id, path, artifact):
        for item in _artifact_items(artifact):
            identity = item.get("identity") or {}
            biz, app, instance = identity.get("business_system_id"), identity.get("application_id"), identity.get("instance_id")
            if any(value in (None, "") for value in (biz, app, instance)):
                continue
            evidence, time_context = self._evidence(run_id, path, item), self._run_time_context(run_id)
            app_id, entity_id = _app_id(biz, app), f"instance:{biz}:{app}:{instance}"
            self._entity(entity_id, "INSTANCE_CANDIDATE", {"business_system_id": str(biz), "application_id": str(app), "instance_id": str(instance)}, {"name": item.get("name")}, evidence, time_context)
            if app_id in self.entities:
                self._relation(app_id, "OBSERVED_INSTANCE", entity_id, "WINDOWED_RUNTIME_OBSERVATION", evidence, time_context)

    def _consume_alarm_events(self, run_id, path, artifact):
        self._consume_alarms(run_id, path, artifact)

    def _consume_alarm_detail(self, run_id, path, artifact):
        self._consume_alarms(run_id, path, artifact)

    def _consume_alarms(self, run_id, path, artifact):
        for item in _artifact_items(artifact):
            identity = _identity(item)
            alarm_id = identity.get("alarmEventId")
            if alarm_id in (None, ""):
                continue
            evidence, time_context = self._evidence(run_id, path, item), self._run_time_context(run_id)
            entity_id = f"alarm:{alarm_id}"
            self._entity(entity_id, "ALARM", {"alarm_id": str(alarm_id)}, {"name": item.get("name")}, evidence, time_context)
            biz, app, action = identity.get("bizSystemId"), identity.get("applicationId"), identity.get("actionId")
            target = _action_id(biz, app, action) if all(value not in (None, "") for value in (biz, app, action)) else _app_id(biz, app) if all(value not in (None, "") for value in (biz, app)) else None
            if target and target in self.entities:
                self._relation(entity_id, "TARGETS", target, "WINDOWED_RUNTIME_OBSERVATION", evidence, time_context)

    def _consume_topology(self, run_id, path, artifact):
        data = artifact.get("data") or {}
        evidence, time_context = self._evidence(run_id, path, None, artifact), artifact.get("time_context") or self._run_time_context(run_id)
        node_ids = {}
        for index, node in enumerate(data.get("structural_nodes") or [], 1):
            if not isinstance(node, Mapping):
                continue
            observed_id = node.get("id") or node.get("key")
            if observed_id in (None, ""):
                continue
            entity_id = f"topology_node:{run_id}:{observed_id}"
            node_ids[str(observed_id)] = entity_id
            self._entity(entity_id, "TOPOLOGY_NODE", {"run_id": run_id, "observed_node_id": str(observed_id)}, {"name": node.get("name"), "type": node.get("type")}, evidence, time_context)
        for index, edge in enumerate(data.get("runtime_edges") or [], 1):
            if not isinstance(edge, Mapping):
                continue
            source_id = edge.get("from") or edge.get("source") or edge.get("fromId")
            target_id = edge.get("to") or edge.get("target") or edge.get("toId")
            if str(source_id) in node_ids and str(target_id) in node_ids:
                self._relation(node_ids[str(source_id)], "CALLS", node_ids[str(target_id)], "WINDOWED_RUNTIME_OBSERVATION", evidence, time_context, observation={"metrics": dict(edge)})

    def _consume_performance(self, run_id, path, artifact):
        scope = artifact.get("scope") or {}
        biz = scope.get("business_system_id") or scope.get("bizSystemId")
        if biz in (None, "") or _biz_id(biz) not in self.entities:
            return
        evidence, time_context = self._evidence(run_id, path, None, artifact), artifact.get("time_context") or self._run_time_context(run_id)
        self._entity(_biz_id(biz), "BUSINESS_SYSTEM", {"business_system_id": str(biz)}, {}, evidence, time_context, observation={"time_context": time_context, "metrics": (artifact.get("data") or {}).get("metrics") or {}, "evidence_ref": evidence})

    def _consume_alarm_metric_series(self, *args):
        self.unmodeled.add("alarm_metric_series")

    def _consume_trace_exceptions(self, *args):
        self.unmodeled.add("trace_exceptions")

    def _consume_trace_stack(self, *args):
        self.unmodeled.add("trace_stack")

    def _entity(self, entity_id, entity_type, canonical, display, evidence, time_context, *, observation=None):
        display = {key: value for key, value in display.items() if value not in (None, "")}
        current = self.entities.get(entity_id)
        if current is None:
            current = {"entity_id": entity_id, "entity_type": entity_type, "canonical_identity": canonical, "display_identity": display, "evidence_refs": [], "time_contexts": [], "observations": []}
            self.entities[entity_id] = current
        elif current["entity_type"] != entity_type or current["canonical_identity"] != canonical:
            self.conflicts.append({"code": "CANONICAL_IDENTITY_CONFLICT", "entity_id": entity_id, "existing": current["canonical_identity"], "observed": canonical})
            return
        for key, value in display.items():
            old = current["display_identity"].get(key)
            if old not in (None, "") and old != value:
                self.conflicts.append({"code": "DISPLAY_IDENTITY_CONFLICT", "entity_id": entity_id, "field": key, "existing": old, "observed": value})
            elif old in (None, ""):
                current["display_identity"][key] = value
        current["evidence_refs"].append(evidence)
        if time_context:
            current["time_contexts"].append(time_context)
        if observation:
            current["observations"].append(observation)

    def _relation(self, from_id, relation_type, to_id, time_semantics, evidence, time_context, *, observation=None):
        relation_id = f"{from_id}|{relation_type}|{to_id}"
        current = self.relations.setdefault(relation_id, {"relation_id": relation_id, "relation_type": relation_type, "from_entity_id": from_id, "to_entity_id": to_id, "time_semantics": time_semantics, "evidence_refs": [], "time_contexts": [], "observations": []})
        current["evidence_refs"].append(evidence)
        if time_context:
            current["time_contexts"].append(time_context)
        if observation:
            current["observations"].append(observation)

    def _final_entity(self, item):
        result = dict(item)
        result["evidence_refs"] = _unique(result["evidence_refs"])
        result["time_contexts"] = _unique(result["time_contexts"])
        result["observations"] = _unique(result["observations"])
        first, last = _observation_bounds(result["time_contexts"])
        result["first_observed"], result["last_observed"] = first, last
        result["verification_level"] = "RUNTIME_VALIDATED"
        result["freshness"] = _freshness(last, self.manifest["as_of"], self.manifest["freshness_threshold_seconds"])
        result["coverage"] = "OBSERVED"
        result["conflicts"] = [conflict for conflict in self.conflicts if conflict.get("entity_id") == result["entity_id"]]
        return result

    def _final_relation(self, item):
        result = dict(item)
        result["evidence_refs"] = _unique(result["evidence_refs"])
        result["time_contexts"] = _unique(result["time_contexts"])
        result["observations"] = _unique(result["observations"])
        result["time_context"] = result["time_contexts"][-1] if result["time_contexts"] else None
        result["verification_level"] = "RUNTIME_VALIDATED"
        result["coverage"] = "OBSERVED"
        return result

    def _evidence(self, run_id, artifact_path, item=None, artifact=None):
        raw_refs = list((item or {}).get("source_refs") or [])
        if not raw_refs:
            source_artifact = artifact
            if source_artifact is None:
                source_artifact = next(
                    (candidate for candidate_run, candidate_path, candidate in self.artifacts if candidate_run == run_id and candidate_path == artifact_path),
                    {},
                )
            raw_refs = list(source_artifact.get("derived_from") or [])
        result = {"run_id": run_id, "artifact_path": artifact_path, "raw_refs": sorted(str(value) for value in raw_refs)}
        if item and item.get("item_ref"):
            result["item_ref"] = item["item_ref"]
        return result

    def _run_time_context(self, run_id, seen=None):
        seen = set(seen or ())
        if run_id in seen:
            return None
        seen.add(run_id)
        manifest = self.run_manifests.get(run_id) or {}
        if manifest.get("time_context"):
            return manifest["time_context"]
        source = manifest.get("source") or {}
        source_run = source.get("run_id")
        return self._run_time_context(str(source_run), seen) if source_run else None


def _snapshot_integrity_issues(snapshot: Any) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    if not isinstance(snapshot, Mapping):
        return [_issue("INVALID_SNAPSHOT_TYPE", "ERROR")]
    raw_entities = snapshot.get("entities") or []
    raw_relations = snapshot.get("relations") or []
    entities = [item for item in raw_entities if isinstance(item, Mapping)] if isinstance(raw_entities, list) else []
    relations = [item for item in raw_relations if isinstance(item, Mapping)] if isinstance(raw_relations, list) else []
    entity_ids = [item.get("entity_id") for item in entities]
    relation_ids = [item.get("relation_id") for item in relations]
    if len(entity_ids) != len(set(entity_ids)):
        issues.append(_issue("DUPLICATE_ENTITY_ID", "ERROR"))
    if len(relation_ids) != len(set(relation_ids)):
        issues.append(_issue("DUPLICATE_RELATION_ID", "ERROR"))
    known_entities = set(entity_ids)
    source_runs = snapshot.get("source_runs") or []
    known_runs = {item.get("run_id") for item in source_runs if isinstance(item, Mapping)} if isinstance(source_runs, list) else set()
    for relation in relations:
        if relation.get("from_entity_id") not in known_entities or relation.get("to_entity_id") not in known_entities:
            issues.append(_issue("MISSING_RELATION_ENDPOINT", "ERROR", relation_id=relation.get("relation_id")))
        if relation.get("time_semantics") == "WINDOWED_RUNTIME_OBSERVATION" and not isinstance(relation.get("time_context"), Mapping):
            issues.append(_issue("MISSING_RUNTIME_TIME_CONTEXT", "ERROR", relation_id=relation.get("relation_id")))
    for owner_type, owners in (("entity", entities), ("relation", relations)):
        for owner in owners:
            evidence_refs = owner.get("evidence_refs")
            if not isinstance(evidence_refs, list) or not evidence_refs:
                issues.append(_issue("MISSING_EVIDENCE_REFERENCE", "ERROR", owner_type=owner_type, owner_id=owner.get(f"{owner_type}_id")))
                continue
            for evidence in evidence_refs:
                if not isinstance(evidence, Mapping):
                    issues.append(_issue("INVALID_EVIDENCE_REFERENCE", "ERROR", owner_type=owner_type, owner_id=owner.get(f"{owner_type}_id")))
                    continue
                raw_refs = evidence.get("raw_refs")
                if evidence.get("run_id") not in known_runs or not evidence.get("artifact_path") or not isinstance(raw_refs, list) or not raw_refs or not all(isinstance(raw_ref, str) and raw_ref for raw_ref in raw_refs):
                    issues.append(_issue("INVALID_EVIDENCE_REFERENCE", "ERROR", owner_type=owner_type, owner_id=owner.get(f"{owner_type}_id")))
    return issues


def _artifact_items(artifact: Mapping[str, Any]) -> List[Dict[str, Any]]:
    data = artifact.get("data") if isinstance(artifact.get("data"), Mapping) else {}
    return [dict(item) for item in data.get("items", []) if isinstance(item, Mapping)]


def _identity(item: Mapping[str, Any]) -> Mapping[str, Any]:
    return item.get("wire_identity") if isinstance(item.get("wire_identity"), Mapping) else {}


def _biz_id(biz) -> str:
    return f"business_system:{biz}"


def _app_id(biz, app) -> str:
    return f"application:{biz}:{app}"


def _action_id(biz, app, action) -> str:
    return f"action:{biz}:{app}:{action}"


def _trace_id(trace) -> str:
    return f"trace:{trace}"


def _observation_bounds(contexts: Sequence[Mapping[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    starts, ends = [], []
    for context in contexts:
        start, end = _time_bounds(context)
        if start:
            starts.append(start)
        if end:
            ends.append(end)
    return (min(starts) if starts else None, max(ends) if ends else None)


def _time_bounds(context: Mapping[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    resolved = context.get("resolved") if isinstance(context.get("resolved"), Mapping) else {}
    start, end = resolved.get("start_time"), resolved.get("end_time")
    requested = context.get("requested") if isinstance(context.get("requested"), Mapping) else {}
    value = requested.get("value")
    if (not start or not end) and requested.get("kind") == "exact_range" and isinstance(value, str) and ".." in value:
        start, end = value.split("..", 1)
    return _iso(start), _iso(end)


def _iso(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not value:
        return None
    parsed = _datetime(value)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if parsed else None


def _datetime(value: str) -> Optional[datetime]:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _freshness(last: Optional[str], as_of: str, threshold: int) -> str:
    last_dt, as_of_dt = _datetime(last or ""), _datetime(as_of)
    if not last_dt or not as_of_dt or last_dt > as_of_dt:
        return "UNKNOWN"
    return "CURRENT" if (as_of_dt - last_dt).total_seconds() <= threshold else "STALE"


def _prepare_output(output_dir: Path, data_root: Path) -> None:
    runs_root = data_root / "runs"
    inflight_root = data_root / ".inflight"
    if _within(runs_root, output_dir) or _within(inflight_root, output_dir):
        raise SystemModelError("OUTPUT_DIR_INSIDE_IMMUTABLE_RUN_STORE")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemModelError("OUTPUT_DIR_NOT_EMPTY")
    output_dir.mkdir(parents=True, exist_ok=True)


def _read_json_or_error(path: Path, code: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemModelError(code, str(exc)) from exc


def _schema_issues(value: Any, schema_path: Path, code: str) -> List[Dict[str, Any]]:
    schema = _read_json_or_error(schema_path, "SYSTEM_MODEL_SCHEMA_UNAVAILABLE")
    return [_issue(code, "ERROR", violation=violation) for violation in validate_schema(value, schema)]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _within(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _unique(values: Iterable[Any]) -> List[Any]:
    by_hash = {_fingerprint(value): value for value in values}
    return [by_hash[key] for key in sorted(by_hash)]


def _index(rows: Iterable[Mapping[str, Any]], field: str) -> Dict[str, Mapping[str, Any]]:
    return {str(row.get(field)): row for row in rows}


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _issue(code: str, severity: str, **context) -> Dict[str, Any]:
    return {"code": code, "severity": severity, "context": context}


def _sorted_issues(issues: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    unique = {_fingerprint(item): dict(item) for item in issues}
    return sorted(unique.values(), key=lambda item: (item.get("severity"), item.get("code"), json.dumps(item.get("context") or {}, sort_keys=True)))


def _has_errors(issues: Iterable[Mapping[str, Any]]) -> bool:
    return any(item.get("severity") == "ERROR" for item in issues)
