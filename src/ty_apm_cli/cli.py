from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .auth import AuthError, AuthManager
from .catalog import Catalog, CatalogNotFound
from .config import load_config
from .envelope import emit, failure, request_id, success
from .http_client import TingyunClient
from .snapshots import collect_snapshot, plan_snapshot

ERROR_TYPES = {
    "ValidationError",
    "CatalogNotFound",
    "SafetyBlocked",
    "AuthError",
    "HttpError",
    "UpstreamError",
    "TimeoutError",
    "PartialFailure",
    "AmbiguousTarget",
    "InternalError",
}
DEFAULT_PAGE_NUMBER = 1
DEFAULT_PAGE_SIZE = 50


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        global_opts, rest = _global_options(argv)
        cfg = load_config(**global_opts)
        catalog = Catalog(cfg.catalog_path)
        if not rest:
            return emit(_err("ty-apm", "ValidationError", "command is required", catalog_ref=catalog.ref()))
        group = rest[0]
        args = rest[1:]
        if group == "catalog":
            env = _catalog_cmd(catalog, args)
        elif group == "auth":
            env = _auth_cmd(cfg, catalog, args)
        elif group == "api":
            env = _api_cmd(cfg, catalog, args)
        elif group == "resolve":
            env = _resolve_cmd(cfg, catalog, args)
        elif group == "snapshot":
            env = _snapshot_cmd(cfg, catalog, args)
        else:
            env = _err(group, "ValidationError", f"unknown command group: {group}", catalog_ref=catalog.ref())
        return emit(env)
    except CatalogNotFound as exc:
        return emit(failure("catalog", "CatalogNotFound", str(exc), retryable=False))
    except ValueError as exc:
        return emit(failure("ty-apm", "ValidationError", str(exc), retryable=False))
    except Exception as exc:
        return emit(failure("ty-apm", "InternalError", str(exc), retryable=False))


def _catalog_cmd(catalog: Catalog, args: List[str]) -> Dict[str, Any]:
    action = args[0] if args else ""
    meta = _meta(catalog)
    if action == "list":
        return success("catalog.list", {"endpoints": catalog.summaries(), "stats": catalog.stats()}, meta=meta)
    if action == "show" and len(args) >= 2:
        return success("catalog.show", catalog.get(args[1]), meta={**meta, "catalog_id": args[1]})
    if action == "search" and len(args) >= 2:
        matches = catalog.search(args[1])
        return success("catalog.search", {"endpoints": catalog.summaries(matches), "count": len(matches)}, meta=meta)
    if action == "filter":
        opts = _options(args[1:])
        matches = catalog.filter(safety=opts.get("safety"), domain=opts.get("domain"))
        return success("catalog.filter", {"endpoints": catalog.summaries(matches), "count": len(matches)}, meta=meta)
    if action == "audit-safety":
        audit = catalog.audit_safety()
        env = success("catalog.audit-safety", audit, meta=meta)
        if not audit["ok"]:
            return failure("catalog.audit-safety", "ValidationError", "catalog safety audit failed", meta=meta, details=audit)
        return env
    return _err("catalog", "ValidationError", "expected list, show, search, filter, or audit-safety", catalog_ref=catalog.ref())


def _auth_cmd(cfg: Any, catalog: Catalog, args: List[str]) -> Dict[str, Any]:
    action = args[0] if args else ""
    meta = _meta(catalog)
    manager = AuthManager(cfg)
    try:
        if action == "test":
            token = manager.get_token()
            return success("auth.test", {"authenticated": True, "token": {"from_cache": token.from_cache, "expires_at": token.expires_at}}, meta=meta)
        if action == "clear-token":
            return success("auth.clear-token", {"cleared": manager.clear_token()}, meta=meta)
    except AuthError as exc:
        return failure(f"auth.{action or 'unknown'}", "AuthError", str(exc), meta=meta, retryable=True)
    return _err("auth", "ValidationError", "expected test or clear-token", catalog_ref=catalog.ref())


