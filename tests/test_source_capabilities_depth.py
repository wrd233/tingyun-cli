import json

import pytest

from tingyun_cli.config import Config
from tingyun_cli.commands import plan_collect, run_collect
from tingyun_cli.promotion import promotion_matrix
from tingyun_cli.safety import ADVANCED_SOURCE_READ_ENDPOINTS, assert_read_endpoint, assert_source_read_endpoint
from tingyun_cli.source_capabilities import (
    alarm_event_detail_request,
    alarm_metric_series_request,
    alarm_events_request,
    application_instances_request,
    external_uri_request,
    performance_timeseries_requests,
    recent_request_ranking_request,
    trace_exceptions_request,
)
from tingyun_cli.storage import RunStore


class FakeClock:
    def __init__(self):
        self.now = 1_783_430_000.0
        self.sleeps = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        return self.responses.pop(0)


def _config(tmp_path):
    return Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0)


def _write_discovery_run(store):
    run = store.begin_run(command="discover", run_type="DISCOVERY")
    store.write_json(run.path / "evidence" / "targets.json", {
        "schema_version": 1,
        "kind": "targets",
        "status": "SUCCESS",
        "data": {"items": [{
            "item_ref": "item-0001",
            "kind": "business_system_candidate",
            "display_name": "集团法务",
            "wire_identity": {"bizSystemId": "1061"},
        }]},
    })
    store.finalize_run(
        run,
        manifest={
            "schema_version": 1,
            "run_id": run.run_id,
            "run_type": "DISCOVERY",
            "overall": "SUCCESS",
            "artifacts": [{"kind": "targets", "path": "evidence/targets.json", "status": "SUCCESS"}],
            "coverage_ref": "coverage.json",
            "live_request_count": 1,
        },
        coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {"targets": {"status": "SUCCESS"}}},
    )
    return run.run_id


def test_promotion_matrix_separates_stable_experimental_and_research_only():
    matrix = promotion_matrix()

    assert matrix["read_error_timeseries"]["runtime_status"] == "ADVANCED_READ_ONLY"
    assert matrix["list_alarm_events"]["runtime_status"] == "ADVANCED_READ_ONLY"
    assert matrix["list_component_operations"]["runtime_status"] == "RESEARCH_ONLY"
    assert matrix["manage_alarm_rules"]["runtime_status"] == "REJECTED"
    assert matrix["overview.max"]["runtime_status"] == "RESEARCH_ONLY"


def test_source_request_builders_use_verified_read_endpoints_and_identity():
    time_context = {"endpoint": {"timePeriod": 10, "endTime": "2026-07-08 08:50"}}
    requests = [
        *performance_timeseries_requests("1061", time_context),
        alarm_events_request(time_context, page_number=1, page_size=20),
        alarm_event_detail_request("alarm-1", time_context),
        alarm_metric_series_request({
            "alarmEventId": 123,
            "metric": "response_time",
            "codeIndex": "avg",
            "policyId": 456,
            "policyCheckMode": 1,
            "product": "SERVER",
            "targetType": "ACTION",
            "eventItems": [{"eventTraceId": "event-trace-1"}],
        }, time_context),
        application_instances_request("1061", "1626", time_context),
        recent_request_ranking_request("1061", time_context, ranking="error"),
        external_uri_request("1061", "1626", time_context),
        trace_exceptions_request({
            "bizSystemId": "1061",
            "treeId": "tree-1",
            "traceId": "trace-1",
            "queryTimestamp": 1000,
        }, time_context),
    ]

    assert [request["endpoint_id"] for request in requests[:3]] == [
        "ep_post_server_api_application_charts_response",
        "ep_post_server_api_application_charts_error",
        "ep_post_server_api_application_charts_throught",
    ]
    assert requests[4]["path"] == "/nalarm-api/event/trace"
    assert requests[5]["path"] == "/nalarm-api/event/metric/chart"
    assert requests[6]["path"] == "/server-api/graph/information"
    assert requests[7]["path"] == "/server-api/webaction/list/errorList"
    assert requests[9]["body"] == {"treeId": "tree-1", "traceId": "trace-1", "bizSystemId": "1061", "queryTimestamp": 1000, "timePeriod": "10", "endTime": "2026-07-08 08:50", "lang": "zh_CN"}
    assert_read_endpoint(requests[0]["method"], requests[0]["path"])
    for request in requests[1:]:
        assert request["runtime_surface"] == "ADVANCED_SOURCE"
        assert_source_read_endpoint(request["method"], request["path"])
    assert {(request["method"], request["path"]) for request in requests[1:]} <= ADVANCED_SOURCE_READ_ENDPOINTS


def test_collect_plan_and_run_stay_three_requests_while_deeper_series_are_optional_sources(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)

    plan = plan_collect(store, source_run_id, "item-0001", "last_30m")

    assert plan["expected_logical_request_count"] == 3
    assert plan["planned_steps"] == ["identity", "topology", "performance", "candidates"]

    transport = FakeTransport([
        {"status": 200, "data": {"nodes": [{"id": "app-1"}], "edges": []}},
        {"status": 200, "data": {"avg": [10], "p50": [8], "p80": [12], "p95": [20], "p99": [30]}},
        {"status": 200, "data": [{
            "applicationId": 1626,
            "actionId": 13172,
            "actionName": "findRelation",
            "applicationName": "app",
            "requestType": "WEB",
            "responseTimeMillisecondAvg": 100,
            "errorRate": 0.2,
        }]},
    ])

    receipt = run_collect(
        store=store,
        config=_config(tmp_path),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    manifest = json.loads((run_path / "manifest.json").read_text())
    assert manifest["live_request_count"] == 3
    assert [request["path"] for request in transport.requests] == [
        "/server-api/graph/queryBizDetailGraph",
        "/server-api/application/charts/response",
        "/server-api/graph/query/overview",
    ]
    optional_paths = [request["path"] for request in performance_timeseries_requests("1061", {"endpoint": {"timePeriod": 30, "endTime": "2026-07-08 08:50"}})[1:]]
    assert optional_paths == ["/server-api/application/charts/error", "/server-api/application/charts/throught"]
