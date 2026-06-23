import json

from ty_apm_cli.catalog import Catalog
from ty_apm_cli.cli import main
from ty_apm_cli.config import PROJECT_ROOT


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
