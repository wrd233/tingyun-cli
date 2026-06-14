from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ty_apm_cli.cli import app


runner = CliRunner()


def parse_output(result) -> dict:
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_catalog_list_cli_outputs_json() -> None:
    result = runner.invoke(app, ["catalog", "list"])
    payload = parse_output(result)
    assert payload["ok"] is True
    assert payload["command"] == "catalog.list"
    assert payload["data"]["stats"]["endpoint_count"] >= 250


def test_api_call_rejects_non_read_cli(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--output-dir",
            str(tmp_path),
            "api",
            "call",
            "business_system.2_2_5.graph_savetopolayout",
            "--param",
            "key=layout",
        ],
    )
    payload = parse_output(result)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "UnsupportedSafetyLevel"


def test_typed_command_uses_json_envelope(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--output-dir", str(tmp_path), "business-system", "list", "--time-period", "60"],
    )
    payload = parse_output(result)
    assert payload["ok"] is False
    assert payload["command"] == "business-system.list"
    assert payload["error"]["type"] == "MissingConfig"
