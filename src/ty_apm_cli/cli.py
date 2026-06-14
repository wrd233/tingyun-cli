from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer

from .artifacts import RunRecorder
from .auth import AuthError, AuthManager
from .catalog import Catalog, CatalogError
from .client import TingyunClient
from .config import AppConfig, load_config
from .envelope import emit, failure, success


app = typer.Typer(add_completion=False)
catalog_app = typer.Typer(add_completion=False)
auth_app = typer.Typer(add_completion=False)
api_app = typer.Typer(add_completion=False)
business_system_app = typer.Typer(add_completion=False)
application_app = typer.Typer(add_completion=False)
transaction_app = typer.Typer(add_completion=False)
service_interface_app = typer.Typer(add_completion=False)
background_task_app = typer.Typer(add_completion=False)
component_app = typer.Typer(add_completion=False)
error_app = typer.Typer(add_completion=False)
trace_app = typer.Typer(add_completion=False)
config_app = typer.Typer(add_completion=False)
health_rule_app = typer.Typer(add_completion=False)


def _ctx_config(ctx: typer.Context) -> AppConfig:
    if not ctx.obj or "config" not in ctx.obj:
        ctx.obj = {"config": load_config()}
    return ctx.obj["config"]


def _catalog(ctx: typer.Context) -> Catalog:
    return Catalog(_ctx_config(ctx).catalog_path)


