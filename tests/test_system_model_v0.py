import hashlib
import json
import shutil
from pathlib import Path

import pytest

from tingyun_cli.system_model import SystemModelError, compile_system_model, diff_system_models, validate_system_model
from tingyun_cli.cli import main
from tingyun_cli.manifest_schema import validate_schema


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures"
DATA_ROOT = FIXTURE_ROOT / "v1_1" / "offline_replay" / "data-root"
MODEL_FIXTURES = FIXTURE_ROOT / "system_model_v0"


def _json(path):
    return json.loads(Path(path).read_text())


def test_system_model_compile_is_deterministic_traceable_and_time_aware(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    result = compile_system_model(MODEL_FIXTURES / "manifest-a.json", data_root=DATA_ROOT, output_dir=first)
    repeated = compile_system_model(MODEL_FIXTURES / "manifest-a.json", data_root=DATA_ROOT, output_dir=second)

    assert result["status"] == repeated["status"] == "SUCCESS"
    assert result["actual_request_count"] == 0
    assert (first / "snapshot.json").read_bytes() == (second / "snapshot.json").read_bytes()
    assert hashlib.sha256((first / "snapshot.json").read_bytes()).hexdigest() == hashlib.sha256((second / "snapshot.json").read_bytes()).hexdigest()

    snapshot = _json(first / "snapshot.json")
    entities = {item["entity_id"]: item for item in snapshot["entities"]}
    relations = {item["relation_id"]: item for item in snapshot["relations"]}
    assert snapshot["schema_version"] == 1
    assert snapshot["model_version"] == "v0"
    assert snapshot["coverage"]["status"] == "PARTIAL"
    assert entities["business_system:biz-001"]["entity_type"] == "BUSINESS_SYSTEM"
    assert entities["application:biz-001:app-001"]["first_observed"] == "2026-01-01T10:00:00Z"
    assert entities["application:biz-001:app-001"]["last_observed"] == "2026-01-01T10:30:00Z"
    assert entities["application:biz-001:app-001"]["freshness"] == "CURRENT"
    assert entities["action:biz-001:app-001:action-001"]["observations"][0]["metrics"]["p99"]["value"] == 1500
    assert entities["trace:trace-correct"]["entity_type"] == "TRACE"
    assert entities["trace_node:run-call-tree-correct:node-http"]["canonical_identity"]["node_id"] == "node-http"
    assert relations["application:biz-001:app-001|OWNS|action:biz-001:app-001:action-001"]["time_semantics"] == "STABLE_OWNERSHIP_OBSERVATION"
    runtime_relation = relations["trace_node:run-call-tree-correct:node-root|CALLS|trace_node:run-call-tree-correct:node-http"]
    assert runtime_relation["time_semantics"] == "WINDOWED_RUNTIME_OBSERVATION"
    assert runtime_relation["evidence_refs"][0]["run_id"] == "run-call-tree-correct"
    assert runtime_relation["evidence_refs"][0]["artifact_path"] == "evidence/call_tree.json"
    assert runtime_relation["time_context"]["requested"]["value"] == "2026-01-01T10:00..2026-01-01T10:30"
    assert relations["trace:trace-correct|CONTAINS_NODE|trace_node:run-call-tree-correct:node-root"]["time_semantics"] == "WINDOWED_RUNTIME_OBSERVATION"
    assert snapshot["conflicts"] == []
    assert validate_system_model(first)["status"] == "PASS"


def test_system_model_validation_detects_tampering_and_missing_relation_endpoint(tmp_path):
    output = tmp_path / "compiled"
    compile_system_model(MODEL_FIXTURES / "manifest-a.json", data_root=DATA_ROOT, output_dir=output)
    snapshot = _json(output / "snapshot.json")
    snapshot["relations"][0]["to_entity_id"] = "missing:entity"
    (output / "snapshot.json").write_text(json.dumps(snapshot, sort_keys=True))

    result = validate_system_model(output)

    assert result["status"] == "FAIL"
    codes = {issue["code"] for issue in result["issues"]}
    assert "SNAPSHOT_HASH_MISMATCH" in codes
    assert "MISSING_RELATION_ENDPOINT" in codes


def test_system_model_diff_never_interprets_not_observed_as_deleted(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    compile_system_model(MODEL_FIXTURES / "manifest-a.json", data_root=DATA_ROOT, output_dir=first)
    compile_system_model(MODEL_FIXTURES / "manifest-b.json", data_root=DATA_ROOT, output_dir=second)

    result = diff_system_models(first / "snapshot.json", second / "snapshot.json")

    assert result["status"] == "SUCCESS"
    assert "entity:deleted" not in json.dumps(result)
    assert "business_system:biz-002" in result["entities"]["added"]
    assert "trace:trace-correct" in result["entities"]["not_observed"]
    assert result["entities"]["not_observed_interpretation"] == "NOT_OBSERVED_IN_AFTER_INPUTS"
    assert result["relations"]["not_observed_interpretation"] == "NOT_OBSERVED_IN_AFTER_INPUTS"


def test_system_model_diff_rejects_schema_valid_snapshot_with_broken_relation(tmp_path):
    compiled = tmp_path / "compiled"
    compile_system_model(MODEL_FIXTURES / "manifest-a.json", data_root=DATA_ROOT, output_dir=compiled)
    snapshot = _json(compiled / "snapshot.json")
    snapshot["relations"][0]["to_entity_id"] = "missing:entity"
    malformed = tmp_path / "malformed-snapshot.json"
    malformed.write_text(json.dumps(snapshot))

    with pytest.raises(SystemModelError) as exc_info:
        diff_system_models(malformed, malformed)

    assert exc_info.value.code == "INVALID_SYSTEM_MODEL_SNAPSHOT"
    assert "MISSING_RELATION_ENDPOINT" in str(exc_info.value)


def test_system_model_cli_surfaces_are_local_only_and_machine_readable(tmp_path, capsys):
    before = tmp_path / "before"
    after = tmp_path / "after"

    code = main(["--data-root", str(DATA_ROOT), "depth", "system-model-compile", "--manifest", str(MODEL_FIXTURES / "manifest-a.json"), "--output-dir", str(before)])
    compiled = json.loads(capsys.readouterr().out)
    assert code == 0
    assert compiled["status"] == "SUCCESS"
    assert compiled["actual_request_count"] == 0

    main(["--data-root", str(DATA_ROOT), "depth", "system-model-compile", "--manifest", str(MODEL_FIXTURES / "manifest-b.json"), "--output-dir", str(after)])
    capsys.readouterr()
    main(["depth", "system-model-validate", "--compiled-dir", str(before)])
    validated = json.loads(capsys.readouterr().out)
    assert validated["status"] == "PASS"
    assert validated["actual_request_count"] == 0

    main(["depth", "system-model-diff", "--before", str(before / "snapshot.json"), "--after", str(after / "snapshot.json")])
    diffed = json.loads(capsys.readouterr().out)
    assert diffed["status"] == "SUCCESS"
    assert diffed["entities"]["not_observed_interpretation"] == "NOT_OBSERVED_IN_AFTER_INPUTS"
    assert not (DATA_ROOT / ".inflight").exists()
    assert not (DATA_ROOT / "runs.jsonl").exists()


def test_system_model_missing_run_is_failed_not_silent_empty_or_partial(tmp_path):
    manifest = {
        "schema_version": 1,
        "snapshot_id": "missing-run-model",
        "as_of": "2026-01-01T11:00:00Z",
        "freshness_threshold_seconds": 3600,
        "run_refs": [{"run_id": "run-does-not-exist"}],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    result = compile_system_model(manifest_path, data_root=DATA_ROOT, output_dir=tmp_path / "compiled")

    assert result["status"] == "FAILED"
    validation = _json(tmp_path / "compiled" / "validation.json")
    assert validation["status"] == "FAIL"
    assert validation["issues"][0]["code"] == "MISSING_SOURCE_RUN"


def test_system_model_outputs_conform_to_committed_schemas(tmp_path):
    output = tmp_path / "compiled"
    compile_system_model(MODEL_FIXTURES / "manifest-a.json", data_root=DATA_ROOT, output_dir=output)
    snapshot = _json(output / "snapshot.json")
    validation = _json(output / "validation.json")
    diff = diff_system_models(output / "snapshot.json", output / "snapshot.json")

    for payload, schema_name in (
        (snapshot, "system-model-snapshot.schema.json"),
        (validation, "system-model-validation.schema.json"),
        (diff, "system-model-diff.schema.json"),
    ):
        schema = _json(ROOT / "schemas" / schema_name)
        assert validate_schema(payload, schema) == []


def test_system_model_rejects_output_inside_immutable_run_store(tmp_path):
    data_root = tmp_path / "data-root"
    shutil.copytree(DATA_ROOT, data_root)

    with pytest.raises(SystemModelError) as exc_info:
        compile_system_model(
            MODEL_FIXTURES / "manifest-a.json",
            data_root=data_root,
            output_dir=data_root / "runs" / "run-collect-a" / "derived-model",
        )

    assert exc_info.value.code == "OUTPUT_DIR_INSIDE_IMMUTABLE_RUN_STORE"
    assert not (data_root / "runs" / "run-collect-a" / "derived-model").exists()


def test_system_model_validation_and_diff_reject_malformed_non_snapshots(tmp_path):
    compiled = tmp_path / "compiled"
    compiled.mkdir()
    (compiled / "snapshot.json").write_text("{}")
    (compiled / "validation.json").write_text(json.dumps({
        "schema_version": 1,
        "kind": "system_model_validation",
        "status": "PASS",
        "snapshot_sha256": hashlib.sha256(b"{}").hexdigest(),
        "issues": [],
    }))

    validation = validate_system_model(compiled)
    assert validation["status"] == "FAIL"
    assert "SNAPSHOT_SCHEMA_VIOLATION" in {issue["code"] for issue in validation["issues"]}
    with pytest.raises(SystemModelError) as exc_info:
        diff_system_models(compiled / "snapshot.json", compiled / "snapshot.json")
    assert exc_info.value.code == "INVALID_SYSTEM_MODEL_SNAPSHOT"


def test_system_model_excludes_artifact_when_raw_evidence_is_missing(tmp_path):
    data_root = tmp_path / "data-root"
    shutil.copytree(DATA_ROOT, data_root)
    (data_root / "runs" / "run-source-external" / "raw" / "response-0001.json").unlink()

    result = compile_system_model(
        MODEL_FIXTURES / "manifest-a.json", data_root=data_root, output_dir=tmp_path / "compiled"
    )
    snapshot = _json(tmp_path / "compiled" / "snapshot.json")

    assert result["status"] == "FAILED"
    assert not [entity for entity in snapshot["entities"] if entity["entity_type"] == "EXTERNAL_SERVICE"]
    assert all(entity["verification_level"] == "RUNTIME_VALIDATED" for entity in snapshot["entities"])


@pytest.mark.parametrize("malformed", [[], None, "not-a-snapshot"])
def test_system_model_validation_returns_machine_failure_for_non_object_json(tmp_path, malformed):
    compiled = tmp_path / "compiled"
    compiled.mkdir()
    encoded = json.dumps(malformed).encode()
    (compiled / "snapshot.json").write_bytes(encoded)
    (compiled / "validation.json").write_text(json.dumps({
        "schema_version": 1,
        "kind": "system_model_validation",
        "status": "PASS",
        "snapshot_sha256": hashlib.sha256(encoded).hexdigest(),
        "issues": [],
    }))

    result = validate_system_model(compiled)

    assert result["status"] == "FAIL"
    assert "SNAPSHOT_SCHEMA_VIOLATION" in {issue["code"] for issue in result["issues"]}


@pytest.mark.parametrize("bad_refs", [[], [1]])
def test_system_model_validation_rejects_missing_or_malformed_evidence_refs(tmp_path, bad_refs):
    compiled = tmp_path / "compiled"
    compile_system_model(MODEL_FIXTURES / "manifest-a.json", data_root=DATA_ROOT, output_dir=compiled)
    snapshot = _json(compiled / "snapshot.json")
    snapshot["entities"][0]["evidence_refs"] = bad_refs
    encoded = (json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    (compiled / "snapshot.json").write_bytes(encoded)
    validation = _json(compiled / "validation.json")
    validation["snapshot_sha256"] = hashlib.sha256(encoded).hexdigest()
    (compiled / "validation.json").write_text(json.dumps(validation))

    result = validate_system_model(compiled)

    assert result["status"] == "FAIL"
    assert {issue["code"] for issue in result["issues"]} & {"MISSING_EVIDENCE_REFERENCE", "INVALID_EVIDENCE_REFERENCE", "SNAPSHOT_SCHEMA_VIOLATION"}


@pytest.mark.parametrize("status", ["BLOCKED", "SKIPPED"])
def test_system_model_preserves_non_request_artifact_status_without_requiring_raw(tmp_path, status):
    data_root = tmp_path / "data-root"
    run_id = f"run-{status.lower()}"
    run_root = data_root / "runs" / run_id
    (run_root / "evidence").mkdir(parents=True)
    artifact = {"schema_version": 1, "kind": "external_calls", "status": status, "data": {"items": []}}
    (run_root / "evidence" / "external_calls.json").write_text(json.dumps(artifact))
    (run_root / "manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "run_id": run_id,
        "run_type": "SOURCE",
        "overall": status,
        "artifacts": [{"kind": "external_calls", "path": "evidence/external_calls.json", "status": status}],
    }))
    manifest = {
        "schema_version": 1,
        "snapshot_id": f"model-{status.lower()}",
        "as_of": "2026-01-01T11:00:00Z",
        "freshness_threshold_seconds": 3600,
        "run_refs": [{"run_id": run_id}],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    result = compile_system_model(manifest_path, data_root=data_root, output_dir=tmp_path / "compiled")

    assert result["status"] == "SUCCESS"
    validation = _json(tmp_path / "compiled" / "validation.json")
    assert "MISSING_RAW_EVIDENCE" not in {issue["code"] for issue in validation["issues"]}