def _api_cmd(cfg: Any, catalog: Catalog, args: List[str]) -> Dict[str, Any]:
    if len(args) < 2 or args[0] != "call":
        return _err("api", "ValidationError", "expected api call <catalog_id>", catalog_ref=catalog.ref())
    catalog_id = args[1]
    try:
        params = _parse_params(args[2:])
        entry = catalog.get(catalog_id)
    except CatalogNotFound as exc:
        return failure("api.call", "CatalogNotFound", str(exc), meta={**_meta(catalog), "catalog_id": catalog_id}, retryable=False)
    except ValueError as exc:
        return failure("api.call", "ValidationError", str(exc), meta={**_meta(catalog), "catalog_id": catalog_id}, retryable=False)
    return TingyunClient(cfg, catalog_ref=catalog.ref()).call(entry, params).envelope


def _resolve_cmd(cfg: Any, catalog: Catalog, args: List[str]) -> Dict[str, Any]:
    if not args or args[0] != "application":
        return _err("resolve", "ValidationError", "expected resolve application", catalog_ref=catalog.ref())
    opts = _options(args[1:])
    name = opts.get("name") or opts.get("application-name")
    biz = opts.get("business-system-name")
    if not name:
        return failure("resolve.application", "ValidationError", "--name or --application-name is required", meta=_meta(catalog), retryable=False)
    resolver = _resolver_entry(catalog)
    if resolver is None:
        return failure("resolve.application", "PartialFailure", "no executable application list catalog entry is available", meta=_meta(catalog), retryable=False)
    params = _required_defaults(resolver)
    record = TingyunClient(cfg, catalog_ref=catalog.ref()).call(resolver, params, command="resolve.application")
    if not record.envelope.get("ok"):
        record.envelope["command"] = "resolve.application"
        return record.envelope
    candidates = _extract_application_candidates(record.response, name, biz)
    if not candidates:
        return success("resolve.application", {"candidates": [], "resolved": None}, meta=_meta(catalog))
    if len(candidates) > 1:
        return failure("resolve.application", "AmbiguousTarget", "multiple application candidates matched", meta=_meta(catalog), details={"candidates": candidates}, retryable=False)
    return success("resolve.application", {"resolved": candidates[0], "candidates": candidates}, meta=_meta(catalog))


def _snapshot_cmd(cfg: Any, catalog: Catalog, args: List[str]) -> Dict[str, Any]:
    if len(args) < 1 or args[0] != "collect":
        return _err("snapshot", "ValidationError", "expected snapshot collect", catalog_ref=catalog.ref())
    opts = _options(args[1:])
    profile = opts.get("profile")
    if not profile:
        return failure("snapshot.collect", "ValidationError", "--profile is required", meta=_meta(catalog), retryable=False)
    try:
        common = {
            "profile": profile,
            "catalog": catalog,
            "application_id": opts.get("application-id"),
            "since": opts.get("since", "60m"),
            "from_time": opts.get("from"),
            "to_time": opts.get("to"),
            "sample_limit": int(opts.get("sample-limit", 20)),
            "page_limit": int(opts.get("page-limit", 3)),
        }
        if opts.get("plan-only") == "true":
            data = plan_snapshot(**common)
            return success("snapshot.collect", data, meta=_meta(catalog))
        data = collect_snapshot(
            config=cfg,
            run_id=opts.get("run-id"),
            **common,
        )
        meta = {**_meta(catalog), "run_id": data["run_id"]}
        if data.get("coverage", {}).get("failures"):
            return failure(
                "snapshot.collect",
                "PartialFailure",
                "snapshot completed with incomplete evidence",
                meta=meta,
                details=data,
                retryable=False,
            )
        return success("snapshot.collect", data, meta=meta)
    except ValueError as exc:
        return failure("snapshot.collect", "ValidationError", str(exc), meta=_meta(catalog), retryable=False)


