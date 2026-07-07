from __future__ import annotations

import argparse
import json
from pathlib import Path

from .candidates import inspect_candidates_all, inspect_candidates_filter, inspect_candidates_top
from .commands import export_sanitized_run, plan_collect, run_collect, run_discover, run_investigate
from .config import load_config
from .storage import RunStore


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tingyun")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--data-root", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover")
    discover.add_argument("--query", default="")

    collect = sub.add_parser("collect")
    collect.add_argument("--source-run-id", required=True)
    collect.add_argument("--source-item-ref", required=True)
    collect.add_argument("--time-context", required=True)
    collect.add_argument("--plan-only", action="store_true")

    investigate = sub.add_parser("investigate")
    investigate.add_argument("--source-run-id", required=True)
    investigate.add_argument("--source-item-ref", required=True)
    investigate.add_argument("--action", required=True)

    inspect = sub.add_parser("inspect")
    inspect_sub = inspect.add_subparsers(dest="inspect_command", required=True)
    candidates = inspect_sub.add_parser("candidates")
    candidates.add_argument("mode", choices=["all", "top", "filter"])
    candidates.add_argument("--run-id", required=True)
    candidates.add_argument("--metric")
    candidates.add_argument("--limit", type=int, default=10)
    candidates.add_argument("--operator")
    candidates.add_argument("--value", type=float)

    export = sub.add_parser("sanitized-export")
    export.add_argument("--run-id", required=True)
    export.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    config = load_config(args.config, data_root=args.data_root)
    store = RunStore(config.data_root)
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
    elif args.command == "inspect":
        run_path = store.run_path(args.run_id)
        try:
            if args.mode == "all":
                result = inspect_candidates_all(run_path)
            elif args.mode == "top":
                result = inspect_candidates_top(run_path, metric=args.metric, limit=args.limit)
            else:
                result = inspect_candidates_filter(run_path, metric=args.metric, operator=args.operator, value=args.value)
        except ValueError as exc:
            result = {
                "schema_version": 1,
                "command": "inspect",
                "status": "LOCAL_ERROR",
                "reason_code": _inspect_reason_code(str(exc)),
                "message": str(exc),
            }
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
