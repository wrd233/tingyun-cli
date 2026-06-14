from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from ty_apm_cli.catalog import Catalog


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "tingyun-apm-api.catalog.json"
SCHEMA_PATH = ROOT / "catalog" / "tingyun-apm-api.catalog.schema.json"


def test_catalog_matches_schema() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(catalog), key=lambda error: list(error.path))
    assert errors == []


def test_catalog_ids_are_unique_and_safety_is_consistent() -> None:
    catalog = Catalog(CATALOG_PATH)
    ids = [endpoint["id"] for endpoint in catalog.endpoints]
    assert len(ids) == len(set(ids))
    assert len(ids) == catalog.document["stats"]["endpoint_count"]
    assert catalog.document["stats"]["pdf_endpoint_candidates"] >= 250

    for endpoint in catalog.endpoints:
        if endpoint["safety"] == "read":
            assert endpoint["execution_supported"] is True
        else:
            assert endpoint["execution_supported"] is False


def test_catalog_safety_audit_passes() -> None:
    audit = Catalog(CATALOG_PATH).audit_safety()
    assert audit["ok"] is True
    assert audit["issue_count"] == 0


def test_catalog_coverage_report_exists() -> None:
    report = ROOT / "docs" / "catalog-coverage-report.md"
    text = report.read_text(encoding="utf-8")
    assert "Catalog Coverage Report" in text
    assert "Catalog endpoints including auth" in text

