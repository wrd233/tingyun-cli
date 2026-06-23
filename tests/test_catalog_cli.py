import json

from ty_apm_cli import cli
from ty_apm_cli.catalog import Catalog
from ty_apm_cli.cli import main
from ty_apm_cli.config import PROJECT_ROOT
from ty_apm_cli.envelope import success
from ty_apm_cli.http_client import CallRecord


def test_catalog_loads_and_audit_passes():
    catalog = Catalog(PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json")
    audit = catalog.audit_safety()
    assert len(catalog.entries) == 275
    assert audit["ok"] is True


def test_cli_catalog_list_emits_one_json_envelope(capsys):
    code = main(["catalog", "list"])
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert code == 0
    assert payload["schema_version"] == "ty-apm.envelope.v1"
    assert payload["ok"] is True
    assert payload["command"] == "catalog.list"


def test_no_raw_api_command_exists(capsys):
    code = main(["api", "raw", "--path", "/server-api/x"])
    payload = json.loads(capsys.readouterr().out)
    assert code != 0
    assert payload["ok"] is False
    assert payload["error"]["type"] == "ValidationError"


def test_api_call_unknown_catalog_id_is_json_failure(capsys):
    code = main(["api", "call", "missing.catalog.id"])
    payload = json.loads(capsys.readouterr().out)
    assert code != 0
    assert payload["ok"] is False
    assert payload["error"]["type"] == "CatalogNotFound"


def test_api_call_safety_blocked_is_json_failure(capsys):
    code = main(["api", "call", "business_system.2_2_2.data_business_updatetopologyshoworhidden"])
    payload = json.loads(capsys.readouterr().out)
    assert code != 0
    assert payload["ok"] is False
    assert payload["error"]["type"] == "SafetyBlocked"


def test_required_command_registration_smoke(capsys):
    commands = [
        ["catalog", "search", "应用"],
        ["catalog", "audit-safety"],
        ["api", "call", "missing.catalog.id"],
        ["snapshot", "collect", "--profile", "missing"],
        ["resolve", "application"],
    ]
    for args in commands:
        main(args)
        payload = json.loads(capsys.readouterr().out)
        assert payload["schema_version"] == "ty-apm.envelope.v1"
        assert "ok" in payload


def test_resolve_application_ambiguous_candidates(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def call(self, entry, params, command="resolve.application"):
            payload = {"code": 200, "data": [{"applicationId": 1, "applicationName": "app"}, {"applicationId": 2, "applicationName": "app"}]}
            return CallRecord(success(command, {"response": payload}), {}, payload, 1, 200, 200)

    monkeypatch.setattr(cli, "TingyunClient", FakeClient)
    code = main(["--base-url", "https://tingyun.example", "resolve", "application", "--name", "app"])
    payload = json.loads(capsys.readouterr().out)
    assert code != 0
    assert payload["error"]["type"] == "AmbiguousTarget"
