from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .candidates import normalize_candidates
from .config import Config
from .http import HttpExecutor
from .storage import RunStore
from .time_context import resolve_time_context


def plan_collect(store: RunStore, source_run_id: str, source_item_ref: str, time_context_value: str) -> Dict[str, Any]:
    source = _resolve_source(store, source_run_id, source_item_ref)
    time_context = resolve_time_context(time_context_value)
    if source["kind"] != "business_system_candidate":
        return {"schema_version": 1, "command": "collect", "status": "BLOCKED", "reason_code": "INVALID_SOURCE_KIND"}
    return {
        "schema_version": 1,
        "command": "collect",
        "status": "READY",
        "source": {"run_id": source_run_id, "item_ref": source_item_ref, "kind": source["kind"]},
        "time_context": time_context,
        "planned_steps": ["identity", "topology", "performance", "candidates"],
        "expected_live_request_count": 3,
    }


def run_collect(
    *,
    store: RunStore,
    config: Config,
    source_run_id: str,
    source_item_ref: str,
    time_context_value: str,
    transport=None,
    clock=None,
) -> Dict[str, Any]:
    if not store.acquire_live_lock():
        return _blocked_run(store, "collect", "COLLECT", "LIVE_EXECUTION_BUSY")
    try:
        try:
            source = _resolve_source(store, source_run_id, source_item_ref)
        except (FileNotFoundError, KeyError):
            return _blocked_run(store, "collect", "COLLECT", "INVALID_SOURCE_REF")
        if source["kind"] != "business_system_candidate":
            return _blocked_run(store, "collect", "COLLECT", "INVALID_SOURCE_KIND")
        try:
            time_context = resolve_time_context(time_context_value, clock or __import__("time"))
        except ValueError:
            return _blocked_run(store, "collect", "COLLECT", "UNSUPPORTED_TIME_SHAPE")
        biz_system_id = source.get("wire_identity", {}).get("bizSystemId")
        if not biz_system_id:
            return _blocked_run(store, "collect", "COLLECT", "MISSING_WIRE_IDENTITY")

        run = store.begin_run(command="collect", run_type="COLLECT")
        preflight = {
            "schema_version": 1,
            "command": "collect",
            "source": {"run_id": source_run_id, "item_ref": source_item_ref},
            "resolved_item_kind": source["kind"],
            "target": {"display_name": source.get("display_name"), "wire_identity": source.get("wire_identity")},
            "time_context": time_context,
            "recipe": "core_collect",
            "safety": {"result": "ALLOW_READ_ONLY"},
            "expected_live_request_count": 3,
        }
        store.write_json(run.path / "preflight.json", preflight)
        executor = HttpExecutor(store=store, run=run, config=config, transport=transport, clock=clock or __import__("time"))
        scope = {"bizSystemId": biz_system_id}
        topology_response = executor.execute(_topology_request(biz_system_id, time_context))
        performance_response = executor.execute(_performance_request(biz_system_id, time_context))
        candidates_response = executor.execute(_candidate_request(biz_system_id, time_context))

        artifacts = _collect_artifacts(source, source_run_id, scope, time_context, topology_response, performance_response, candidates_response)
        for filename, artifact in artifacts.items():
            store.write_json(run.path / "evidence" / filename, artifact)
        coverage = _coverage_from_artifacts(artifacts)
        manifest = _manifest(
            run_id=run.run_id,
            run_type="COLLECT",
            command="collect",
            source={"run_id": source_run_id, "item_ref": source_item_ref},
            time_context=time_context,
            artifacts=artifacts,
            coverage=coverage,
            live_request_count=executor.sequence,
        )
        path = store.finalize_run(run, manifest=manifest, coverage=coverage)
        return _receipt("collect", manifest["overall"], run.run_id, path / "manifest.json")
    finally:
        store.release_live_lock()


