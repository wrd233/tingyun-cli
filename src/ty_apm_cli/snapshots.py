from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .catalog import Catalog
from .config import AppConfig
from .envelope import generated_run_id, now_iso
from .http_client import TingyunClient
from .redact import redact

SECTION_NAMES = ["identity", "topology", "behavior_samples", "rules_and_config"]


@dataclass
class SnapshotWriter:
    config: AppConfig
    run_id: str
    profile: str
    catalog_ref: Dict[str, Any]
    target: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.config.artifacts_dir) / "runs" / self.run_id
        self.calls_dir = self.root / "calls"
        self.logs_dir = self.root / "logs"
        self.snapshot_dir = self.root / "snapshot"
        self.sections_dir = self.snapshot_dir / "sections"
        for path in (self.calls_dir, self.logs_dir, self.sections_dir):
            path.mkdir(parents=True, exist_ok=True)
        self.calls: List[Dict[str, Any]] = []
        self._write_json(
            self.root / "run.json",
            {
                "schema_version": "ty-apm.run.v1",
                "run_id": self.run_id,
                "created_at": now_iso(),
                "command": "snapshot.collect",
                "profile": self.profile,
                "catalog_ref": self.catalog_ref,
                "target": self.target,
                "redaction": {"enabled": True},
            },
        )

    def call(self, client: TingyunClient, entry: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        call_id = f"call_{len(self.calls) + 1:04d}"
        record = client.call(entry, params, command="snapshot.collect")
        req_path = self.calls_dir / f"{call_id}.request.json"
        res_path = self.calls_dir / f"{call_id}.response.json"
        self._write_json(req_path, record.request)
        self._write_json(res_path, record.response)
        log_row = {
            "schema_version": "ty-apm.call_log.v1",
            "ts": now_iso(),
            "run_id": self.run_id,
            "call_id": call_id,
            "catalog_id": entry.get("id"),
            "method": entry.get("method"),
            "path": entry.get("path"),
            "safety": entry.get("safety"),
            "attempt": 1,
            "page": None,
            "duration_ms": record.duration_ms,
            "http_status": record.http_status,
            "upstream_code": record.upstream_code,
            "ok": record.envelope.get("ok"),
            "items_count": _items_count(record.response),
            "request_artifact": f"calls/{req_path.name}",
            "response_artifact": f"calls/{res_path.name}",
        }
        with (self.logs_dir / "calls.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(redact(log_row), ensure_ascii=False, sort_keys=True) + "\n")
        source = {"catalog_id": entry.get("id"), "call_id": call_id, "artifact": f"calls/{res_path.name}"}
        self.calls.append({**log_row, "source": source, "envelope": record.envelope})
        return source

    def section(self, name: str, payload: Dict[str, Any]) -> None:
        body = {
            "schema_version": "ty-apm.snapshot_section.v1",
            "section": name,
            **payload,
        }
        self._write_json(self.sections_dir / f"{name}.json", body)

    def finalize(
        self,
        *,
        requested_sections: List[str],
        time_range: Optional[Dict[str, Any]] = None,
        limits: Optional[Dict[str, Any]] = None,
        gaps: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        gaps = gaps or []
        sections = []
        for name in requested_sections:
            path = self.sections_dir / f"{name}.json"
            completed = path.exists()
            section_gaps = [gap for gap in gaps if gap.get("section") == name]
            sections.append(
                {
                    "name": name,
                    "requested": True,
                    "completed": completed,
                    "complete": completed and not section_gaps,
                    "sources": _section_sources(path) if completed else [],
                    "gaps": section_gaps,
                }
            )
        coverage = {
            "schema_version": "ty-apm.coverage.v1",
            "profile": self.profile,
            "sections": sections,
            "blocked_by_safety": [gap for gap in gaps if gap.get("type") == "safety_blocked"],
            "not_implemented": [gap for gap in gaps if gap.get("type") == "not_implemented"],
            "failures": [gap for gap in gaps if gap.get("type") not in {"safety_blocked", "not_implemented"}],
        }
        summary = {
            "schema_version": "ty-apm.snapshot_summary.v1",
            "profile": self.profile,
            "target": self.target,
            "counts": {"calls_total": len(self.calls), "calls_ok": sum(1 for c in self.calls if c.get("ok"))},
            "execution": {
                "sections_requested": len(requested_sections),
                "sections_completed": sum(1 for s in sections if s["completed"]),
                "sections_failed": sum(1 for s in sections if s["requested"] and not s["complete"]),
                "calls_total": len(self.calls),
                "calls_ok": sum(1 for c in self.calls if c.get("ok")),
                "calls_failed": sum(1 for c in self.calls if not c.get("ok")),
            },
        }
        manifest = {
            "schema_version": "ty-apm.snapshot_manifest.v1",
            "run_id": self.run_id,
            "profile": self.profile,
            "created_at": now_iso(),
            "target": self.target,
            "time_range": time_range or {},
            "limits": limits or {},
            "files": {
                "summary": "snapshot/summary.json",
                "coverage": "snapshot/coverage.json",
                "sections": {name: f"snapshot/sections/{name}.json" for name in requested_sections},
            },
            "catalog_ref": self.catalog_ref,
        }
        self._write_json(self.snapshot_dir / "manifest.json", manifest)
        self._write_json(self.snapshot_dir / "summary.json", summary)
        self._write_json(self.snapshot_dir / "coverage.json", coverage)
        return {"run_id": self.run_id, "root": str(self.root), "manifest": "snapshot/manifest.json", "coverage": coverage}

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(redact(payload), fh, ensure_ascii=False, indent=2, sort_keys=True)


def collect_snapshot(
    *,
    profile: str,
    catalog: Catalog,
    config: AppConfig,
    run_id: Optional[str] = None,
    application_id: Optional[str] = None,
    since: str = "60m",
    from_time: Optional[str] = None,
    to_time: Optional[str] = None,
    sample_limit: int = 20,
    page_limit: int = 3,
) -> Dict[str, Any]:
    if profile not in {"catalog-smoke", "inventory", "health-rules", "application-context"}:
        raise ValueError(f"unsupported snapshot profile: {profile}")
    if profile == "application-context" and not application_id:
        raise ValueError("--application-id is required for application-context")
    run_id = run_id or generated_run_id(profile.replace("-", "_"))
    target = {"application_id": application_id} if application_id else {}
    writer = SnapshotWriter(config, run_id, profile, catalog.ref(), target)
    client = TingyunClient(config, catalog_ref=catalog.ref())
    gaps: List[Dict[str, Any]] = []
    time_range = {"since": since, "from": from_time, "to": to_time, "source": "explicit" if from_time or to_time else "default"}
    limits = {"sample_limit_per_section": sample_limit, "page_limit_per_section": page_limit, "timeout_seconds": config.timeout_seconds}

    if profile == "catalog-smoke":
        entries = _read_entries(catalog, limit=3)
        sources = _safe_calls(writer, client, entries, _base_params(since, application_id), gaps, "identity")
        writer.section("identity", {"item_count": len(sources), "complete": not gaps, "sources": sources})
        return writer.finalize(requested_sections=["identity"], time_range=time_range, limits=limits, gaps=gaps)

    if profile == "inventory":
        entries = _domain_entries(catalog, {"business_system", "application", "component"}, limit=8)
        sources = _safe_calls(writer, client, entries, _base_params(since, application_id), gaps, "identity")
        writer.section("identity", {"item_count": len(sources), "complete": not gaps, "sources": sources})
        return writer.finalize(requested_sections=["identity"], time_range=time_range, limits=limits, gaps=gaps)

    if profile == "health-rules":
        entries = _domain_entries(catalog, {"health_rule"}, limit=8)
        sources = _safe_calls(writer, client, entries, _base_params(since, application_id), gaps, "rules_and_config")
        writer.section("rules_and_config", {"item_count": len(sources), "complete": not gaps, "sources": sources})
        return writer.finalize(requested_sections=["rules_and_config"], time_range=time_range, limits=limits, gaps=gaps)

    section_domains = {
        "identity": {"application", "business_system"},
        "topology": {"application", "transaction", "service_interface", "background_task", "component"},
        "behavior_samples": {"error", "trace", "transaction", "service_interface"},
        "rules_and_config": {"health_rule", "config"},
    }
    for section, domains in section_domains.items():
        entries = _domain_entries(catalog, domains, limit=5)
        sources = _safe_calls(writer, client, entries, _base_params(since, application_id), gaps, section)
        writer.section(section, {"item_count": len(sources), "complete": True, "sources": sources, "facts": []})
    return writer.finalize(requested_sections=SECTION_NAMES, time_range=time_range, limits=limits, gaps=gaps)


def _read_entries(catalog: Catalog, *, limit: int) -> List[Dict[str, Any]]:
    return [e for e in catalog.entries if e.get("safety") == "read" and e.get("execution_supported")][:limit]


def _domain_entries(catalog: Catalog, domains: set[str], *, limit: int) -> List[Dict[str, Any]]:
    return [
        e
        for e in catalog.entries
        if e.get("domain") in domains and e.get("safety") == "read" and e.get("execution_supported")
    ][:limit]


def _base_params(since: str, application_id: Optional[str]) -> Dict[str, Any]:
    params: Dict[str, Any] = {"timePeriod": _since_minutes(since)}
    if application_id:
        params["applicationId"] = _coerce_number(application_id)
    return params


def _safe_calls(
    writer: SnapshotWriter,
    client: TingyunClient,
    entries: List[Dict[str, Any]],
    base_params: Dict[str, Any],
    gaps: List[Dict[str, Any]],
    section: str,
) -> List[Dict[str, Any]]:
    sources = []
    for entry in entries:
        params = dict(base_params)
        for p in entry.get("request", {}).get("params", []):
            if p.get("required") and p.get("name") not in params:
                params[p["name"]] = _default_param(p["name"])
        source = writer.call(client, entry, params)
        sources.append(source)
        call = writer.calls[-1]
        if not call.get("ok"):
            gaps.append(
                {
                    "section": section,
                    "type": "call_failed",
                    "catalog_id": entry.get("id"),
                    "message": call.get("envelope", {}).get("error", {}).get("message", "call failed"),
                }
            )
    return sources


def _default_param(name: str) -> Any:
    lower = name.lower()
    if "timeperiod" == lower:
        return 60
    if lower.endswith("id") or lower in {"page", "pageindex", "pagenum", "pagesize"}:
        return 1 if lower != "pagesize" else 20
    if "lang" in lower:
        return "zh_CN"
    if "time" in lower:
        return now_iso()
    return ""


def _since_minutes(since: str) -> int:
    if since.endswith("m"):
        return int(since[:-1])
    if since.endswith("h"):
        return int(since[:-1]) * 60
    return int(since)


def _coerce_number(value: str) -> Any:
    try:
        return int(value)
    except ValueError:
        return value


def _items_count(payload: Any) -> Optional[int]:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("data", "content", "list", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
            if isinstance(value, dict):
                nested = _items_count(value)
                if nested is not None:
                    return nested
    return None


def _section_sources(path: Path) -> List[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return list(payload.get("sources", []))
    except Exception:
        return []
