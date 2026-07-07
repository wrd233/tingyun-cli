from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .candidates import is_inspect_call_tree_eligible, is_investigate_trace_eligible, normalize_candidates
from .config import Config
from .http import ExecutionResult, HttpExecutor
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
    requested_intent = {
        "source_run_id": source_run_id,
        "source_item_ref": source_item_ref,
        "time_context": time_context_value,
    }
    if not store.acquire_live_lock():
        return _blocked_run(store, "collect", "COLLECT", "LIVE_EXECUTION_BUSY", requested_intent=requested_intent)
    try:
        try:
            source = _resolve_source(store, source_run_id, source_item_ref)
        except (FileNotFoundError, KeyError):
            return _blocked_run(store, "collect", "COLLECT", "INVALID_SOURCE_REF", requested_intent=requested_intent)
        if source["kind"] != "business_system_candidate":
            return _blocked_run(store, "collect", "COLLECT", "INVALID_SOURCE_KIND", requested_intent=requested_intent)
        try:
            time_context = resolve_time_context(time_context_value, clock or __import__("time"))
        except ValueError:
            return _blocked_run(store, "collect", "COLLECT", "UNSUPPORTED_TIME_SHAPE", requested_intent=requested_intent)
        biz_system_id = source.get("wire_identity", {}).get("bizSystemId")
        if not biz_system_id:
            return _blocked_run(store, "collect", "COLLECT", "MISSING_WIRE_IDENTITY", requested_intent=requested_intent)

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
            "requested_intent": requested_intent,
        }
        store.write_json(run.path / "preflight.json", preflight)
        executor = HttpExecutor(store=store, run=run, config=config, transport=transport, clock=clock or __import__("time"))
        scope = {"bizSystemId": biz_system_id}
        topology_result = executor.execute(_topology_request(biz_system_id, time_context))
        performance_result = executor.execute(_performance_request(biz_system_id, time_context))
        candidates_result = executor.execute(_candidate_request(biz_system_id, time_context))

        artifacts = _collect_artifacts(source, source_run_id, run.run_id, scope, time_context, topology_result, performance_result, candidates_result)
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
        return _blocked_run(store, "discover", "DISCOVERY", "LIVE_EXECUTION_BUSY", requested_intent={"query": query})
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
        result = executor.execute(_business_tree_request(time_context))
        artifact = _targets_artifact(result, query, time_context)
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
    requested_intent = {
        "source_run_id": source_run_id,
        "source_item_ref": source_item_ref,
        "action": action,
    }
    if not store.acquire_live_lock():
        return _blocked_run(store, "investigate", "INVESTIGATION", "LIVE_EXECUTION_BUSY", requested_intent=requested_intent)
    try:
        try:
            source = _resolve_source(store, source_run_id, source_item_ref)
        except (FileNotFoundError, KeyError):
            return _blocked_run(store, "investigate", "INVESTIGATION", "INVALID_SOURCE_REF", requested_intent=requested_intent)
        if action not in source.get("available_actions", []):
            return _blocked_run(store, "investigate", "INVESTIGATION", "INVALID_ACTION", requested_intent=requested_intent)
        if action not in {"investigate_trace", "inspect_call_tree"}:
            return _blocked_run(store, "investigate", "INVESTIGATION", "ACTION_NOT_STABLE", requested_intent=requested_intent)
        if not _action_identity_complete(source, action):
            return _blocked_run(store, "investigate", "INVESTIGATION", "ACTION_IDENTITY_INCOMPLETE", requested_intent=requested_intent)

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
            "requested_intent": requested_intent,
        })
        executor = HttpExecutor(store=store, run=run, config=config, transport=transport, clock=clock or __import__("time"))
        if action == "investigate_trace":
            result = executor.execute(_trace_detail_request(source, time_context))
            artifact_name = "trace.json"
            artifact = _trace_artifact(result, source, source_run_id, time_context)
        else:
            result = executor.execute(_call_tree_request(source, time_context))
            artifact_name = "call_tree.json"
            artifact = _call_tree_artifact(result, source, source_run_id, time_context)
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
    safe_files = {"manifest.json", "preflight.json", "coverage.json", "run-meta.json"}
    for path in source.rglob("*.json"):
        rel = path.relative_to(source)
        if rel.parts[0] == "raw":
            if not rel.name.startswith("request-"):
                continue
        if rel.parts[0] == "evidence" or rel.name in safe_files:
            data = json.loads(path.read_text(encoding="utf-8"))
            sanitized = _sanitize(data, root=store.root)
            target = output_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"schema_version": 1, "command": "sanitized_export", "status": "SUCCESS", "output_path": str(output_dir)}