def _global_options(argv: List[str]) -> Tuple[Dict[str, Any], List[str]]:
    opts: Dict[str, Any] = {}
    rest: List[str] = []
    i = 0
    names = {
        "--base-url": "base_url",
        "--api-key": "api_key",
        "--secret-key": "secret_key",
        "--artifacts-dir": "artifacts_dir",
        "--catalog-path": "catalog_path",
        "--token-cache-path": "token_cache_path",
        "--config": "config_path",
        "--timeout": "timeout_seconds",
    }
    while i < len(argv):
        arg = argv[i]
        if arg == "--no-token-cache":
            opts["no_token_cache"] = True
            i += 1
        elif arg in names:
            if i + 1 >= len(argv):
                raise ValueError(f"{arg} requires a value")
            value: Any = argv[i + 1]
            if arg == "--timeout":
                value = float(value)
            opts[names[arg]] = value
            i += 2
        else:
            rest = argv[i:]
            break
    opts.setdefault("no_token_cache", False)
    return opts, rest


def _options(args: List[str]) -> Dict[str, str]:
    opts: Dict[str, str] = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if not arg.startswith("--"):
            i += 1
            continue
        key = arg[2:]
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            opts[key] = "true"
            i += 1
        else:
            opts[key] = args[i + 1]
            i += 2
    return opts


def _parse_params(args: List[str]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--params":
            if i + 1 >= len(args):
                raise ValueError("--params requires a file path")
            with Path(args[i + 1]).open("r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            if not isinstance(loaded, dict):
                raise ValueError("--params file must contain a JSON object")
            params.update(loaded)
            i += 2
        elif arg == "--param":
            if i + 1 >= len(args) or "=" not in args[i + 1]:
                raise ValueError("--param requires key=value")
            key, value = args[i + 1].split("=", 1)
            params[key] = _json_value(value)
            i += 2
        else:
            raise ValueError(f"unknown api call option: {arg}")
    return params


def _json_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _resolver_entry(catalog: Catalog) -> Optional[Dict[str, Any]]:
    preferred = [
        "application.3_1_1.application_app_list",
        "application.3_1_1.application_app_list.2",
        "application.3_2_2.application_app_select",
    ]
    for catalog_id in preferred:
        try:
            entry = catalog.get(catalog_id)
        except CatalogNotFound:
            continue
        if entry.get("safety") == "read" and entry.get("execution_supported"):
            return entry
    for entry in catalog.entries:
        if entry.get("domain") == "application" and entry.get("safety") == "read" and "list" in entry.get("id", ""):
            return entry
    return None


def _required_defaults(entry: Dict[str, Any]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    for param in entry.get("request", {}).get("params", []):
        if not param.get("required"):
            continue
        name = param.get("name")
        if not name:
            continue
        lower = name.lower()
        if lower == "timeperiod":
            params[name] = 60
        elif "lang" in lower:
            params[name] = "zh_CN"
        elif lower in {"page", "pagenum", "pageindex"}:
            params[name] = DEFAULT_PAGE_NUMBER
        elif lower == "pagesize":
            params[name] = DEFAULT_PAGE_SIZE
        elif lower.endswith("id"):
            continue
        else:
            continue
    return params


def _extract_application_candidates(payload: Any, name: str, biz: Optional[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            lowered = {str(k).lower(): v for k, v in value.items()}
            app_name = _first(lowered, ["applicationname", "appname", "name", "application_name"])
            app_id = _first(lowered, ["applicationid", "appid", "id", "application_id"])
            biz_name = _first(lowered, ["bizsystemname", "businesssystemname", "business_system_name"])
            if app_name is not None and str(app_name) == name:
                if biz is None or biz_name is None or str(biz_name) == biz:
                    rows.append({"application_id": app_id, "application_name": app_name, "business_system_name": biz_name})
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    unique: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        key = (row.get("application_id"), row.get("application_name"), row.get("business_system_name"))
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def _first(mapping: Dict[str, Any], names: List[str]) -> Any:
    for name in names:
        if name in mapping:
            return mapping[name]
    return None


def _meta(catalog: Catalog) -> Dict[str, Any]:
    return {"request_id": request_id(), "run_id": None, "catalog_ref": catalog.ref()}


def _err(command: str, error_type: str, message: str, *, catalog_ref: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return failure(command, error_type, message, meta={"request_id": request_id(), "run_id": None, "catalog_ref": catalog_ref or {}}, retryable=False)


if __name__ == "__main__":
    raise SystemExit(main())
