from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .catalog import Catalog, CatalogNotFound
from .config import AppConfig
from .envelope import generated_run_id, now_iso
from .http_client import TingyunClient
from .redact import redact

SECTION_NAMES = ["identity", "topology", "behavior_samples", "rules_and_config"]
MANIFEST_SCHEMA = "ty-apm.snapshot.manifest.v1"
SUMMARY_SCHEMA = "ty-apm.snapshot.summary.v1"
COVERAGE_SCHEMA = "ty-apm.snapshot.coverage.v1"
SECTION_SCHEMA = "ty-apm.snapshot.section.v1"


@dataclass(frozen=True)
class SectionStep:
    section: str
    catalog_id: str
    params: Dict[str, str] = field(default_factory=dict)


CATALOG_SMOKE_PROFILE = [
    SectionStep("identity", "application.3_1_1.application_app_list"),
    SectionStep("identity", "application.3_2_2.application_business_systemconflist"),
    SectionStep("identity", "config.12_1.data_business_querybizsystemselect"),
]

INVENTORY_PROFILE = [
    SectionStep("identity", "business_system.2_1.application_business_list", {"endTime": "end_time", "timePeriod": "time_period"}),
    SectionStep("identity", "application.3_1_1.application_app_list"),
    SectionStep("identity", "application.3_2_2.application_business_systemconflist"),
    SectionStep("identity", "config.12_1.data_business_querybizsystemselect"),
]

HEALTH_RULES_PROFILE = [
    SectionStep("rules_and_config", "health_rule.14_1.data_health_rule_pagelist", {"pageNum": "page_number", "pageSize": "page_size"}),
    SectionStep("rules_and_config", "health_rule.14_2.data_health_rule_ruleid"),
]

APPLICATION_CONTEXT_PROFILE = [
    SectionStep("identity", "application.3_2_4_3.application_get_id", {"id": "application_id"}),
    SectionStep("identity", "application.3_2_4_4.api_event_getwarnandcriticalcounts", {"applicationId": "application_id", "timePeriod": "time_period"}),
    SectionStep("topology", "application.4_2_3.graph_query_overview_application_overview_instance_list", {"applicationIds": "application_ids"}),
    SectionStep("topology", "application.4_2_4.graph_query_overview_app_upper_list", {"applicationIds": "application_ids"}),
    SectionStep("topology", "application.4_2_5.graph_query_overview_app_under_app_list", {"applicationIds": "application_ids", "endTime": "end_time"}),
    SectionStep("topology", "application.4_2_6.graph_query_overview_app_component_list", {"applicationIds": "application_ids", "endTime": "end_time"}),
    SectionStep("behavior_samples", "application.3_2_4_5.application_charts_response", {"applicationId": "application_id", "timePeriod": "time_period", "endTime": "end_time"}),
    SectionStep("behavior_samples", "application.3_2_4_6.application_charts_throught", {"applicationId": "application_id", "timePeriod": "time_period", "endTime": "end_time"}),
    SectionStep("behavior_samples", "application.3_2_4_7.application_charts_error", {"applicationId": "application_id", "timePeriod": "time_period", "endTime": "end_time"}),
    SectionStep("behavior_samples", "application.4_3_11.graph_query_overview_top_error", {"applicationIds": "application_ids", "endTime": "end_time", "pageSize": "page_size"}),
    SectionStep("rules_and_config", "application.3_2_16_2.instance_environment_instrument", {"applicationId": "application_id"}),
    SectionStep("rules_and_config", "config.12_4_1.data_instance_list", {"applicationId": "application_id"}),
    SectionStep("rules_and_config", "health_rule.14_1.data_health_rule_pagelist", {"pageNum": "page_number", "pageSize": "page_size"}),
]

PROFILE_STEPS = {
    "catalog-smoke": CATALOG_SMOKE_PROFILE,
    "inventory": INVENTORY_PROFILE,
    "health-rules": HEALTH_RULES_PROFILE,
    "application-context": APPLICATION_CONTEXT_PROFILE,
}