def run_discover(
    *,
    store: RunStore,
    config: Config,
    query: str,
    transport=None,
    clock=None,
) -> Dict[str, Any]:
    if not store.acquire_live_lock():
        return _blocked_run(store, "discover", "DISCOVERY", "LIVE_EXECUTION_BUSY")
    try:
        time_context = resolve_time_context("last_60m", clock or __import__("time"))
        run = store.begin_run(command="discover", run_type="DISCOVERY")
        store.write_json(run.path / "preflight.json", {
            "schema_version": 1,
            "command": "discover",
            "query": query,
            "time_context": time_context,
            "safety": {"result": "ALLOW_READ_ONLY"},
            "expected_live_request_count": 1,
        })
        executor = HttpExecutor(store=store, run=run, config=config, transport=transport, clock=clock or __import__("time"))
        response = executor.execute(_business_tree_request(time_context))
        artifact = _targets_artifact(response, query, time_context)
        artifacts = {"targets.json": artifact}
        store.write_json(run.path / "evidence" / "targets.json", artifact)
        coverage = _coverage_from_artifacts(artifacts)
        manifest = _manifest(
            run_id=run.run_id,
            run_type="DISCOVERY",
            command="discover",
            source=None,
            time_context=time_context,
            artifacts=artifacts,
            coverage=coverage,
            live_request_count=executor.sequence,
        )
        path = store.finalize_run(run, manifest=manifest, coverage=coverage)
        return _receipt("discover", manifest["overall"], run.run_id, path / "manifest.json")
    finally:
        store.release_live_lock()


def run_investigate(
    *,
    store: RunStore,
    config: Config,
    source_run_id: str,
    source_item_ref: str,
    action: str,
    transport=None,
    clock=None,
) -> Dict[str, Any]:
    if not store.acquire_live_lock():
        return _blocked_run(store, "investigate", "INVESTIGATION", "LIVE_EXECUTION_BUSY")
    try:
        try:
            source = _resolve_source(store, source_run_id, source_item_ref)
        except (FileNotFoundError, KeyError):
            return _blocked_run(store, "investigate", "INVESTIGATION", "INVALID_SOURCE_REF")
        if action not in source.get("available_actions", []):
            return _blocked_run(store, "investigate", "INVESTIGATION", "INVALID_ACTION")
        if action not in {"investigate_trace", "inspect_call_tree"}:
            return _blocked_run(store, "investigate", "INVESTIGATION", "ACTION_NOT_STABLE")

        source_manifest = _read_manifest(store, source_run_id)
        time_context = source_manifest.get("time_context") or resolve_time_context("last_30m", clock or __import__("time"))
        run = store.begin_run(command="investigate", run_type="INVESTIGATION")
        store.write_json(run.path / "preflight.json", {
            "schema_version": 1,
            "command": "investigate",
            "source": {"run_id": source_run_id, "item_ref": source_item_ref},
            "action": action,
            "time_context": time_context,
            "safety": {"result": "ALLOW_READ_ONLY"},
            "expected_live_request_count": 1,
        })
        executor = HttpExecutor(store=store, run=run, config=config, transport=transport, clock=clock or __import__("time"))
        if action == "investigate_trace":
            response = executor.execute(_trace_detail_request(source, time_context))
            artifact_name = "trace.json"
            artifact = _trace_artifact(response, source, source_run_id, time_context)
        else:
            response = executor.execute(_call_tree_request(source, time_context))
            artifact_name = "call_tree.json"
            artifact = _call_tree_artifact(response, source, source_run_id, time_context)
        artifacts = {artifact_name: artifact}
        store.write_json(run.path / "evidence" / artifact_name, artifact)
        coverage = _coverage_from_artifacts(artifacts)
        manifest = _manifest(
            run_id=run.run_id,
            run_type="INVESTIGATION",
            command="investigate",
            source={"run_id": source_run_id, "item_ref": source_item_ref},
            time_context=time_context,
            artifacts=artifacts,
            coverage=coverage,
            live_request_count=executor.sequence,
            action=action,
        )
        path = store.finalize_run(run, manifest=manifest, coverage=coverage)
        return _receipt("investigate", manifest["overall"], run.run_id, path / "manifest.json")
    finally:
        store.release_live_lock()


def export_sanitized_run(store: RunStore, run_id: str, output_dir: Path) -> Dict[str, Any]:
    source = store.run_path(run_id)
    if not source.exists():
        raise FileNotFoundError(run_id)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    for path in source.rglob("*.json"):
        rel = path.relative_to(source)
        data = json.loads(path.read_text(encoding="utf-8"))
        sanitized = _sanitize(data, root=store.root)
        target = output_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"schema_version": 1, "command": "sanitized_export", "status": "SUCCESS", "output_path": str(output_dir)}


class Blocked(Exception):
    pass


