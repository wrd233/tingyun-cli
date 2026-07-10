from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


def correction_record(*, artifact_id: str, superseded_by: str, reason: str, evidence_refs: Iterable[str], timestamp: str) -> Dict[str, Any]:
    return {"artifact_id": artifact_id, "status": "SUPERSEDED", "superseded_by": superseded_by, "reason": reason, "timestamp": timestamp, "evidence_refs": list(evidence_refs)}


def active_artifacts(artifacts: Iterable[Mapping[str, Any]], corrections: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    inactive = {record["artifact_id"] for record in corrections if record.get("status") in {"SUPERSEDED", "INVALIDATED"}}
    return [dict(artifact) for artifact in artifacts if artifact.get("artifact_id") not in inactive and artifact.get("status") == "ACTIVE"]
