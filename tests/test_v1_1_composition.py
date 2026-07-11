import hashlib
import json
import shutil
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from tingyun_cli.cli import main
from tingyun_cli.evidence_composition import CompositionError, compile_evidence
from tingyun_cli.evidence_extraction import extract_call_tree
from tingyun_cli.evidence_validation import validate_compiled_dir


FIXTURE = Path(__file__).parent / "fixtures" / "v1_1" / "offline_replay"
SCHEMA = Path(__file__).parents[1] / "schemas" / "investigation-manifest.schema.json"


def _replay(tmp_path):
    data_root = tmp_path / "data-root"
    shutil.copytree(FIXTURE / "data-root", data_root)
    manifest = tmp_path / "investigation-manifest.json"
    shutil.copy2(FIXTURE / "investigation-manifest.json", manifest)
    return data_root, manifest


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_tree(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_offline_replay_compiles_exact_lineage_and_preserves_deep_evidence(tmp_path):
    data_root, manifest = _replay(tmp_path)
    output = tmp_path / "compiled"

    result = compile_evidence(manifest, data_root=data_root, output_dir=output)

    assert result["status"] == "SUCCESS"
    validation = _json(output / "validation.json")
    assert not [issue for issue in validation["issues"] if issue["severity"] == "ERROR"]
    assert any(issue["code"] == "WRONG_TARGET_TRACE_REJECTED" for issue in validation["issues"])
    source_of_truth = _json(output / "source-of-truth.json")
    assert source_of_truth["counts"] == {
        "alarm_seed_count": 4,
        "incident_count": 3,
        "window_count": 3,
        "collect_run_count": 3,
        "trace_run_count": 2,
        "target_correct_trace_count": 1,
        "call_tree_run_count": 1,
        "target_correct_call_tree_count": 1,
        "source_run_count": 1,
    }
    evidence_map = _json(output / "evidence-map.json")
    incident = next(item for item in evidence_map["incidents"] if item["incident_id"] == "incident-001")
    assert [item["trace_run_id"] for item in incident["trace_runs"]] == ["run-trace-correct"]
    assert [item["call_tree_run_id"] for item in incident["call_tree_runs"]] == ["run-call-tree-correct"]
    assert incident["links"][0]["url"] == "/verified/synthetic/action-001"
    candidate = _json(output / "extractions" / "candidates" / "candidate-binding-001.json")
    assert candidate["metrics"]["p95"]["value"] == 900
    call_tree = _json(output / "extractions" / "call-trees" / "run-call-tree-correct.json")
    sql_vendors = {span.get("vendor") for span in call_tree["database_spans"] if span.get("sql", "").startswith("select synthetic")}
    assert sql_vendors >= {"PostgreSQL", "Oracle"}
    assert any(span["total_time"] == 129397 for span in call_tree["http_spans"])
    assert {span["node_id"] for span in call_tree["all_spans"]} >= {"node-root", "node-rpc", "node-db", "node-sql", "node-oracle-sql", "node-http"}
    assert _json(output / "report-readiness.json")["incidents"][0]["deep"]["status"] == "READY"
    assert validate_compiled_dir(output)["status"] == "PASS"


def test_trace_artifact_item_lineage_is_verified_independently_of_run_manifest(tmp_path):
    data_root, manifest = _replay(tmp_path)
    trace_path = data_root / "runs" / "run-trace-correct" / "evidence" / "trace.json"
    trace = _json(trace_path)
    trace["data"]["items"][0]["source_item_ref"] = "item-wrong"
    trace_path.write_text(json.dumps(trace), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-wrong-artifact-lineage")

    evidence_map = _json(tmp_path / "compiled-wrong-artifact-lineage" / "evidence-map.json")
    incident = next(item for item in evidence_map["incidents"] if item["incident_id"] == "incident-001")
    assert incident["trace_runs"] == []
    assert any(item["trace_run_id"] == "run-trace-correct" and item["status"] == "REJECTED_WRONG_TARGET" for item in evidence_map["rejected_trace_runs"])
    assert any(issue["code"] == "WRONG_TARGET_TRACE_REJECTED" for issue in result["validation"]["issues"])


@pytest.mark.parametrize(("run_id", "kind"), [("run-trace-correct", "trace"), ("run-call-tree-correct", "call_tree")])
@pytest.mark.parametrize("artifact_status", ["FAILED", "EMPTY"])
def test_failed_or_empty_trace_and_call_tree_artifacts_never_become_evidence(tmp_path, run_id, kind, artifact_status):
    data_root, manifest = _replay(tmp_path)
    artifact_path = data_root / "runs" / run_id / "evidence" / f"{kind}.json"
    artifact = _json(artifact_path)
    artifact["status"] = artifact_status
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / f"compiled-{run_id}-{artifact_status.lower()}")

    assert result["status"] == "FAILED"
    assert any(issue["code"] == "UNUSABLE_ARTIFACT" and issue["severity"] == "ERROR" for issue in result["validation"]["issues"])
    evidence_map = _json(tmp_path / f"compiled-{run_id}-{artifact_status.lower()}" / "evidence-map.json")
    incident = next(item for item in evidence_map["incidents"] if item["incident_id"] == "incident-001")
    field = "trace_runs" if kind == "trace" else "call_tree_runs"
    assert incident[field] == []


@pytest.mark.parametrize(("run_id", "kind"), [("run-trace-correct", "trace"), ("run-call-tree-correct", "call_tree")])
def test_manifest_and_artifact_status_must_agree_before_evidence_is_accepted(tmp_path, run_id, kind):
    data_root, manifest = _replay(tmp_path)
    run_manifest_path = data_root / "runs" / run_id / "manifest.json"
    run_manifest = _json(run_manifest_path)
    run_manifest["artifacts"][0]["status"] = "FAILED"
    run_manifest_path.write_text(json.dumps(run_manifest), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / f"compiled-status-mismatch-{kind}")

    assert result["status"] == "FAILED"
    assert any(issue["code"] == "ARTIFACT_STATUS_MISMATCH" for issue in result["validation"]["issues"])
    evidence_map = _json(tmp_path / f"compiled-status-mismatch-{kind}" / "evidence-map.json")
    incident = next(item for item in evidence_map["incidents"] if item["incident_id"] == "incident-001")
    assert incident["trace_runs" if kind == "trace" else "call_tree_runs"] == []


def test_cross_window_binding_fails_with_exact_code_and_never_substitutes_same_name(tmp_path):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    payload["candidate_bindings"][0]["collect_run_id"] = "run-collect-b"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-invalid-window")

    assert result["status"] == "FAILED"
    issues = _json(tmp_path / "compiled-invalid-window" / "validation.json")["issues"]
    assert any(issue["code"] == "CROSS_WINDOW_EVIDENCE_REJECTED" and issue["severity"] == "ERROR" for issue in issues)
    evidence_map = _json(tmp_path / "compiled-invalid-window" / "evidence-map.json")
    incident = next(item for item in evidence_map["incidents"] if item["incident_id"] == "incident-001")
    assert incident["candidate_bindings"] == []


def test_noncanonical_incident_id_is_a_hard_failure(tmp_path):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    payload["source_bindings"][0]["incident_id"] = "incident-drifted"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-invalid-incident")

    assert result["status"] == "FAILED"
    issues = _json(tmp_path / "compiled-invalid-incident" / "validation.json")["issues"]
    assert any(issue["code"] == "NONCANONICAL_INCIDENT_ID" for issue in issues)


def test_missing_collect_run_cannot_report_successful_context_coverage(tmp_path):
    data_root, manifest = _replay(tmp_path)
    shutil.rmtree(data_root / "runs" / "run-collect-c")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-missing-context")

    assert result["status"] == "FAILED"
    coverage = _json(tmp_path / "compiled-missing-context" / "coverage.json")
    incident = next(item for item in coverage["incidents"] if item["incident_id"] == "incident-003")
    assert incident["context"]["status"] == "REJECTED"


@pytest.mark.parametrize(
    ("registry", "field", "value"),
    [
        ("candidate_bindings", "incident_id", "incident-002"),
        ("trace_bindings", "incident_id", "incident-002"),
        ("call_tree_bindings", "incident_id", "incident-002"),
    ],
)
def test_binding_incident_must_match_its_parent_lineage(tmp_path, registry, field, value):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    payload[registry][0][field] = value
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / f"compiled-{registry}")

    assert result["status"] == "FAILED"
    issues = _json(tmp_path / f"compiled-{registry}" / "validation.json")["issues"]
    assert any(issue["code"] == "NONCANONICAL_INCIDENT_ID" and issue["severity"] == "ERROR" for issue in issues)


