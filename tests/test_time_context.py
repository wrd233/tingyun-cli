import json

from tingyun_cli.commands import plan_collect, run_collect
from tingyun_cli.config import Config
from tingyun_cli.storage import RunStore
from tingyun_cli.time_context import resolve_time_context


class NoopTransport:
    def send(self, request):
        raise AssertionError("HTTP must not be called for blocked time shape")


def _write_discovery_run(store):
    run = store.begin_run(command="discover", run_type="DISCOVERY")
    store.write_json(run.path / "evidence" / "targets.json", {
        "schema_version": 1,
        "kind": "targets",
        "status": "SUCCESS",
        "data": {
            "items": [{
                "item_ref": "item-0001",
                "kind": "business_system_candidate",
                "display_name": "target",
                "wire_identity": {"bizSystemId": "biz-1"},
            }]
        },
    })
    store.finalize_run(
        run,
        manifest={"schema_version": 1, "run_id": run.run_id, "run_type": "DISCOVERY", "overall": "SUCCESS", "artifacts": [], "coverage_ref": "coverage.json", "live_request_count": 1},
        coverage={"schema_version": 1, "overall": "SUCCESS", "artifacts": {}},
    )
    return run.run_id


def test_exact_historical_time_range_maps_to_endpoint_minutes():
    context = resolve_time_context("2026-07-06T13:00..2026-07-06T13:30")

    assert context["requested"]["kind"] == "exact_range"
    assert context["endpoint"] == {"timePeriod": 30, "endTime": "2026-07-06 13:30"}


def test_unsupported_time_shape_blocks_with_zero_live_requests(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)

    receipt = run_collect(
        store=store,
        config=Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0),
        source_run_id=source_run_id,
        source_item_ref="item-0001",
        time_context_value="2026-07-06T13:00..2026-07-06T13:37:30",
        transport=NoopTransport(),
    )

    manifest = json.loads((tmp_path / "runs" / receipt["run_id"] / "manifest.json").read_text())
    assert receipt["status"] == "BLOCKED"
    assert receipt["reason_code"] == "UNSUPPORTED_TIME_SHAPE"
    assert manifest["live_request_count"] == 0


def test_plan_collect_supports_exact_time_without_writes(tmp_path):
    store = RunStore(tmp_path)
    source_run_id = _write_discovery_run(store)
    before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))

    plan = plan_collect(store, source_run_id, "item-0001", "2026-07-06T13:00..2026-07-06T14:00")

    after = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    assert before == after
    assert plan["status"] == "READY"
    assert plan["time_context"]["endpoint"] == {"timePeriod": 60, "endTime": "2026-07-06 14:00"}