def _load_json_object(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError("--params must point to a JSON object")
    return payload


def _parse_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _merge_params(params_file: Optional[Path], param: List[str]) -> Dict[str, Any]:
    params = _load_json_object(params_file)
    for item in param:
        if "=" not in item:
            raise ValueError("--param must use key=value")
        key, value = item.split("=", 1)
        params[key] = _parse_value(value)
    return params


def _call_endpoint(
    ctx: typer.Context,
    *,
    command: str,
    endpoint: Dict[str, Any],
    params: Dict[str, Any],
) -> None:
    cfg = _ctx_config(ctx)
    recorder = RunRecorder(cfg)
    envelope = TingyunClient(cfg, recorder=recorder).call(endpoint, params)
    envelope["command"] = command
    emit(envelope)


def _call_path(
    ctx: typer.Context,
    *,
    command: str,
    path: str,
    params: Dict[str, Any],
    title_contains: Optional[str] = None,
) -> None:
    try:
        endpoint = _catalog(ctx).find_by_path(path, title_contains=title_contains)
        _call_endpoint(ctx, command=command, endpoint=endpoint, params=params)
    except CatalogError as exc:
        emit(failure(command, "CatalogError", str(exc), retryable=False))


@app.callback()
def main(
    ctx: typer.Context,
    base_url: Optional[str] = typer.Option(None, "--base-url"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    secret_key: Optional[str] = typer.Option(None, "--secret-key"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir"),
    catalog_path: Optional[str] = typer.Option(None, "--catalog-path"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
    no_token_cache: bool = typer.Option(False, "--no-token-cache"),
    config_path: Optional[str] = typer.Option(None, "--config"),
) -> None:
    ctx.obj = {
        "config": load_config(
            base_url=base_url,
            api_key=api_key,
            secret_key=secret_key,
            output_dir=output_dir,
            catalog_path=catalog_path,
            run_id=run_id,
            no_token_cache=no_token_cache,
            config_path=config_path,
        )
    }


@catalog_app.command("list")
def catalog_list(ctx: typer.Context) -> None:
    catalog = _catalog(ctx)
    emit(success("catalog.list", {"endpoints": catalog.summaries(), "stats": catalog.stats()}))


@catalog_app.command("show")
def catalog_show(ctx: typer.Context, catalog_id: str) -> None:
    try:
        emit(success("catalog.show", _catalog(ctx).get(catalog_id)))
    except CatalogError as exc:
        emit(failure("catalog.show", "CatalogError", str(exc), retryable=False, meta={"catalog_id": catalog_id}))


@catalog_app.command("search")
def catalog_search(ctx: typer.Context, keyword: str) -> None:
    catalog = _catalog(ctx)
    matches = catalog.search(keyword)
    emit(success("catalog.search", {"endpoints": catalog.summaries(matches), "count": len(matches)}))


@catalog_app.command("filter")
def catalog_filter(
    ctx: typer.Context,
    domain: Optional[str] = typer.Option(None, "--domain"),
    safety: Optional[str] = typer.Option(None, "--safety"),
    confidence: Optional[str] = typer.Option(None, "--confidence"),
) -> None:
    catalog = _catalog(ctx)
    matches = catalog.filter(domain=domain, safety=safety, confidence=confidence)
    emit(success("catalog.filter", {"endpoints": catalog.summaries(matches), "count": len(matches)}))


@catalog_app.command("test-plan")
def catalog_test_plan(ctx: typer.Context) -> None:
    emit(success("catalog.test-plan", _catalog(ctx).test_plan()))


@catalog_app.command("audit-safety")
def catalog_audit_safety(ctx: typer.Context) -> None:
    audit = _catalog(ctx).audit_safety()
    emit(success("catalog.audit-safety", audit))


@catalog_app.command("stats")
def catalog_stats(ctx: typer.Context) -> None:
    emit(success("catalog.stats", _catalog(ctx).stats()))


@auth_app.command("test")
def auth_test(ctx: typer.Context, force_refresh: bool = typer.Option(False, "--force-refresh")) -> None:
    cfg = _ctx_config(ctx)
    try:
        token = AuthManager(cfg).get_token(force_refresh=force_refresh)
        emit(
            success(
                "auth.test",
                {
                    "authenticated": True,
                    "token": {"from_cache": token.from_cache, "expires_at": token.expires_at},
                },
            )
        )
    except AuthError as exc:
        emit(failure("auth.test", "AuthError", str(exc), retryable=True))


@auth_app.command("clear-token")
def auth_clear_token(ctx: typer.Context) -> None:
    cleared = AuthManager(_ctx_config(ctx)).clear_token()
    emit(success("auth.clear-token", {"cleared": cleared}))


@api_app.command("call")
def api_call(
    ctx: typer.Context,
    catalog_id: str,
    params_file: Optional[Path] = typer.Option(None, "--params", exists=True, file_okay=True, dir_okay=False),
    param: List[str] = typer.Option([], "--param"),
) -> None:
    try:
        params = _merge_params(params_file, param)
        endpoint = _catalog(ctx).get(catalog_id)
        _call_endpoint(ctx, command="api.call", endpoint=endpoint, params=params)
    except (CatalogError, ValueError, OSError, json.JSONDecodeError) as exc:
        emit(failure("api.call", exc.__class__.__name__, str(exc), retryable=False, meta={"catalog_id": catalog_id}))


@business_system_app.command("list")
def business_system_list(
    ctx: typer.Context,
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
) -> None:
    params = {"timePeriod": time_period}
    if end_time:
        params["endTime"] = end_time
    _call_path(ctx, command="business-system.list", path="/server-api/application/business/list", params=params)


@business_system_app.command("topology")
def business_system_topology(
    ctx: typer.Context,
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
) -> None:
    params = {"timePeriod": time_period}
    if end_time:
        params["endTime"] = end_time
    _call_path(ctx, command="business-system.topology", path="/server-api/graph/queryBizSystenGraph", params=params)


@application_app.command("list")
def application_list(
    ctx: typer.Context,
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
    lang: str = typer.Option("zh_CN", "--lang"),
) -> None:
    params = {"timePeriod": time_period, "lang": lang}
    if end_time:
        params["endTime"] = end_time
    _call_path(ctx, command="application.list", path="/server-api/graph/query/overview?application_overview", params=params)


@application_app.command("instances")
def application_instances(
    ctx: typer.Context,
    application_id: Optional[int] = typer.Option(None, "--application-id"),
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
) -> None:
    params: Dict[str, Any] = {"timePeriod": time_period}
    if application_id is not None:
        params["applicationId"] = application_id
    if end_time:
        params["endTime"] = end_time
    _call_path(
        ctx,
        command="application.instances",
        path="/server-api/graph/query/overview?application_overview_instance_list",
        params=params,
    )


@transaction_app.command("list")
def transaction_list(
    ctx: typer.Context,
    application_id: Optional[int] = typer.Option(None, "--application-id"),
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
) -> None:
    params: Dict[str, Any] = {"timePeriod": time_period}
    if application_id is not None:
        params["applicationId"] = application_id
    if end_time:
        params["endTime"] = end_time
    _call_path(ctx, command="transaction.list", path="/server-api/webaction/list/actionList", params=params)


@service_interface_app.command("list")
def service_interface_list(
    ctx: typer.Context,
    application_id: Optional[int] = typer.Option(None, "--application-id"),
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
) -> None:
    params: Dict[str, Any] = {"timePeriod": time_period}
    if application_id is not None:
        params["applicationId"] = application_id
    if end_time:
        params["endTime"] = end_time
    _call_path(ctx, command="service-interface.list", path="/server-api/webaction/list/interfaceList", params=params)


@background_task_app.command("list")
def background_task_list(
    ctx: typer.Context,
    application_id: Optional[int] = typer.Option(None, "--application-id"),
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
) -> None:
    params: Dict[str, Any] = {"timePeriod": time_period}
    if application_id is not None:
        params["applicationId"] = application_id
    if end_time:
        params["endTime"] = end_time
    _call_path(ctx, command="background-task.list", path="/server-api/webaction/list/backgroundList", params=params)


@component_app.command("database-list")
def component_database_list(ctx: typer.Context, application_id: Optional[int] = typer.Option(None, "--application-id")) -> None:
    params: Dict[str, Any] = {}
    if application_id is not None:
        params["applicationId"] = application_id
    _call_path(ctx, command="component.database-list", path="/server-api/Database/list", params=params)


@component_app.command("mq-list")
def component_mq_list(ctx: typer.Context, application_id: Optional[int] = typer.Option(None, "--application-id")) -> None:
    params: Dict[str, Any] = {}
    if application_id is not None:
        params["applicationId"] = application_id
    _call_path(ctx, command="component.mq-list", path="/server-api/MQ/MQApplication/list", params=params)


@error_app.command("list")
def error_list(
    ctx: typer.Context,
    application_id: Optional[int] = typer.Option(None, "--application-id"),
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
) -> None:
    params: Dict[str, Any] = {"timePeriod": time_period}
    if application_id is not None:
        params["applicationId"] = application_id
    if end_time:
        params["endTime"] = end_time
    _call_path(ctx, command="error.list", path="/server-api/errorList", params=params)


@trace_app.command("list")
def trace_list(
    ctx: typer.Context,
    application_id: Optional[int] = typer.Option(None, "--application-id"),
    end_time: Optional[str] = typer.Option(None, "--end-time"),
    time_period: int = typer.Option(60, "--time-period"),
) -> None:
    params: Dict[str, Any] = {"timePeriod": time_period}
    if application_id is not None:
        params["applicationId"] = application_id
    if end_time:
        params["endTime"] = end_time
    _call_path(ctx, command="trace.list", path="/server-api/action/trace", params=params)


@config_app.command("business-systems")
def config_business_systems(ctx: typer.Context) -> None:
    _call_path(ctx, command="config.business-systems", path="/server-config/data/business/queryBizSystemSelect", params={})


@config_app.command("applications")
def config_applications(ctx: typer.Context) -> None:
    _call_path(ctx, command="config.applications", path="/server-config/data/application/list", params={})


@health_rule_app.command("list")
def health_rule_list(ctx: typer.Context) -> None:
    _call_path(ctx, command="health-rule.list", path="/server-config/data/health/rule/pageList", params={})


@health_rule_app.command("detail")
def health_rule_detail(ctx: typer.Context, rule_id: int) -> None:
    _call_path(
        ctx,
        command="health-rule.detail",
        path="/server-config/data/health/rule/{ruleId}",
        params={"ruleId": rule_id},
    )


@health_rule_app.command("check")
def health_rule_check(ctx: typer.Context, health_id: int) -> None:
    _call_path(
        ctx,
        command="health-rule.check",
        path="/server-api/health/targets?healthId={healthId}",
        params={"healthId": health_id},
    )


app.add_typer(auth_app, name="auth")
app.add_typer(catalog_app, name="catalog")
app.add_typer(api_app, name="api")
app.add_typer(business_system_app, name="business-system")
app.add_typer(application_app, name="application")
app.add_typer(transaction_app, name="transaction")
app.add_typer(service_interface_app, name="service-interface")
app.add_typer(background_task_app, name="background-task")
app.add_typer(component_app, name="component")
app.add_typer(error_app, name="error")
app.add_typer(trace_app, name="trace")
app.add_typer(config_app, name="config")
app.add_typer(health_rule_app, name="health-rule")


if __name__ == "__main__":
    app()