@dataclass
class SnapshotWriter:
    config: AppConfig
    run_id: str
    profile: str
    catalog_ref: Dict[str, Any]
    scope: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.config.artifacts_dir) / "runs" / self.run_id
        self.calls_dir = self.root / "calls"
        self.logs_dir = self.root / "logs"
        self.snapshot_dir = self.root / "snapshot"
        self.sections_dir = self.snapshot_dir / "sections"
        for path in (self.calls_dir, self.logs_dir, self.sections_dir):
            path.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "calls.jsonl").touch()
        self.calls: List[Dict[str, Any]] = []
        self._write_json(
            self.root / "run.json",
            {
                "schema_version": "ty-apm.run.v1",
                "run_id": self.run_id,
                "created_at": now_iso(),
                "command": "snapshot.collect",
                "profile": self.profile,
                "scope": self.scope,
                "catalog_ref": self.catalog_ref,
                "target": self.scope,
                "redaction": {"enabled": True},
            },
        )

    def call(self, client: TingyunClient, step: Dict[str, Any], entry: Dict[str, Any]) -> Dict[str, Any]:
        call_id = f"call_{len(self.calls) + 1:04d}"
        params = {name: spec["value"] for name, spec in step["params"].items() if spec["source"] != "missing"}
        record = client.call(entry, params, command="snapshot.collect")
        req_path = self.calls_dir / f"{call_id}.request.json"
        res_path = self.calls_dir / f"{call_id}.response.json"
        self._write_json(req_path, record.request)
        self._write_json(res_path, record.response)
        ts = now_iso()
        log_row = {
            "schema_version": "ty-apm.call_log.v1",
            "ts": ts,
            "run_id": self.run_id,
            "catalog_ref": self.catalog_ref,
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
        source = {
            "catalog_id": entry.get("id"),
            "call_id": call_id,
            "artifact_path": f"calls/{res_path.name}",
            "artifact": f"calls/{res_path.name}",
            "item_count": log_row["items_count"],
            "collected_at": ts,
        }
        self.calls.append({**log_row, "source": source, "envelope": record.envelope, "section": step["section"]})
        return source

    def section(self, name: str, payload: Dict[str, Any]) -> None:
        body = {
            "schema_version": SECTION_SCHEMA,
            "section": name,
            **payload,
        }
        self._write_json(self.sections_dir / f"{name}.json", body)

    def finalize(
        self,
        *,
        requested_sections: List[str],
        time_range: Dict[str, Any],
        limits: Dict[str, Any],
        gaps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        sections = []
        for name in requested_sections:
            path = self.sections_dir / f"{name}.json"
            completed = path.exists()
            section_gaps = [gap for gap in gaps if gap.get("section") == name]
            status = _section_status(completed, section_gaps)
            sections.append(
                {
                    "name": name,
                    "requested": True,
                    "completed": completed,
                    "complete": completed and not section_gaps,
                    "status": status,
                    "sources": _section_sources(path) if completed else [],
                    "gaps": section_gaps,
                }
            )
        skipped_types = {"missing_required_param", "not_implemented", "skipped"}
        coverage = {
            "schema_version": COVERAGE_SCHEMA,
            "profile": self.profile,
            "run_id": self.run_id,
            "catalog_ref": self.catalog_ref,
            "sections": sections,
            "blocked_by_safety": [gap for gap in gaps if gap.get("type") == "safety_blocked"],
            "skipped": [gap for gap in gaps if gap.get("type") in skipped_types],
            "not_implemented": [gap for gap in gaps if gap.get("type") == "not_implemented"],
            "failures": [gap for gap in gaps if gap.get("type") not in skipped_types | {"safety_blocked"}],
        }
        summary = {
            "schema_version": SUMMARY_SCHEMA,
            "run_id": self.run_id,
            "profile": self.profile,
            "catalog_ref": self.catalog_ref,
            "scope": self.scope,
            "target": self.scope,
            "counts": {"calls_total": len(self.calls), "calls_ok": sum(1 for c in self.calls if c.get("ok"))},
            "execution": {
                "sections_requested": len(requested_sections),
                "sections_completed": sum(1 for s in sections if s["completed"]),
                "sections_failed": sum(1 for s in sections if s["status"] == "failed"),
                "sections_skipped": sum(1 for s in sections if s["status"] == "skipped"),
                "calls_total": len(self.calls),
                "calls_ok": sum(1 for c in self.calls if c.get("ok")),
                "calls_failed": sum(1 for c in self.calls if not c.get("ok")),
            },
        }
        manifest = {
            "schema_version": MANIFEST_SCHEMA,
            "run_id": self.run_id,
            "profile": self.profile,
            "created_at": now_iso(),
            "scope": self.scope,
            "target": self.scope,
            "time_range": time_range,
            "limits": limits,
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


def plan_snapshot(
    *,
    profile: str,
    catalog: Catalog,
    application_id: Optional[str] = None,
    since: str = "60m",
    from_time: Optional[str] = None,
    to_time: Optional[str] = None,
    sample_limit: int = 20,
    page_limit: int = 3,
) -> Dict[str, Any]:
    if profile not in PROFILE_STEPS:
        raise ValueError(f"unsupported snapshot profile: {profile}")
    if profile == "application-context" and not application_id:
        raise ValueError("--application-id is required for application-context")
    context = _planning_context(application_id, since, from_time, to_time, sample_limit, page_limit)
    steps = [_plan_step(catalog, step, context) for step in PROFILE_STEPS[profile]]
    return {
        "profile": profile,
        "mode": "plan_only",
        "scope": context["scope"],
        "time_range": context["time_range"],
        "limits": context["limits"],
        "sections": sorted({step.section for step in PROFILE_STEPS[profile]}, key=_section_sort_key),
        "steps": steps,
        "catalog_ref": catalog.ref(),
    }


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
    plan = plan_snapshot(
        profile=profile,
        catalog=catalog,
        application_id=application_id,
        since=since,
        from_time=from_time,
        to_time=to_time,
        sample_limit=sample_limit,
        page_limit=page_limit,
    )
    run_id = run_id or generated_run_id(profile.replace("-", "_"))
    writer = SnapshotWriter(config, run_id, profile, catalog.ref(), plan["scope"])
    client = TingyunClient(config, catalog_ref=catalog.ref())
    gaps: List[Dict[str, Any]] = []
    section_sources: Dict[str, List[Dict[str, Any]]] = {section: [] for section in plan["sections"]}

    for step in plan["steps"]:
        if not step["will_execute"]:
            gaps.append(_gap_from_step(step))
            continue
        entry = catalog.get(step["catalog_id"])
        source = writer.call(client, step, entry)
        section_sources.setdefault(step["section"], []).append(source)
        call = writer.calls[-1]
        if not call.get("ok"):
            gaps.append(
                {
                    "section": step["section"],
                    "type": _gap_type(call.get("envelope", {})),
                    "catalog_id": step["catalog_id"],
                    "message": call.get("envelope", {}).get("error", {}).get("message", "call failed"),
                }
            )

    for section in plan["sections"]:
        section_gaps = [gap for gap in gaps if gap.get("section") == section]
        sources = section_sources.get(section, [])
        writer.section(
            section,
            {
                "complete": bool(sources) and not section_gaps,
                "item_count": sum(source.get("item_count") or 0 for source in sources),
                "sources": sources,
                "data": {},
            },
        )
    return writer.finalize(
        requested_sections=plan["sections"],
        time_range=plan["time_range"],
        limits=plan["limits"],
        gaps=gaps,
    )


def _planning_context(
    application_id: Optional[str],
    since: str,
    from_time: Optional[str],
    to_time: Optional[str],
    sample_limit: int,
    page_limit: int,
) -> Dict[str, Any]:
    since_minutes = _since_minutes(since)
    end_time = to_time or now_iso()
    scope: Dict[str, Any] = {}
    if application_id:
        scope["application_id"] = _coerce_number(application_id)
    return {
        "scope": scope,
        "time_range": {
            "since": since,
            "since_minutes": since_minutes,
            "from": from_time,
            "to": to_time,
            "end_time": end_time,
            "source": "explicit" if from_time or to_time else "default",
        },
        "limits": {
            "sample_limit": sample_limit,
            "page_limit": page_limit,
            "sample_limit_per_section": sample_limit,
            "page_limit_per_section": page_limit,
        },
    }


def _plan_step(catalog: Catalog, step: SectionStep, context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        entry = catalog.get(step.catalog_id)
    except CatalogNotFound:
        return {
            "section": step.section,
            "catalog_id": step.catalog_id,
            "safety": None,
            "execution_supported": False,
            "params": {},
            "will_execute": False,
            "skip_reason": "catalog_not_found",
        }
    planned_params: Dict[str, Dict[str, Any]] = {}
    for name, source in step.params.items():
        planned_params[name] = _derive_param(source, context)
    for name in _required_param_names(entry):
        if name not in planned_params:
            planned_params[name] = _derive_param(_safe_source_for_name(name), context)
    missing = [name for name, spec in planned_params.items() if spec["source"] == "missing"]
    blocked = entry.get("safety") != "read" or not entry.get("execution_supported")
    will_execute = not missing and not blocked
    planned = {
        "section": step.section,
        "catalog_id": step.catalog_id,
        "title": entry.get("title"),
        "method": entry.get("method"),
        "path": entry.get("path"),
        "safety": entry.get("safety"),
        "execution_supported": entry.get("execution_supported"),
        "params": planned_params,
        "will_execute": will_execute,
    }
    if missing:
        planned["skip_reason"] = "missing_required_param"
        planned["missing_params"] = missing
    if blocked:
        planned["skip_reason"] = "safety_blocked"
    return planned


def _required_param_names(entry: Dict[str, Any]) -> List[str]:
    names = [
        p.get("name")
        for p in entry.get("request", {}).get("params", [])
        if p.get("required") is True and p.get("name")
    ]
    for name in re.findall(r"{([^{}]+)}", str(entry.get("path", ""))):
        if name not in names:
            names.append(name)
    return [str(name) for name in names]


def _safe_source_for_name(name: str) -> str:
    lower = name.lower()
    if lower in {"applicationid", "appid", "id", "appicationid"}:
        return "application_id"
    if lower in {"timeperiod"}:
        return "time_period"
    if lower in {"endtime"}:
        return "end_time"
    if lower in {"pagenum", "pagenumber", "page", "pageindex"}:
        return "page_number"
    if lower == "pagesize":
        return "page_size"
    if "lang" in lower:
        return "lang"
    return "missing"


def _derive_param(source: str, context: Dict[str, Any]) -> Dict[str, Any]:
    scope = context["scope"]
    time_range = context["time_range"]
    limits = context["limits"]
    if source == "application_id" and "application_id" in scope:
        return {"value": scope["application_id"], "source": "explicit"}
    if source == "application_ids" and "application_id" in scope:
        return {"value": [scope["application_id"]], "source": "derived"}
    if source == "time_period":
        return {"value": time_range["since_minutes"], "source": "default"}
    if source == "end_time":
        return {"value": time_range["end_time"], "source": "default"}
    if source == "page_number":
        return {"value": 1, "source": "default"}
    if source == "page_size":
        return {"value": limits["sample_limit"], "source": "default"}
    if source == "lang":
        return {"value": "zh_CN", "source": "default"}
    return {"value": None, "source": "missing"}


def _gap_from_step(step: Dict[str, Any]) -> Dict[str, Any]:
    reason = step.get("skip_reason") or "skipped"
    return {
        "section": step["section"],
        "type": reason,
        "catalog_id": step["catalog_id"],
        "message": _gap_message(reason, step),
        "missing_params": step.get("missing_params", []),
    }


def _gap_message(reason: str, step: Dict[str, Any]) -> str:
    if reason == "missing_required_param":
        return "required parameters could not be safely derived"
    if reason == "safety_blocked":
        return "planned catalog entry is not executable read"
    if reason == "catalog_not_found":
        return "planned catalog entry was not found"
    return "step skipped"


def _section_status(completed: bool, gaps: List[Dict[str, Any]]) -> str:
    if any(gap.get("type") == "safety_blocked" for gap in gaps):
        return "blocked"
    failure_types = {"upstream_error", "http_error", "failed"}
    if any(gap.get("type") in failure_types for gap in gaps):
        return "failed"
    if not completed or gaps:
        return "skipped"
    return "completed"


def _section_sort_key(section: str) -> int:
    return SECTION_NAMES.index(section) if section in SECTION_NAMES else len(SECTION_NAMES)


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


def _gap_type(envelope: Dict[str, Any]) -> str:
    error_type = envelope.get("error", {}).get("type")
    message = str(envelope.get("error", {}).get("message", ""))
    if error_type == "ValidationError" and "missing required parameter" in message:
        return "missing_required_param"
    return {
        "SafetyBlocked": "safety_blocked",
        "ValidationError": "failed",
        "UpstreamError": "upstream_error",
        "HttpError": "http_error",
        "TimeoutError": "http_error",
        "AuthError": "http_error",
    }.get(str(error_type), "failed")
