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


class FailingClient:
    def __init__(self, *args, **kwargs):
        pass

    def call(self, entry, params, command="snapshot.collect"):
        from ty_apm_cli.envelope import failure

        env = failure(command, "UpstreamError", "upstream business code was not success")
        return CallRecord(env, {"headers": {"Authorization": "***REDACTED***"}}, {"code": 500}, 1, 200, 500)


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
    assert coverage["schema_version"] == "ty-apm.snapshot.coverage.v1"
    assert coverage["catalog_ref"]["catalog_version"] == "v1"
    assert {s["name"] for s in coverage["sections"]} == {"identity", "topology", "behavior_samples", "rules_and_config"}
    manifest = json.loads((root / "snapshot" / "manifest.json").read_text())
    summary = json.loads((root / "snapshot" / "summary.json").read_text())
    section = json.loads((root / "snapshot" / "sections" / "identity.json").read_text())
    assert manifest["schema_version"] == "ty-apm.snapshot.manifest.v1"
    assert summary["schema_version"] == "ty-apm.snapshot.summary.v1"
    assert section["schema_version"] == "ty-apm.snapshot.section.v1"
    assert "scope" in manifest
    first_source = section["sources"][0]
    assert {"catalog_id", "call_id", "artifact_path", "item_count", "collected_at"} <= set(first_source)
    first_log = json.loads((root / "logs" / "calls.jsonl").read_text().splitlines()[0])
    assert first_log["schema_version"] == "ty-apm.call_log.v1"
    assert first_log["catalog_ref"]["catalog_version"] == "v1"


def test_all_snapshot_profiles_create_run_structure(monkeypatch, tmp_path):
    monkeypatch.setattr(snapshots, "TingyunClient", FakeClient)
    catalog = Catalog(PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json")
    cfg = AppConfig(base_url="https://tingyun.example", artifacts_dir=tmp_path)
    profiles = ["catalog-smoke", "inventory", "health-rules"]
    for profile in profiles:
        result = snapshots.collect_snapshot(profile=profile, catalog=catalog, config=cfg, run_id=profile)
        root = tmp_path / "runs" / profile
        assert result["run_id"] == profile
        assert (root / "run.json").exists()
        assert (root / "logs" / "calls.jsonl").exists()
        assert (root / "snapshot" / "manifest.json").exists()
        assert (root / "snapshot" / "coverage.json").exists()


def test_snapshot_coverage_records_failed_section(monkeypatch, tmp_path):
    monkeypatch.setattr(snapshots, "TingyunClient", FailingClient)
    catalog = Catalog(PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json")
    cfg = AppConfig(base_url="https://tingyun.example", artifacts_dir=tmp_path)
    snapshots.collect_snapshot(profile="catalog-smoke", catalog=catalog, config=cfg, run_id="failed")
    coverage = json.loads((tmp_path / "runs" / "failed" / "snapshot" / "coverage.json").read_text())
    assert coverage["sections"][0]["status"] == "failed"
    assert coverage["sections"][0]["gaps"][0]["type"] == "upstream_error"