def test_source_role_must_match_the_bound_run_artifact_kind(tmp_path):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    payload["source_bindings"][0]["role"] = "application_instances"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-source-kind")

    assert result["status"] == "FAILED"
    issues = _json(tmp_path / "compiled-source-kind" / "validation.json")["issues"]
    assert any(issue["code"] == "NONCANONICAL_SOURCE_BINDING" and issue["severity"] == "ERROR" for issue in issues)


def test_bound_recent_timeseries_and_topology_sources_route_to_exact_extractions(tmp_path):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    cases = [
        ("run-source-recent", "recent_requests", "recent_requests_error", "recent-requests", {"ranking": "error"}),
        ("run-source-series", "performance_error_series", "performance_error_series", "timeseries", {}),
        ("run-source-instances", "instance_context", "application_instances", "topology", {}),
    ]
    for run_id, kind, role, _directory, source in cases:
        run_path = data_root / "runs" / run_id
        (run_path / "evidence").mkdir(parents=True)
        (run_path / "raw").mkdir()
        (run_path / "raw" / "response-0001.json").write_text(json.dumps({"response": {"status": 200, "data": "synthetic"}}), encoding="utf-8")
        artifact = {"schema_version": 1, "kind": kind, "status": "SUCCESS", "derived_from": ["raw/response-0001.json"], "data": {"items": [{"item_ref": "item-0001", "source_run_id": run_id, "source_refs": ["raw/response-0001.json"]}]}}
        if source:
            artifact["source"] = source
        (run_path / "evidence" / f"{kind}.json").write_text(json.dumps(artifact), encoding="utf-8")
        (run_path / "manifest.json").write_text(json.dumps({"schema_version": 1, "run_id": run_id, "run_type": "SOURCE", "overall": "SUCCESS", "artifacts": [{"kind": kind, "path": f"evidence/{kind}.json", "status": "SUCCESS"}], "live_request_count": 1}), encoding="utf-8")
        payload["source_bindings"].append({"incident_id": "incident-001", "source_run_id": run_id, "role": role})
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-source-routes")

    assert result["status"] == "SUCCESS"
    for run_id, _kind, role, directory, _source in cases:
        extraction = _json(tmp_path / "compiled-source-routes" / "extractions" / directory / f"{run_id}.json")
        assert extraction["role"] == role


