import json

from ty_apm_cli import cli
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


def test_catalog_smoke_uses_explicit_low_risk_ids_not_first_n():
    catalog = Catalog(PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json")
    first_three = [entry["id"] for entry in catalog.entries if entry["safety"] == "read" and entry["execution_supported"]][:3]
    smoke_ids = [step.catalog_id for step in snapshots.CATALOG_SMOKE_PROFILE]
    assert smoke_ids == [
        "application.3_1_1.application_app_list",
        "application.3_2_2.application_business_systemconflist",
        "config.12_1.data_business_querybizsystemselect",
    ]
    assert smoke_ids != first_three


def test_application_context_uses_explicit_section_mapping():
    sections = {step.section for step in snapshots.APPLICATION_CONTEXT_PROFILE}
    assert sections == {"identity", "topology", "behavior_samples", "rules_and_config"}
    assert all(step.catalog_id for step in snapshots.APPLICATION_CONTEXT_PROFILE)


def test_missing_required_params_are_marked_missing_not_guessed():
    catalog = Catalog(PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json")
    plan = snapshots.plan_snapshot(profile="health-rules", catalog=catalog)
    rule_list = next(step for step in plan["steps"] if step["catalog_id"] == "health_rule.14_1.data_health_rule_pagelist")
    assert rule_list["params"]["bizSystemId"] == {"value": None, "source": "missing"}
    assert rule_list["will_execute"] is False
    assert rule_list["skip_reason"] == "missing_required_param"


def test_plan_only_cli_uses_no_http_and_creates_no_artifacts(monkeypatch, tmp_path, capsys):
    class ExplodingClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("plan-only must not create an HTTP client")

    monkeypatch.setattr(snapshots, "TingyunClient", ExplodingClient)
    monkeypatch.setattr(cli, "TingyunClient", ExplodingClient)
    code = cli.main([
        "--artifacts-dir",
        str(tmp_path),
        "snapshot",
        "collect",
        "--profile",
        "application-context",
        "--application-id",
        "123",
        "--plan-only",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["mode"] == "plan_only"
    assert {step["section"] for step in payload["data"]["steps"]} == {"identity", "topology", "behavior_samples", "rules_and_config"}
    assert not (tmp_path / "runs").exists()


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


def test_snapshot_blocked_step_is_gap_without_http(monkeypatch, tmp_path):
    class CountingClient:
        calls = 0

        def __init__(self, *args, **kwargs):
            pass

        def call(self, entry, params, command="snapshot.collect"):
            CountingClient.calls += 1
            raise AssertionError("blocked steps must not execute HTTP")

    monkeypatch.setattr(snapshots, "TingyunClient", CountingClient)
    monkeypatch.setitem(
        snapshots.PROFILE_STEPS,
        "blocked-test",
        [snapshots.SectionStep("identity", "business_system.2_2_2.data_business_updatetopologyshoworhidden")],
    )
    catalog = Catalog(PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json")
    cfg = AppConfig(base_url="https://tingyun.example", artifacts_dir=tmp_path)
    snapshots.collect_snapshot(profile="blocked-test", catalog=catalog, config=cfg, run_id="blocked")
    coverage = json.loads((tmp_path / "runs" / "blocked" / "snapshot" / "coverage.json").read_text())
    assert CountingClient.calls == 0
    assert coverage["sections"][0]["status"] == "blocked"
    assert coverage["blocked_by_safety"][0]["catalog_id"] == "business_system.2_2_2.data_business_updatetopologyshoworhidden"
