import json

from ty_apm_cli.catalog import Catalog
from ty_apm_cli.config import AppConfig, PROJECT_ROOT
from ty_apm_cli.envelope import success
from ty_apm_cli.http_client import CallRecord
from ty_apm_cli import snapshots


class FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    def call(self, entry, params, command="snapshot.collect"):
        env = success(command, {"catalog_id": entry["id"], "response": {"code": 200, "data": []}})
        return CallRecord(env, {"headers": {"Authorization": "***REDACTED***"}}, {"code": 200, "data": []}, 1, 200, 200)


def test_application_context_snapshot_package(monkeypatch, tmp_path):
    monkeypatch.setattr(snapshots, "TingyunClient", FakeClient)
    catalog = Catalog(PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json")
    cfg = AppConfig(base_url="https://tingyun.example", artifacts_dir=tmp_path)
    result = snapshots.collect_snapshot(
        profile="application-context",
        catalog=catalog,
        config=cfg,
        run_id="test_run",
        application_id="123",
    )
    root = tmp_path / "runs" / "test_run"
    assert result["run_id"] == "test_run"
    assert (root / "run.json").exists()
    assert (root / "logs" / "calls.jsonl").exists()
    assert (root / "snapshot" / "manifest.json").exists()
    assert (root / "snapshot" / "sections" / "identity.json").exists()
    coverage = json.loads((root / "snapshot" / "coverage.json").read_text())
    assert coverage["schema_version"] == "ty-apm.coverage.v1"
    assert {s["name"] for s in coverage["sections"]} == {"identity", "topology", "behavior_samples", "rules_and_config"}