def test_verified_navigation_claim_without_verified_link_is_a_hard_failure(tmp_path):
    data_root, manifest = _replay(tmp_path)
    candidate_path = data_root / "runs" / "run-collect-a" / "evidence" / "candidates.json"
    candidate = _json(candidate_path)
    candidate["data"]["items"][0]["links"][0]["verification"] = "GUESSED"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-url-failure")

    assert result["status"] == "FAILED"
    assert any(issue["code"] == "URL_PROPAGATION_FAILURE" for issue in result["validation"]["issues"])


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda root: shutil.rmtree(root / "runs" / "run-collect-a"), "MISSING_RUN"),
        (lambda root: (root / "runs" / "run-collect-a" / "evidence" / "candidates.json").unlink(), "MISSING_ARTIFACT"),
        (lambda root: (root / "runs" / "run-collect-a" / "raw" / "response-0003.json").unlink(), "MISSING_RAW_REF"),
    ],
)
def test_missing_run_artifact_and_raw_ref_are_explicit_failures(tmp_path, mutation, expected_code):
    data_root, manifest = _replay(tmp_path)
    mutation(data_root)

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / f"compiled-{expected_code.lower()}")

    assert result["status"] == "FAILED"
    assert any(issue["code"] == expected_code and issue["severity"] == "ERROR" for issue in result["validation"]["issues"])


@pytest.mark.parametrize("attack", ["run_id", "artifact_path", "raw_ref"])
def test_compiler_rejects_path_escape_from_untrusted_manifest_or_run_metadata(tmp_path, attack):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    if attack == "run_id":
        payload["windows"][0]["collect_run_id"] = "../../outside"
        payload["candidate_bindings"][0]["collect_run_id"] = "../../outside"
    elif attack == "artifact_path":
        run_manifest_path = data_root / "runs" / "run-collect-a" / "manifest.json"
        run_manifest = _json(run_manifest_path)
        run_manifest["artifacts"][0]["path"] = "../../../../outside.json"
        run_manifest_path.write_text(json.dumps(run_manifest), encoding="utf-8")
    else:
        candidate_path = data_root / "runs" / "run-collect-a" / "evidence" / "candidates.json"
        candidate = _json(candidate_path)
        candidate["derived_from"] = ["raw/../../../../outside.json"]
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / f"compiled-unsafe-{attack}")

    assert result["status"] == "FAILED"
    assert any(issue["code"] == "UNSAFE_PATH_REF" and issue["severity"] == "ERROR" for issue in result["validation"]["issues"])