class Blocked(Exception):
    pass


def _blocked_run(
    store: RunStore,
    command: str,
    run_type: str,
    reason_code: str,
    *,
    requested_intent: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    run = store.begin_run(command=command, run_type=run_type)
    preflight = {
        "schema_version": 1,
        "command": command,
        "result": "BLOCKED",
        "reason_code": reason_code,
        "live_request_count": 0,
    }
    if requested_intent:
        preflight["requested_intent"] = requested_intent
    store.write_json(run.path / "preflight.json", preflight)
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
    if requested_intent:
        manifest["requested_intent"] = requested_intent
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
                "responseP75",
                "responseP95",
                "responseP99",
                "responseTimeMillisecondAvg",
                "throughput",
                "totalCount",
                "errorRate",
                "errorTotalCount",
                "slowCount",
                "exceptionCountTotal",
                "apdex",
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
    raw_action_type = identity.get("requestType") or identity.get("actionType") or ""
    action_type = raw_action_type.split(",")[0].strip() if "," in raw_action_type else raw_action_type
    return {
        "endpoint_id": "ep_post_server_api_action_trace_detail",
        "method": "POST",
        "path": "/server-api/action/trace/detail",
        "body_kind": "form",
        "body": {
            "bizSystemId": identity.get("bizSystemId"),
            "applicationId": identity.get("applicationId"),
            "actionId": identity.get("actionId"),
            "actionType": action_type,
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
            "actionType": identity.get("actionType") or identity.get("requestType"),
            "timePeriod": str(endpoint["timePeriod"]),
            "endTime": endpoint["endTime"],
            "lang": "zh_CN",
        },
    }


def _collect_artifacts(
    source,
    source_run_id,
    collect_run_id,
    scope,
    time_context,
    topology_result: ExecutionResult,
    performance_result: ExecutionResult,
    candidates_result: ExecutionResult,
):
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
        "topology.json": _topology_artifact(topology_result, scope, time_context),
        "performance.json": _performance_artifact(performance_result, scope, time_context),
        "candidates.json": _candidates_artifact(candidates_result, collect_run_id, scope, time_context),
    }