def _blocked_run(store: RunStore, command: str, run_type: str, reason_code: str) -> Dict[str, Any]:
    run = store.begin_run(command=command, run_type=run_type)
    store.write_json(run.path / "preflight.json", {
        "schema_version": 1,
        "command": command,
        "result": "BLOCKED",
        "reason_code": reason_code,
        "live_request_count": 0,
    })
    coverage = {"schema_version": 1, "overall": "BLOCKED", "artifacts": {}, "reason_code": reason_code}
    manifest = {
        "schema_version": 1,
        "run_id": run.run_id,
        "run_type": run_type,
        "overall": "BLOCKED",
        "reason_code": reason_code,
        "artifacts": [],
        "coverage_ref": "coverage.json",
        "live_request_count": 0,
    }
    path = store.finalize_run(run, manifest=manifest, coverage=coverage)
    receipt = _receipt(command, "BLOCKED", run.run_id, path / "manifest.json")
    receipt["reason_code"] = reason_code
    return receipt


def _resolve_source(store: RunStore, run_id: str, item_ref: str) -> Dict[str, Any]:
    run_path = store.run_path(run_id)
    if not run_path.exists():
        raise FileNotFoundError(run_id)
    for artifact_path in (run_path / "evidence").glob("*.json"):
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        for item in _artifact_items(artifact):
            if item.get("item_ref") == item_ref:
                return item
    raise KeyError(item_ref)