def test_every_target_correct_call_tree_is_retained_in_the_evidence_map(tmp_path):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    source = data_root / "runs" / "run-call-tree-correct"
    replacement = data_root / "runs" / "run-call-tree-correct-2"
    shutil.copytree(source, replacement)
    run_manifest = _json(replacement / "manifest.json")
    run_manifest["run_id"] = "run-call-tree-correct-2"
    (replacement / "manifest.json").write_text(json.dumps(run_manifest), encoding="utf-8")
    payload["call_tree_bindings"].append({"incident_id": "incident-001", "trace_run_id": "run-trace-correct", "call_tree_run_id": "run-call-tree-correct-2"})
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-two-trees")

    assert result["status"] == "SUCCESS"
    evidence_map = _json(tmp_path / "compiled-two-trees" / "evidence-map.json")
    incident = next(item for item in evidence_map["incidents"] if item["incident_id"] == "incident-001")
    assert [item["call_tree_run_id"] for item in incident["call_tree_runs"]] == ["run-call-tree-correct", "run-call-tree-correct-2"]


def test_compilation_is_byte_stable_for_identical_manifest_and_runs(tmp_path):
    data_root, manifest = _replay(tmp_path)
    first = tmp_path / "compiled-1"
    second = tmp_path / "compiled-2"

    compile_evidence(manifest, data_root=data_root, output_dir=first)
    compile_evidence(manifest, data_root=data_root, output_dir=second)

    assert _sha_tree(first) == _sha_tree(second)


def test_nonempty_output_dir_is_blocked_without_overwrite(tmp_path):
    data_root, manifest = _replay(tmp_path)
    output = tmp_path / "compiled"
    output.mkdir()
    marker = output / "user-file.txt"
    marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(CompositionError) as error:
        compile_evidence(manifest, data_root=data_root, output_dir=output)

    assert error.value.code == "OUTPUT_DIR_NOT_EMPTY"
    assert marker.read_text(encoding="utf-8") == "preserve"


def test_validator_detects_tampered_compiled_output(tmp_path):
    data_root, manifest = _replay(tmp_path)
    output = tmp_path / "compiled"
    compile_evidence(manifest, data_root=data_root, output_dir=output)
    evidence_map = _json(output / "evidence-map.json")
    evidence_map["incidents"] = []
    (output / "evidence-map.json").write_text(json.dumps(evidence_map), encoding="utf-8")

    result = validate_compiled_dir(output)

    assert result["status"] == "FAIL"
    assert any(issue["code"] == "COMPILED_HASH_MISMATCH" for issue in result["issues"])


def test_validator_rejects_a_tampered_file_hidden_by_removing_its_hash_entry(tmp_path):
    data_root, manifest = _replay(tmp_path)
    output = tmp_path / "compiled"
    compile_evidence(manifest, data_root=data_root, output_dir=output)
    validation = _json(output / "validation.json")
    validation["compiled_hashes"].pop("evidence-map.json")
    (output / "validation.json").write_text(json.dumps(validation), encoding="utf-8")
    evidence_map = _json(output / "evidence-map.json")
    evidence_map["tampered"] = True
    (output / "evidence-map.json").write_text(json.dumps(evidence_map), encoding="utf-8")

    result = validate_compiled_dir(output)

    assert result["status"] == "FAIL"
    assert any(issue["code"] == "COMPILED_HASH_SET_MISMATCH" for issue in result["issues"])


def test_compile_and_validate_cli_are_local_only_and_do_not_mutate_data_root(tmp_path):
    data_root, manifest = _replay(tmp_path)
    before = _sha_tree(data_root)
    output = tmp_path / "compiled"

    stdout = StringIO()
    with redirect_stdout(stdout):
        compile_code = main(["--data-root", str(data_root), "depth", "evidence-compile", "--manifest", str(manifest), "--output-dir", str(output)])
    compile_payload = json.loads(stdout.getvalue())
    stdout = StringIO()
    with redirect_stdout(stdout):
        validate_code = main(["--data-root", str(data_root), "depth", "evidence-validate", "--compiled-dir", str(output)])
    validate_payload = json.loads(stdout.getvalue())

    assert compile_code == validate_code == 0
    assert compile_payload["status"] == "SUCCESS"
    assert validate_payload["status"] == "PASS"
    assert _sha_tree(data_root) == before
    assert not (data_root / ".inflight").exists()
    assert not (data_root / "runs.jsonl").exists()


