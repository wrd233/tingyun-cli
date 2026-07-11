from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


CORE_OUTPUTS = (
    "source-of-truth.json",
    "evidence-map.json",
    "coverage.json",
    "validation.json",
    "report-readiness.json",
)


def validate_compiled_dir(compiled_dir: Path) -> Dict[str, Any]:
    root = Path(compiled_dir)
    issues: List[Dict[str, Any]] = []
    documents = {}
    for name in CORE_OUTPUTS:
        path = root / name
        if not path.is_file():
            issues.append(_issue("MISSING_COMPILED_ARTIFACT", "ERROR", path=name))
            continue
        try:
            documents[name] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(_issue("INVALID_COMPILED_JSON", "ERROR", path=name, detail=str(exc)))
    validation = documents.get("validation.json", {})
    declared_hashes = validation.get("compiled_hashes") if isinstance(validation.get("compiled_hashes"), dict) else {}
    actual_files = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path.name != "validation.json"
    }
    declared_files = set(declared_hashes)
    if actual_files != declared_files:
        issues.append(_issue("COMPILED_HASH_SET_MISMATCH", "ERROR", missing_hashes=sorted(actual_files - declared_files), missing_files=sorted(declared_files - actual_files)))
    for path, expected in sorted(declared_hashes.items()):
        target = root / path
        if not target.is_file() or _sha256(target) != expected:
            issues.append(_issue("COMPILED_HASH_MISMATCH", "ERROR", path=path))
    if any(item.get("severity") == "ERROR" for item in validation.get("issues", [])):
        issues.append(_issue("COMPILED_VALIDATION_ERROR", "ERROR"))
    source = documents.get("source-of-truth.json", {})
    evidence_map = documents.get("evidence-map.json", {})
    counts = source.get("counts") if isinstance(source.get("counts"), dict) else {}
    incidents = evidence_map.get("incidents") if isinstance(evidence_map.get("incidents"), list) else []
    if counts.get("incident_count") is not None and counts.get("incident_count") != len(incidents):
        issues.append(_issue("SOURCE_OF_TRUTH_COUNT_MISMATCH", "ERROR", field="incident_count"))
    for incident in incidents:
        evidence_count = sum(len(incident.get(field) or []) for field in ("candidate_bindings", "trace_runs", "call_tree_runs", "source_runs"))
        if incident.get("has_evidence") and evidence_count == 0:
            issues.append(_issue("EMPTY_EVIDENCE_MAP", "ERROR", incident_id=incident.get("incident_id")))
    issues.sort(key=lambda item: (item["severity"], item["code"], json.dumps(item.get("context") or {}, sort_keys=True)))
    return {"schema_version": 1, "status": "FAIL" if issues else "PASS", "issues": issues}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _issue(code: str, severity: str, **context) -> Dict[str, Any]:
    return {"code": code, "severity": severity, "context": context}
