import json

import pytest

from tingyun_cli.commands import export_sanitized_run, run_collect
from tingyun_cli.config import Config
from tingyun_cli.safety import assert_read_endpoint
from tingyun_cli.storage import RunStore


class NoopTransport:
    def send(self, request):
        raise AssertionError("HTTP must not be called")


def test_unknown_or_write_endpoint_is_blocked():
    with pytest.raises(ValueError, match="not in stable read surface"):
        assert_read_endpoint("POST", "/server-api/data/business/updateBizSystemSetting")

    with pytest.raises(ValueError, match="not in stable read surface"):
        assert_read_endpoint("GET", "/server-api/unknown")

    assert_read_endpoint("POST", "/server-api/graph/query/overview")


def test_invalid_collect_source_creates_blocked_run_with_zero_live_requests(tmp_path):
    store = RunStore(tmp_path)
    receipt = run_collect(
        store=store,
        config=Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0),
        source_run_id="missing-run",
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=NoopTransport(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    manifest = json.loads((run_path / "manifest.json").read_text())
    assert receipt["status"] == "BLOCKED"
    assert receipt["reason_code"] == "INVALID_SOURCE_REF"
    assert manifest["live_request_count"] == 0
    assert not (run_path / "evidence").exists()


def test_stale_inflight_is_frozen_as_interrupted(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="collect", run_type="COLLECT", pid=99999999)
    store.write_json(run.path / "raw" / "request-0001.json", {"authorization": "Bearer should-not-appear"})

    interrupted = store.freeze_stale_inflight()

    assert interrupted == [run.run_id]
    manifest = json.loads((tmp_path / "runs" / run.run_id / "manifest.json").read_text())
    assert manifest["overall"] == "INTERRUPTED"
    assert manifest["live_request_count"] == 1
    assert manifest["raw_summary"]["request_count"] == 1


def test_sanitized_export_removes_secrets_paths_ids_and_actions(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="investigate", run_type="INVESTIGATION")
    store.write_json(run.path / "manifest.json", {
        "schema_version": 1,
        "run_id": run.run_id,
        "overall": "SUCCESS",
        "local_path": str(tmp_path / "secret-path"),
    })
    store.write_json(run.path / "evidence" / "trace.json", {
        "data": {
            "items": [{
                "item_ref": "item-0001",
                "wire_identity": {"actionId": 123, "traceId": "trace-1"},
                "available_actions": ["inspect_call_tree"],
                "headers": {"Authorization": "Bearer secret", "Cookie": "x=y"},
            }]
        }
    })
    store.finalize_existing_inflight(run)

    output_dir = tmp_path / "exports" / "safe"
    result = export_sanitized_run(store, run.run_id, output_dir)
    text = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.rglob("*.json"))

    assert result["status"] == "SUCCESS"
    assert "Bearer" not in text
    assert "Cookie" not in text
    assert "actionId" not in text
    assert "trace-1" not in text
    assert "available_actions" not in text
    assert str(tmp_path) not in text
    index_entries = [
        json.loads(line)
        for line in (tmp_path / "runs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert all(entry["command"] != "sanitized_export" for entry in index_entries)