def test_call_tree_extraction_uses_exclusive_ranking_and_marks_total_time_fallback():
    call_tree = _json(Path(__file__).parent / "fixtures" / "v1_1" / "deep_call_tree" / "call_tree.json")
    call_tree["nodeMap"]["node-db"].pop("exclTime")

    extraction = extract_call_tree(call_tree, evidence_ref="run-call-tree/evidence/call_tree.json")

    fallback = next(span for span in extraction["all_spans"] if span["node_id"] == "node-db")
    assert fallback["overlap_warning"] is True
    assert extraction["top_exclusive_leaf_spans"][0]["node_id"] == "node-http"
    assert all(span["evidence_ref"] == "run-call-tree/evidence/call_tree.json" for span in extraction["all_spans"])


def test_investigation_manifest_has_a_formal_finite_schema():
    schema = _json(SCHEMA)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == 1
    assert set(schema["properties"]["incidents"]["items"]["properties"]["kind"]["enum"]) == {
        "TEMPORAL_INCIDENT", "CALL_CHAIN_INCIDENT", "SERVICE_FAMILY_CLUSTER",
        "RECURRING_ALARM_CLUSTER", "INSTANCE_CLUSTER", "OTHER",
    }
    assert set(schema["properties"]["source_bindings"]["items"]["properties"]["role"]["enum"]) >= {
        "external_calls", "recent_requests_response", "application_instances", "other",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.update({"forbidden_property": True}),
        lambda payload: payload["alarm_seeds"][0].update({"occurred_at": 123}),
        lambda payload: payload["source_bindings"][0].update({"role": "not_in_schema"}),
    ],
)
def test_committed_manifest_schema_is_enforced_at_runtime(tmp_path, mutation):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    mutation(payload)
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-schema-invalid")

    assert result["status"] == "FAILED"
    assert any(issue["code"] == "INVALID_INVESTIGATION_MANIFEST" and issue["context"].get("validator") == "draft_2020_12_subset" for issue in result["validation"]["issues"])


def test_report_readiness_models_every_required_evidence_class_from_accepted_evidence(tmp_path):
    data_root, manifest = _replay(tmp_path)

    compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-readiness")

    readiness = _json(tmp_path / "compiled-readiness" / "report-readiness.json")
    rich = next(item for item in readiness["incidents"] if item["incident_id"] == "incident-001")
    sparse = next(item for item in readiness["incidents"] if item["incident_id"] == "incident-003")
    assert set(rich["simple"]["requirements"]) >= {"alarm_inventory", "alarm_distribution", "important_incident", "candidate_metrics", "key_trace", "important_upstream_downstream", "verified_url", "evidence_gap_accounting"}
    assert set(rich["deep"]["requirements"]) >= {"alarm_seed", "historical_context", "candidate_aggregate", "trace_sample", "sample_assessment", "call_tree", "deep_spans", "sql_or_external", "counter_signals", "unknowns", "evidence_chain"}
    assert rich["simple"]["status"] == "READY"
    assert rich["deep"]["status"] == "READY"
    assert sparse["simple"]["requirements"]["important_upstream_downstream"] is False
    assert sparse["simple"]["requirements"]["verified_url"] is False
    assert sparse["deep"]["requirements"]["evidence_chain"] is False
    assert sparse["simple"]["status"] == "PARTIAL"
    assert sparse["deep"]["status"] == "PARTIAL"


@pytest.mark.parametrize(
    ("registry", "mutation"),
    [
        ("call_tree_bindings", lambda row: row.pop("trace_run_id")),
        ("source_bindings", lambda row: row.update({"role": "guessed_role"})),
    ],
)
def test_manifest_validation_covers_call_tree_and_source_binding_schema(tmp_path, registry, mutation):
    data_root, manifest = _replay(tmp_path)
    payload = _json(manifest)
    mutation(payload[registry][0])
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / f"compiled-{registry}")

    assert result["status"] == "FAILED"
    issues = _json(tmp_path / f"compiled-{registry}" / "validation.json")["issues"]
    assert any(issue["code"] == "INVALID_INVESTIGATION_MANIFEST" for issue in issues)


@pytest.mark.parametrize(
    "payload",
    [[], {"schema_version": 1, "investigation_id": "synthetic", "alarm_seeds": ["not-an-object"], "incidents": [], "windows": [], "candidate_bindings": [], "trace_bindings": [], "call_tree_bindings": [], "source_bindings": []}],
)
def test_malformed_manifest_is_a_deterministic_failed_product_not_a_crash(tmp_path, payload):
    data_root, manifest = _replay(tmp_path)
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_evidence(manifest, data_root=data_root, output_dir=tmp_path / "compiled-malformed")

    assert result["status"] == "FAILED"
    assert any(issue["code"] == "INVALID_INVESTIGATION_MANIFEST" for issue in result["validation"]["issues"])
    assert validate_compiled_dir(tmp_path / "compiled-malformed")["status"] == "FAIL"
