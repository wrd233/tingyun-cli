from __future__ import annotations

import argparse
import json
from pathlib import Path

from .candidate_matching import match_candidates
from .candidates import inspect_candidates_all, inspect_candidates_filter, inspect_candidates_top
from .compare import compare_windows, diff_call_trees
from .commands import export_sanitized_run, plan_collect, run_collect, run_discover, run_investigate, run_source_capability
from .config import load_config
from .evidence_adapter import adapt_evidence
from .evidence_composition import CompositionError, compile_evidence
from .evidence_validation import validate_compiled_dir
from .narrowing import adaptive_window_narrow, locate_peak
from .promotion import promotion_matrix
from .selection import select_trace, trace_candidates_from_rows
from .storage import RunStore
from .triage import analyze_external_dependencies, classify_request_path, cluster_error_signatures
from .trace_sample_assessment import assess_trace_sample, candidate_from_evidence
from .system_model import SystemModelError, compile_system_model, diff_system_models, validate_system_model
from .workflows import workflow_plan


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tingyun")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--data-root", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="Core Live read-only discovery")
    discover.add_argument("--query", default="")

    collect = sub.add_parser("collect", help="Core Live read-only evidence collection")
    collect.add_argument("--source-run-id", required=True)
    collect.add_argument("--source-item-ref", required=True)
    collect.add_argument("--time-context", required=True)
    collect.add_argument("--plan-only", action="store_true")

    investigate = sub.add_parser("investigate", help="Core Live read-only investigation")
    investigate.add_argument("--source-run-id", required=True)
    investigate.add_argument("--source-item-ref", required=True)
    investigate.add_argument("--action", required=True)

    inspect = sub.add_parser("inspect", help="Local-only Candidate inspection")
    inspect_sub = inspect.add_subparsers(dest="inspect_command", required=True)
    candidates = inspect_sub.add_parser("candidates")
    candidates.add_argument("mode", choices=["all", "top", "filter", "match"])
    candidates.add_argument("--run-id", required=True)
    candidates.add_argument("--metric")
    candidates.add_argument("--limit", type=int, default=10)
    candidates.add_argument("--operator")
    candidates.add_argument("--value", type=float)
    candidates.add_argument("--name")
    candidates.add_argument("--application")
    candidates.add_argument("--route-fragment")
    candidates.add_argument("--request-type")

    export = sub.add_parser("sanitized-export", help="Local-only identity-sanitized handoff")
    export.add_argument("--run-id", required=True)
    export.add_argument("--output", type=Path, required=True)

    depth = sub.add_parser("depth", help="Local-only deterministic investigation primitives")
    depth_sub = depth.add_subparsers(dest="depth_command", required=True)
    depth_sub.add_parser("promotion-matrix")
    trace_candidates = depth_sub.add_parser("trace-candidates")
    trace_candidates.add_argument("--input", type=Path, required=True)
    trace_candidates.add_argument("--scope", required=True)
    trace_candidates.add_argument("--source", required=True)
    trace_candidates.add_argument("--time-window", required=True)
    select = depth_sub.add_parser("select-trace")
    select.add_argument("--input", type=Path, required=True)
    select.add_argument("--strategy", required=True, choices=["slowest", "error", "exact", "newest", "oldest"])
    select.add_argument("--trace-id")
    narrow = depth_sub.add_parser("narrow-window")
    narrow.add_argument("--input", type=Path, required=True)
    narrow.add_argument("--signal", required=True)
    narrow.add_argument("--min-window-minutes", type=int, required=True)
    narrow.add_argument("--max-steps", type=int, required=True)
    narrow.add_argument("--request-budget", type=int, required=True)
    triage = depth_sub.add_parser("triage-path")
    triage.add_argument("--path", required=True)
    peak = depth_sub.add_parser("locate-peak")
    peak.add_argument("--input", type=Path, required=True)
    peak.add_argument("--metric-semantic-status", required=True, choices=["VERIFIED", "AMBIGUOUS", "UNKNOWN"])
    peak.add_argument("--request-budget", type=int, default=3)
    cluster = depth_sub.add_parser("cluster-errors")
    cluster.add_argument("--input", type=Path, required=True)
    compare = depth_sub.add_parser("compare-windows")
    compare.add_argument("--before", type=Path, required=True)
    compare.add_argument("--incident", type=Path, required=True)
    diff = depth_sub.add_parser("diff-call-trees")
    diff.add_argument("--baseline", type=Path, required=True)
    diff.add_argument("--abnormal", type=Path, required=True)
    external = depth_sub.add_parser("analyze-external")
    external.add_argument("--input", type=Path, required=True)
    workflow = depth_sub.add_parser("workflow-plan")
    workflow.add_argument("--workflow", required=True, choices=["slow_transaction", "external_dependency_timeout", "instance_anomaly", "transaction_error", "alarm_to_trace"])
    workflow.add_argument("--source", type=Path, required=True)
    workflow.add_argument("--max-live-requests", type=int, default=20)
    sample = depth_sub.add_parser("trace-sample-assess")
    sample.add_argument("--candidate", type=Path, required=True)
    sample.add_argument("--candidate-item-ref")
    sample.add_argument("--trace", type=Path, required=True)
    sample.add_argument("--alarm-metric")
    compile_parser = depth_sub.add_parser("evidence-compile")
    compile_parser.add_argument("--manifest", type=Path, required=True)
    compile_parser.add_argument("--output-dir", type=Path, required=True)
    validate_parser = depth_sub.add_parser("evidence-validate")
    validate_parser.add_argument("--compiled-dir", type=Path, required=True)
    model_compile = depth_sub.add_parser("system-model-compile")
    model_compile.add_argument("--manifest", type=Path, required=True)
    model_compile.add_argument("--output-dir", type=Path, required=True)
    model_validate = depth_sub.add_parser("system-model-validate")
    model_validate.add_argument("--compiled-dir", type=Path, required=True)
    model_diff = depth_sub.add_parser("system-model-diff")
    model_diff.add_argument("--before", type=Path, required=True)
    model_diff.add_argument("--after", type=Path, required=True)

    source = sub.add_parser("source", help="Advanced explicit read-only acquisition")
    source_sub = source.add_subparsers(dest="source_command", required=True)
    alarm_events = source_sub.add_parser("alarm-events")
    alarm_events.add_argument("--time-context", required=True)
    for name in ("performance-error-series", "performance-throughput-series", "alarm-detail", "alarm-metric-series", "application-instances", "external-calls", "trace-exceptions", "trace-stack"):
        source_parser = source_sub.add_parser(name)
        _add_source_identity_args(source_parser)
        source_parser.add_argument("--time-context", required=True)
    recent_requests = source_sub.add_parser("recent-requests")
    _add_source_identity_args(recent_requests)
    recent_requests.add_argument("--time-context", required=True)
    recent_requests.add_argument("--ranking", choices=["response", "error", "throughput"], default="response")

    args = parser.parse_args(argv)
    if args.command == "depth":
        data_root = None
        if args.depth_command in {"evidence-compile", "system-model-compile"}:
            data_root = load_config(args.config, data_root=args.data_root).data_root
        try:
            result = _run_depth_command(args, data_root=data_root)
        except (CompositionError, SystemModelError) as exc:
            result = {"schema_version": 1, "command": f"depth {args.depth_command}", "status": "BLOCKED", "reason_code": exc.code, "message": str(exc), "actual_request_count": 0}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    config = load_config(args.config, data_root=args.data_root)
    if args.command == "inspect":
        run_path = config.data_root / "runs" / args.run_id
        try:
            if args.mode == "all":
                result = inspect_candidates_all(run_path)
            elif args.mode == "top":
                result = inspect_candidates_top(run_path, metric=args.metric, limit=args.limit)
            elif args.mode == "filter":
                result = inspect_candidates_filter(run_path, metric=args.metric, operator=args.operator, value=args.value)
            else:
                if not args.name:
                    raise ValueError("candidate name is required")
                artifact = _read_json(run_path / "evidence" / "candidates.json")
                result = match_candidates(artifact, run_id=args.run_id, name=args.name, application=args.application, route_fragment=args.route_fragment, request_type=args.request_type)
        except ValueError as exc:
            result = {"schema_version": 1, "command": "inspect", "status": "LOCAL_ERROR", "reason_code": _inspect_reason_code(str(exc)), "message": str(exc)}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    store = RunStore(config.data_root)
    store.freeze_stale_inflight()
    if args.command == "discover":
        result = run_discover(store=store, config=config, query=args.query)
    elif args.command == "collect":
        if args.plan_only:
            result = plan_collect(store, args.source_run_id, args.source_item_ref, args.time_context)
        else:
            result = run_collect(
                store=store,
                config=config,
                source_run_id=args.source_run_id,
                source_item_ref=args.source_item_ref,
                time_context_value=args.time_context,
            )
    elif args.command == "investigate":
        result = run_investigate(
            store=store,
            config=config,
            source_run_id=args.source_run_id,
            source_item_ref=args.source_item_ref,
            action=args.action,
        )
    elif args.command == "source":
        result = run_source_capability(
            store=store,
            config=config,
            capability=_source_capability_name(args.source_command),
            source_run_id=getattr(args, "source_run_id", None),
            source_item_ref=getattr(args, "source_item_ref", None),
            time_context_value=args.time_context,
            ranking=getattr(args, "ranking", "response"),
        )
    else:
        result = export_sanitized_run(store, args.run_id, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


def _inspect_reason_code(message: str) -> str:
    if message.startswith("unavailable metric:"):
        return "UNAVAILABLE_METRIC"
    if message.startswith("unsupported metric:"):
        return "UNSUPPORTED_METRIC"
    if message.startswith("unsupported operator:"):
        return "UNSUPPORTED_OPERATOR"
    return "LOCAL_INSPECT_ERROR"


def _add_source_identity_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-item-ref", required=True)


def _source_capability_name(command_name: str) -> str:
    return {
        "performance-error-series": "performance_error_series",
        "performance-throughput-series": "performance_throughput_series",
        "alarm-events": "alarm_events",
        "alarm-detail": "alarm_detail",
        "alarm-metric-series": "alarm_metric_series",
        "recent-requests": "recent_requests",
        "application-instances": "application_instances",
        "external-calls": "external_calls",
        "trace-exceptions": "trace_exceptions",
        "trace-stack": "trace_stack",
    }[command_name]


def _run_depth_command(args, *, data_root=None) -> dict:
    if args.depth_command == "promotion-matrix":
        return {"schema_version": 1, "command": "depth promotion-matrix", "status": "SUCCESS", "actual_request_count": 0, "capabilities": promotion_matrix()}
    if args.depth_command == "trace-candidates":
        rows = adapt_evidence(_read_json(args.input), "candidate_items")
        items = trace_candidates_from_rows(rows, scope=json.loads(args.scope), source=json.loads(args.source), time_window=json.loads(args.time_window))
        return {"schema_version": 1, "command": "depth trace-candidates", "status": "SUCCESS", "actual_request_count": 0, "candidate_count": len(items), "items": items}
    if args.depth_command == "select-trace":
        selected = select_trace(_items_from_json(_read_json(args.input)), strategy=args.strategy, trace_id=args.trace_id)
        return {"schema_version": 1, "command": "depth select-trace", "status": "SUCCESS", "actual_request_count": 0, "selected": selected}
    if args.depth_command == "narrow-window":
        windows = adapt_evidence(_read_json(args.input), "performance_windows")
        result = adaptive_window_narrow(windows, signal=args.signal, min_window_minutes=args.min_window_minutes, max_steps=args.max_steps, request_budget=args.request_budget)
        return {"schema_version": 1, "command": "depth narrow-window", "status": result["status"], "actual_request_count": 0, "result": result}
    if args.depth_command == "triage-path":
        return {"schema_version": 1, "command": "depth triage-path", "status": "SUCCESS", "actual_request_count": 0, "classification": classify_request_path(args.path)}
    if args.depth_command == "locate-peak":
        windows = adapt_evidence(_read_json(args.input), "performance_windows")
        result = locate_peak(windows=windows, metric_semantic_status=args.metric_semantic_status, candidates=[], request_budget=args.request_budget)
        return {"schema_version": 1, "command": "depth locate-peak", "status": result["status"], "actual_request_count": 0, "result": result}
    if args.depth_command == "cluster-errors":
        events = adapt_evidence(_read_json(args.input), "error_events")
        return {"schema_version": 1, "command": "depth cluster-errors", "status": "SUCCESS", "actual_request_count": 0, "clusters": cluster_error_signatures(events)}
    if args.depth_command == "compare-windows":
        return {"schema_version": 1, "command": "depth compare-windows", "status": "SUCCESS", "actual_request_count": 0, "comparison": compare_windows(before=_read_json(args.before), incident=_read_json(args.incident))}
    if args.depth_command == "diff-call-trees":
        baseline = adapt_evidence(_read_json(args.baseline), "call_tree")
        abnormal = adapt_evidence(_read_json(args.abnormal), "call_tree")
        return {"schema_version": 1, "command": "depth diff-call-trees", "status": "SUCCESS", "actual_request_count": 0, "diff": diff_call_trees(baseline, abnormal)}
    if args.depth_command == "analyze-external":
        return {"schema_version": 1, "command": "depth analyze-external", "status": "SUCCESS", "actual_request_count": 0, "analysis": analyze_external_dependencies(_read_json(args.input))}
    if args.depth_command == "workflow-plan":
        plan = workflow_plan(args.workflow, source=_read_json(args.source), max_live_requests=args.max_live_requests)
        return {"schema_version": 1, "command": "depth workflow-plan", "status": plan["status"], "actual_request_count": 0, "plan": plan}
    if args.depth_command == "trace-sample-assess":
        candidate = candidate_from_evidence(_read_json(args.candidate), args.candidate_item_ref)
        assessment = assess_trace_sample(candidate, _read_json(args.trace), alarm_metric=args.alarm_metric)
        return {"schema_version": 1, "command": "depth trace-sample-assess", "status": "SUCCESS", "actual_request_count": 0, "assessment": assessment}
    if args.depth_command == "evidence-compile":
        if data_root is None:
            raise CompositionError("INVALID_INVESTIGATION_MANIFEST", "data root is required")
        result = compile_evidence(args.manifest, data_root=data_root, output_dir=args.output_dir)
        result["actual_request_count"] = 0
        return result
    if args.depth_command == "evidence-validate":
        result = validate_compiled_dir(args.compiled_dir)
        return {**result, "command": "depth evidence-validate", "actual_request_count": 0}
    if args.depth_command == "system-model-compile":
        if data_root is None:
            raise SystemModelError("INVALID_SYSTEM_MODEL_MANIFEST", "data root is required")
        return compile_system_model(args.manifest, data_root=data_root, output_dir=args.output_dir)
    if args.depth_command == "system-model-validate":
        return {**validate_system_model(args.compiled_dir), "command": "depth system-model-validate", "actual_request_count": 0}
    if args.depth_command == "system-model-diff":
        return {**diff_system_models(args.before, args.after), "command": "depth system-model-diff", "actual_request_count": 0}
    raise ValueError(f"unsupported depth command: {args.depth_command}")


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _items_from_json(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        nested = data.get("data", {})
        if isinstance(nested, dict) and isinstance(nested.get("items"), list):
            return nested["items"]
        if isinstance(data.get("items"), list):
            return data["items"]
    raise ValueError("input JSON must be an item list or contain data.items")