def _targets_artifact(result: ExecutionResult, query: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    if result.outcome == "FAILED":
        return _failed_artifact("targets", None, time_context, result, data={"query": query, "items": []})
    response = result.response or {}
    candidates = _business_candidates(response.get("data", []), query=query)
    return {
        "schema_version": 1,
        "kind": "targets",
        "status": "SUCCESS" if candidates else "EMPTY",
        "time_context": time_context,
        "derived_from": _derived_from(result),
        "execution": _execution_metadata(result),
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


def _topology_artifact(result: ExecutionResult, scope: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    if result.outcome == "FAILED":
        return _failed_artifact("topology", scope, time_context, result, data={"structural_nodes": [], "runtime_edges": []})
    response = result.response or {}
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    nodes = data.get("nodes") or data.get("nodeList") or data.get("nodeDataArray") or []
    edges = data.get("edges") or data.get("lines") or data.get("linkeDataArray") or []
    no_data = data.get("noData")
    has_content = bool(nodes or edges)
    if no_data is True and not has_content:
        has_content = False
    return {
        "schema_version": 1,
        "kind": "topology",
        "status": "SUCCESS" if has_content else "EMPTY",
        "scope": scope,
        "time_context": time_context,
        "derived_from": _derived_from(result),
        "execution": _execution_metadata(result),
        "data": {"structural_nodes": nodes, "runtime_edges": edges},
    }


def _performance_artifact(result: ExecutionResult, scope: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    if result.outcome == "FAILED":
        return _failed_artifact("performance", scope, time_context, result, data={"metrics": {}})
    response = result.response or {}
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    _SERIES_NAME_MAP = {
        "响应时间": "response_avg",
        "50分位值": "p50",
        "80分位值": "p80",
        "95分位值": "p95",
        "99分位值": "p99",
    }
    metrics = {
        "response_avg": {"semantic": "response_time", "aggregation": "average", "unit": "ms", "series": data.get("avg") or data.get("average") or []},
        "p50": {"semantic": "response_time", "aggregation": "p50", "unit": "ms", "series": data.get("p50") or data.get("P50") or []},
        "p80": {"semantic": "response_time", "aggregation": "p80", "unit": "ms", "series": data.get("p80") or data.get("P80") or []},
        "p95": {"semantic": "response_time", "aggregation": "p95", "unit": "ms", "series": data.get("p95") or data.get("P95") or []},
        "p99": {"semantic": "response_time", "aggregation": "p99", "unit": "ms", "series": data.get("p99") or data.get("P99") or []},
    }
    overview_data = data.get("overviews")
    if isinstance(overview_data, dict):
        metrics["overview"] = {
            "avg": {"value": overview_data.get("avg"), "unit": "ms"} if overview_data.get("avg") is not None else None,
            "max": {"value": overview_data.get("max"), "unit": "ms"} if overview_data.get("max") is not None else None,
        }
    series_array = data.get("series")
    if isinstance(series_array, list):
        for s in series_array:
            if not isinstance(s, dict):
                continue
            name = s.get("name", "")
            metric_key = _SERIES_NAME_MAP.get(name)
            if metric_key is None:
                continue
            points = s.get("data") or s.get("points") or []
            if isinstance(points, list):
                extracted = []
                for pt in points:
                    if isinstance(pt, dict) and "y" in pt:
                        extracted.append({"timestamp": pt.get("x"), "value": pt["y"]})
                if extracted:
                    metrics[metric_key]["series"] = extracted
    has_series = any(
        (isinstance(metric.get("series"), list) and len(metric["series"]) > 0)
        for metric in metrics.values()
        if isinstance(metric, dict)
    )
    return {
        "schema_version": 1,
        "kind": "performance",
        "status": "SUCCESS" if has_series else "EMPTY",
        "scope": scope,
        "time_context": time_context,
        "derived_from": _derived_from(result),
        "execution": _execution_metadata(result),
        "data": {"metrics": metrics},
    }


def _candidates_artifact(result: ExecutionResult, source_run_id: str, scope: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    if result.outcome == "FAILED":
        return _failed_artifact("candidates", scope, time_context, result, data={"items": [], "row_count": 0})
    artifact = normalize_candidates(
        response=result.response or {},
        source_run_id=source_run_id,
        scope=scope,
        time_context=time_context,
        raw_ref=_final_ref(result),
    )
    artifact["execution"] = _execution_metadata(result)
    return artifact


def _trace_artifact(result: ExecutionResult, source: Dict[str, Any], source_run_id: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    if result.outcome == "FAILED":
        return _failed_artifact("trace", None, time_context, result, data={"items": []})
    response = result.response or {}
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    identity = dict(source.get("wire_identity", {}))
    for key in ("bizSystemId", "applicationId", "actionId", "actionType"):
        if data.get(key) not in (None, ""):
            identity[key] = data[key]
    if identity.get("requestType") and not identity.get("actionType"):
        identity["actionType"] = identity["requestType"]
    if data.get("actionGuid"):
        identity["actionGuid"] = data["actionGuid"]
    trace_id = nested.get("id") or data.get("id") or data.get("traceId")
    if trace_id:
        identity["traceId"] = trace_id
    summary = {k: data.get(k) for k in ("duration", "respTime", "actionName", "actionAlias", "applicationName", "bizSystemName") if k in data}
    item = {
        "item_ref": "item-0001",
        "kind": "trace",
        "source_run_id": source_run_id,
        "wire_identity": identity,
        "source_refs": _derived_from(result),
        "summary": summary,
    }
    if is_inspect_call_tree_eligible(item):
        item["available_actions"] = ["inspect_call_tree"]
    return {
        "schema_version": 1,
        "kind": "trace",
        "status": "SUCCESS" if data else "EMPTY",
        "time_context": time_context,
        "derived_from": _derived_from(result),
        "execution": _execution_metadata(result),
        "data": {
            "summary": summary,
            "timeline": data.get("timeLine") or {},
            "trace_topology": data.get("topology") or {},
            "service_flow": data.get("serviceFlow") or {},
            "request_service_flow": data.get("requestServiceFlow") or {},
            "exceptions": data.get("exceptions") or [],
            "embedded_stack": _embedded_stack(data),
            "context": _trace_context(data),
            "items": [item] if data else [],
        },
    }


def _call_tree_artifact(result: ExecutionResult, source: Dict[str, Any], source_run_id: str, time_context: Dict[str, Any]) -> Dict[str, Any]:
    if result.outcome == "FAILED":
        return _failed_artifact("call_tree", None, time_context, result, data={"source_item": {"run_id": source_run_id, "item_ref": source.get("item_ref")}, "call_tree": {}})
    response = result.response or {}
    data = response.get("data", {})
    return {
        "schema_version": 1,
        "kind": "call_tree",
        "status": "SUCCESS" if data else "EMPTY",
        "time_context": time_context,
        "derived_from": _derived_from(result),
        "execution": _execution_metadata(result),
        "data": {"source_item": {"run_id": source_run_id, "item_ref": source.get("item_ref")}, "call_tree": data},
    }


def _failed_artifact(
    kind: str,
    scope: Optional[Dict[str, Any]],
    time_context: Dict[str, Any],
    result: ExecutionResult,
    *,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    artifact: Dict[str, Any] = {
        "schema_version": 1,
        "kind": kind,
        "status": "FAILED",
        "time_context": time_context,
        "derived_from": _derived_from(result),
        "execution": _execution_metadata(result),
        "error": _execution_error(result),
        "data": data,
    }
    if scope is not None:
        artifact["scope"] = scope
    return artifact


def _execution_metadata(result: ExecutionResult) -> Dict[str, Any]:
    data = {
        "outcome": result.outcome,
        "attempt_count": result.attempt_count,
        "attempt_refs": list(result.attempt_refs),
        "transient_retried": result.transient_retried,
        "auth_recovered": result.auth_recovered,
    }
    if result.reason_code:
        data["reason_code"] = result.reason_code
    if result.final_response_ref:
        data["final_response_ref"] = result.final_response_ref
    if result.final_error_ref:
        data["final_error_ref"] = result.final_error_ref
    return data


def _execution_error(result: ExecutionResult) -> Dict[str, Any]:
    error = {"reason_code": result.reason_code or "EXECUTION_FAILED"}
    response = result.response or {}
    status = response.get("transport_status", response.get("status"))
    if status is not None:
        error["status"] = status
    message = response.get("message") or response.get("msg")
    if message:
        error["message"] = message
    if result.final_error_ref:
        error["raw_error_ref"] = result.final_error_ref
    if result.final_response_ref:
        error["raw_response_ref"] = result.final_response_ref
    return error


def _derived_from(result: ExecutionResult) -> List[str]:
    ref = _final_ref(result)
    return [ref] if ref else []


def _final_ref(result: ExecutionResult) -> str:
    return result.final_response_ref or result.final_error_ref or ""


def _trace_context(data: Dict[str, Any]) -> Dict[str, Any]:
    keys = (
        "applicationName",
        "bizSystemName",
        "instanceId",
        "instanceName",
        "requestId",
        "refId",
        "actionType",
    )
    return {key: data.get(key) for key in keys if key in data}


def _embedded_stack(data: Dict[str, Any]) -> Dict[str, Any]:
    stacks: List[Any] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key == "stack" and isinstance(nested, list):
                    stacks.append(nested)
                else:
                    visit(nested)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit({"exceptions": data.get("exceptions"), "timeLine": data.get("timeLine")})
    return {"source": "trace_detail_embedded", "stacks": stacks}


def _action_identity_complete(source: Dict[str, Any], action: str) -> bool:
    if action == "investigate_trace":
        return is_investigate_trace_eligible(source)
    if action == "inspect_call_tree":
        return is_inspect_call_tree_eligible(source)
    return False


def _coverage_from_artifacts(artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    entries = {}
    for filename, artifact in artifacts.items():
        kind = filename.removesuffix(".json")
        step = {
            "capability": _capability_for_kind(kind),
            "status": artifact["status"],
            "evidence_refs": artifact.get("derived_from", []),
        }
        execution = artifact.get("execution")
        if execution:
            step.update({
                "attempt_count": execution.get("attempt_count"),
                "attempt_refs": execution.get("attempt_refs", []),
                "transient_retried": execution.get("transient_retried", False),
                "auth_recovered": execution.get("auth_recovered", False),
            })
            if execution.get("reason_code"):
                step["reason_code"] = execution["reason_code"]
        entries[kind] = {
            "status": artifact["status"],
            "steps": [step],
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
    identity_keys = {
        "wire_identity",
        "actionId",
        "actionGuid",
        "traceId",
        "bizSystemId",
        "applicationId",
        "systemId",
        "instanceId",
        "instanceName",
        "available_actions",
        "links",
        "url",
    }
    name_label_keys = {
        "display_name",
        "name",
        "applicationName",
        "bizSystemName",
        "actionName",
    }
    id_value_keys = {"bizSystemId", "applicationId", "actionId", "systemId", "instanceId", "actionGuid", "traceId"}
    pseudonyms = _PseudonymState()
    _collect_identity_values(value, pseudonyms)
    return _sanitize_with_state(value, root=root, secret_parts=secret_parts, identity_keys=identity_keys,
                               name_label_keys=name_label_keys, pseudonyms=pseudonyms)


class _PseudonymState:
    def __init__(self):
        self.name_map: Dict[str, str] = {}
        self.id_map: Dict[str, str] = {}
        self._name_counter = 0
        self._id_counter = 0

    def pseudonym_for_name(self, original: str, prefix: str) -> str:
        key = (prefix, original)
        if key not in self.name_map:
            self._name_counter += 1
            self.name_map[key] = f"{prefix}_{self._name_counter:03d}"
        return self.name_map[key]

    def pseudonym_for_id(self, original: str) -> str:
        if original not in self.id_map:
            self._id_counter += 1
            self.id_map[original] = f"ID_{self._id_counter:03d}"
        return self.id_map[original]


def _collect_identity_values(value: Any, state: _PseudonymState) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in ("bizSystemId", "applicationId", "actionId", "systemId", "instanceId", "actionGuid", "traceId"):
                if isinstance(nested, (str, int)) and nested not in (None, ""):
                    state.pseudonym_for_id(str(nested))
            _collect_identity_values(nested, state)
    elif isinstance(value, list):
        for item in value:
            _collect_identity_values(item, state)


def _sanitize_with_state(value: Any, *, root: Path, secret_parts: Tuple[str, ...],
                         identity_keys: Set[str], name_label_keys: Set[str],
                         pseudonyms: _PseudonymState) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, nested in value.items():
            if key in identity_keys or any(part in key.lower() for part in secret_parts):
                continue
            if key in name_label_keys and isinstance(nested, str) and nested:
                prefix_map = {
                    "display_name": "BS",
                    "bizSystemName": "BS",
                    "applicationName": "APP",
                    "actionName": "ACTION",
                    "name": "NAME",
                }
                prefix = prefix_map.get(key, "NAME")
                result[key] = pseudonyms.pseudonym_for_name(nested, prefix)
            else:
                result[key] = _sanitize_with_state(nested, root=root, secret_parts=secret_parts,
                                                   identity_keys=identity_keys, name_label_keys=name_label_keys,
                                                   pseudonyms=pseudonyms)
        return result
    if isinstance(value, list):
        return [_sanitize_with_state(item, root=root, secret_parts=secret_parts,
                                     identity_keys=identity_keys, name_label_keys=name_label_keys,
                                     pseudonyms=pseudonyms) for item in value]
    if isinstance(value, str):
        text = value.replace(str(root), "<local-path>")
        if any(part in text.lower() for part in secret_parts):
            return "<redacted>"
        return text
    if isinstance(value, (int, float)):
        text = str(value)
        if text in pseudonyms.id_map:
            return pseudonyms.id_map[text]
    return value