def _artifact_items(artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = artifact.get("data", {})
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def _read_manifest(store: RunStore, run_id: str) -> Dict[str, Any]:
    path = store.run_path(run_id) / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _topology_request(biz_system_id: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return {
        "endpoint_id": "ep_post_server_api_graph_querybizdetailgraph",
        "method": "POST",
        "path": "/server-api/graph/queryBizDetailGraph",
        "body_kind": "form",
        "body": {
            "bizSystemId": biz_system_id,
            "timePeriod": str(endpoint["timePeriod"]),
            "endTime": endpoint["endTime"],
            "mergeGraph": "1",
            "cascadingDisplay": "1",
            "lang": "zh_CN",
        },
    }


def _performance_request(biz_system_id: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return {
        "endpoint_id": "ep_post_server_api_application_charts_response",
        "method": "POST",
        "path": "/server-api/application/charts/response",
        "body_kind": "form",
        "body": {
            "bizSystemId": biz_system_id,
            "businessType": "BIZ_SYSTEM",
            "timePeriod": str(endpoint["timePeriod"]),
            "endTime": endpoint["endTime"],
            "lang": "zh_CN",
        },
    }


def _candidate_request(biz_system_id: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return {
        "endpoint_id": "ep_post_server_api_graph_query_overview",
        "variant_id": "variant_metric_request_overview",
        "method": "POST",
        "path": "/server-api/graph/query/overview",
        "query": {"request_overview": "", "lang": "zh_CN"},
        "body_kind": "json",
        "body": {
            "endTime": endpoint["endTime"],
            "timePeriod": endpoint["timePeriod"],
            "metric": "request_overview",
            "autoMetrics": [
                "actionName",
                "requestType",
                "applicationName",
                "responseP50",
                "throughput",
                "totalCount",
                "errorRate",
                "slowCount",
                "option",
            ],
            "zoomTime": False,
            "labels": {"systemIds": [biz_system_id]},
            "lang": "zh_CN",
        },
    }


def _business_tree_request(time_context: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = time_context["endpoint"]
    return {
        "endpoint_id": "ep_get_server_api_data_business_getbusinesstree",
        "method": "GET",
        "path": "/server-api/data/business/getBusinessTree",
        "query": {
            "timePeriod": str(endpoint["timePeriod"]),
            "endTime": endpoint["endTime"],
            "hidden7dNoDataApp": "true",
            "random": "0",
            "lang": "zh_CN",
        },
    }


def _trace_detail_request(source: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    identity = source.get("wire_identity", {})
    endpoint = time_context["endpoint"]
    return {
        "endpoint_id": "ep_post_server_api_action_trace_detail",
        "method": "POST",
        "path": "/server-api/action/trace/detail",
        "body_kind": "form",
        "body": {
            "bizSystemId": identity.get("bizSystemId"),
            "applicationId": identity.get("applicationId"),
            "actionId": identity.get("actionId"),
            "actionType": identity.get("requestType"),
            "timePeriod": str(endpoint["timePeriod"]),
            "endTime": endpoint["endTime"],
            "lang": "zh_CN",
        },
    }


def _call_tree_request(source: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    identity = source.get("wire_identity", {})
    endpoint = time_context["endpoint"]
    return {
        "endpoint_id": "ep_post_server_api_action_trace_calltree",
        "method": "POST",
        "path": "/server-api/action/trace/callTree",
        "body_kind": "form",
        "body": {
            "bizSystemId": identity.get("bizSystemId"),
            "applicationId": identity.get("applicationId"),
            "actionGuid": identity.get("actionGuid"),
            "traceId": identity.get("traceId"),
            "actionId": identity.get("actionId"),
            "actionType": identity.get("actionType"),
            "timePeriod": str(endpoint["timePeriod"]),
            "endTime": endpoint["endTime"],
            "lang": "zh_CN",
        },
    }


def _collect_artifacts(source, source_run_id, scope, time_context, topology_response, performance_response, candidates_response):
    return {
        "identity.json": {
            "schema_version": 1,
            "kind": "identity",
            "status": "SUCCESS",
            "scope": scope,
            "time_context": time_context,
            "derived_from": [],
            "data": {"source_item": source, "wire_identity": source.get("wire_identity", {})},
        },
        "topology.json": _topology_artifact(topology_response, scope, time_context),
        "performance.json": _performance_artifact(performance_response, scope, time_context),
        "candidates.json": normalize_candidates(
            response=candidates_response,
            source_run_id=source_run_id,
            scope=scope,
            time_context=time_context,
            raw_ref="raw/response-0003.json",
        ),
    }


def _targets_artifact(response: Dict[str, Any], query: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    candidates = _business_candidates(response.get("data", []), query=query)
    return {
        "schema_version": 1,
        "kind": "targets",
        "status": "SUCCESS" if candidates else "EMPTY",
        "time_context": time_context,
        "derived_from": ["raw/response-0001.json"],
        "data": {"query": query, "items": candidates},
    }


def _business_candidates(value: Any, *, query: str) -> List[Dict[str, Any]]:
    found: List[Tuple[str, str]] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            name = node.get("bizSystemName") or node.get("name") or node.get("displayName") or node.get("title")
            identity = node.get("bizSystemId") or node.get("id") or node.get("businessId")
            if name and identity and (not query or query.lower() in str(name).lower()):
                found.append((str(identity), str(name)))
            for child_key in ("children", "childList", "items", "data"):
                if child_key in node:
                    visit(node[child_key])
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(value)
    items = []
    for index, (identity, name) in enumerate(found, 1):
        items.append({
            "item_ref": f"item-{index:04d}",
            "kind": "business_system_candidate",
            "display_name": name,
            "wire_identity": {"bizSystemId": identity},
        })
    return items


def _topology_artifact(response: Dict[str, Any], scope: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    nodes = data.get("nodes") or data.get("nodeList") or []
    edges = data.get("edges") or data.get("lines") or []
    return {
        "schema_version": 1,
        "kind": "topology",
        "status": "SUCCESS" if nodes or edges else "EMPTY",
        "scope": scope,
        "time_context": time_context,
        "derived_from": ["raw/response-0001.json"],
        "data": {"structural_nodes": nodes, "runtime_edges": edges},
    }


def _performance_artifact(response: Dict[str, Any], scope: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    metrics = {
        "response_avg": {"semantic": "response_time", "aggregation": "average", "unit": "ms", "series": data.get("avg") or data.get("average") or []},
        "p50": {"semantic": "response_time", "aggregation": "p50", "unit": "ms", "series": data.get("p50") or data.get("P50") or []},
        "p80": {"semantic": "response_time", "aggregation": "p80", "unit": "ms", "series": data.get("p80") or data.get("P80") or []},
        "p95": {"semantic": "response_time", "aggregation": "p95", "unit": "ms", "series": data.get("p95") or data.get("P95") or []},
        "p99": {"semantic": "response_time", "aggregation": "p99", "unit": "ms", "series": data.get("p99") or data.get("P99") or []},
    }
    has_series = any(metric["series"] for metric in metrics.values())
    return {
        "schema_version": 1,
        "kind": "performance",
        "status": "SUCCESS" if has_series else "EMPTY",
        "scope": scope,
        "time_context": time_context,
        "derived_from": ["raw/response-0002.json"],
        "data": {"metrics": metrics},
    }


def _trace_artifact(response: Dict[str, Any], source: Dict[str, Any], source_run_id: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    identity = dict(source.get("wire_identity", {}))
    if data.get("actionGuid"):
        identity["actionGuid"] = data["actionGuid"]
    trace_id = nested.get("id") or data.get("traceId")
    if trace_id:
        identity["traceId"] = trace_id
    item = {
        "item_ref": "item-0001",
        "kind": "trace",
        "source_run_id": source_run_id,
        "wire_identity": identity,
        "source_refs": ["raw/response-0001.json"],
        "summary": {k: data.get(k) for k in ("duration", "actionName", "applicationName") if k in data},
    }
    if identity.get("actionGuid") and identity.get("traceId"):
        item["available_actions"] = ["inspect_call_tree"]
    return {
        "schema_version": 1,
        "kind": "trace",
        "status": "SUCCESS" if data else "EMPTY",
        "time_context": time_context,
        "derived_from": ["raw/response-0001.json"],
        "data": {"items": [item] if data else []},
    }


def _call_tree_artifact(response: Dict[str, Any], source: Dict[str, Any], source_run_id: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    data = response.get("data", {})
    return {
        "schema_version": 1,
        "kind": "call_tree",
        "status": "SUCCESS" if data else "EMPTY",
        "time_context": time_context,
        "derived_from": ["raw/response-0001.json"],
        "data": {"source_item": {"run_id": source_run_id, "item_ref": source.get("item_ref")}, "call_tree": data},
    }


def _coverage_from_artifacts(artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    entries = {}
    for filename, artifact in artifacts.items():
        kind = filename.removesuffix(".json")
        entries[kind] = {
            "status": artifact["status"],
            "steps": [{"capability": _capability_for_kind(kind), "status": artifact["status"], "evidence_refs": artifact.get("derived_from", [])}],
        }
    overall = _overall_from_statuses([artifact["status"] for artifact in artifacts.values()])
    return {"schema_version": 1, "overall": overall, "artifacts": entries}


def _manifest(
    *,
    run_id,
    run_type,
    command,
    source,
    time_context,
    artifacts,
    coverage,
    live_request_count,
    action=None,
):
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "run_type": run_type,
        "command": command,
        "overall": coverage["overall"],
        "source": source,
        "time_context": time_context,
        "artifacts": [
            {"kind": filename.removesuffix(".json"), "path": f"evidence/{filename}", "status": artifact["status"]}
            for filename, artifact in artifacts.items()
        ],
        "coverage_ref": "coverage.json",
        "live_request_count": live_request_count,
    }
    if action:
        manifest["action"] = action
    return manifest


def _overall_from_statuses(statuses: List[str]) -> str:
    if all(status in {"SUCCESS", "EMPTY", "SKIPPED"} for status in statuses):
        return "SUCCESS"
    return "PARTIAL"


def _capability_for_kind(kind: str) -> str:
    return {
        "targets": "list_business_systems",
        "identity": "resolve_source_identity",
        "topology": "read_business_topology",
        "performance": "read_performance_timeseries",
        "candidates": "list_request_overview_candidates",
        "trace": "get_trace_detail",
        "call_tree": "get_trace_call_tree",
    }.get(kind, kind)


def _receipt(command: str, status: str, run_id: str, manifest_path: Path) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "command": command,
        "status": status,
        "run_id": run_id,
        "manifest_path": str(manifest_path),
    }


def _sanitize(value: Any, *, root: Path) -> Any:
    secret_parts = ("authorization", "cookie", "token", "password", "secret")
    identity_keys = {"wire_identity", "actionId", "actionGuid", "traceId", "bizSystemId", "applicationId", "systemId", "available_actions"}
    if isinstance(value, dict):
        result = {}
        for key, nested in value.items():
            if key in identity_keys or any(part in key.lower() for part in secret_parts):
                continue
            result[key] = _sanitize(nested, root=root)
        return result
    if isinstance(value, list):
        return [_sanitize(item, root=root) for item in value]
    if isinstance(value, str):
        text = value.replace(str(root), "<local-path>")
        if any(part in text.lower() for part in secret_parts):
            return "<redacted>"
        return text
    return value
