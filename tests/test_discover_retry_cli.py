import json
import os
from io import StringIO
from contextlib import redirect_stdout

from tingyun_cli.cli import main
from tingyun_cli.commands import run_collect, run_discover
from tingyun_cli.config import Config
from tingyun_cli.http import HttpExecutor
from tingyun_cli.storage import RunStore


class SequenceTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.recoveries = 0

    def send(self, request):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    def recover_auth(self):
        self.recoveries += 1
        return True


class FakeClock:
    def __init__(self):
        self.now = 1_783_430_000.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def test_discover_creates_discovery_run_with_real_candidate_items(tmp_path):
    store = RunStore(tmp_path)
    transport = SequenceTransport([{
        "status": 200,
        "data": [
            {"id": "biz-1", "name": "orders"},
            {"id": "biz-2", "name": "billing"},
        ],
    }])

    receipt = run_discover(
        store=store,
        config=Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0),
        query="bill",
        transport=transport,
        clock=FakeClock(),
    )

    run_path = tmp_path / "runs" / receipt["run_id"]
    targets = json.loads((run_path / "evidence" / "targets.json").read_text())
    assert receipt["status"] == "SUCCESS"
    assert [item["display_name"] for item in targets["data"]["items"]] == ["billing"]
    assert targets["data"]["items"][0]["wire_identity"] == {"bizSystemId": "biz-2"}
    assert "selected" not in targets["data"]["items"][0]
    assert transport.requests[0]["path"] == "/server-api/data/business/getBusinessTree"


def test_executor_retries_transient_failure_once_and_audits_both_attempts(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="collect", run_type="COLLECT")
    transport = SequenceTransport([TimeoutError("read timeout"), {"status": 200, "data": {}}])
    executor = HttpExecutor(
        store=store,
        run=run,
        config=Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0),
        transport=transport,
        clock=FakeClock(),
    )

    result = executor.execute({"method": "POST", "path": "/server-api/graph/query/overview", "body": {}, "body_kind": "json"})

    assert result.response["status"] == 200
    assert result.final_response_ref == "raw/response-0002.json"
    assert result.attempt_count == 2
    assert len(transport.requests) == 2
    assert (run.path / "raw" / "request-0001.json").exists()
    assert (run.path / "raw" / "error-0001.json").exists()
    assert (run.path / "raw" / "request-0002.json").exists()
    assert (run.path / "raw" / "response-0002.json").exists()


def test_executor_auth_recovery_replays_same_read_request_once(tmp_path):
    store = RunStore(tmp_path)
    run = store.begin_run(command="collect", run_type="COLLECT")
    transport = SequenceTransport([
        {"transport_status": 401, "status": 401, "message": "expired"},
        {"status": 200, "data": {"ok": True}},
    ])
    executor = HttpExecutor(
        store=store,
        run=run,
        config=Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0),
        transport=transport,
        clock=FakeClock(),
    )
    request = {"method": "POST", "path": "/server-api/graph/query/overview", "body": {"metric": "request_overview"}, "body_kind": "json"}

    result = executor.execute(request)

    assert result.response["status"] == 200
    assert result.final_response_ref == "raw/response-0002.json"
    assert result.auth_recovered is True
    assert transport.recoveries == 1
    assert transport.requests == [request, request]


def test_live_lock_conflict_creates_blocked_run_without_http(tmp_path):
    store = RunStore(tmp_path)
    (tmp_path / "live.lock").write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
    receipt = run_collect(
        store=store,
        config=Config(base_url="https://tingyun.example", data_root=tmp_path, min_request_interval_seconds=0),
        source_run_id="missing",
        source_item_ref="item-0001",
        time_context_value="last_30m",
        transport=SequenceTransport([{"status": 500}]),
    )

    assert receipt["status"] == "BLOCKED"
    assert receipt["reason_code"] == "LIVE_EXECUTION_BUSY"


def test_cli_live_command_stdout_is_only_receipt_for_blocked_run(tmp_path):
    out = StringIO()
    with redirect_stdout(out):
        code = main([
            "--data-root",
            str(tmp_path),
            "collect",
            "--source-run-id",
            "missing",
            "--source-item-ref",
            "item-0001",
            "--time-context",
            "last_30m",
        ])

    payload = json.loads(out.getvalue())
    assert code == 0
    assert payload["status"] == "BLOCKED"
    assert "evidence" not in payload
    assert "items" not in payload
