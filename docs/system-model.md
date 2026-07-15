# Evidence-backed Living System Model v0

## Purpose and boundary

System Model v0 is a deterministic, immutable local snapshot compiled from an explicit list of existing Runs. It helps an Agent understand which business systems, applications, actions, traces, trace nodes, external dependencies, instance candidates and alarms have actually been observed, and when.

It is not a CMDB, digital twin, database, online cache, report generator or RCA engine. It does not infer identity from names, IPs, URLs or temporal proximity. Coverage is `PARTIAL` by design.

## Manifest

The committed input schema is `schemas/system-model-manifest.schema.json`. Snapshot, validation and diff outputs are also versioned by `schemas/system-model-snapshot.schema.json`, `schemas/system-model-validation.schema.json` and `schemas/system-model-diff.schema.json`. Required manifest fields are:

```json
{
  "schema_version": 1,
  "snapshot_id": "system-model-2026-07-15-a",
  "as_of": "2026-07-15T12:00:00Z",
  "freshness_threshold_seconds": 86400,
  "run_refs": [
    {"run_id": "run-..."},
    {"run_id": "run-...", "expected_manifest_sha256": "optional-pinned-hash"}
  ]
}
```

`as_of` and the freshness threshold are explicit inputs, so compilation never reads the current clock. Optional manifest hashes detect a changed source Run before compilation.

## Compile

```bash
tingyun --data-root .tingyun-runs depth system-model-compile \
  --manifest system-model-manifest.json \
  --output-dir compiled-model
```

Compile performs 0 HTTP, 0 LLM and creates 0 Run. It reads only each declared Run manifest and its declared Artifacts, verifies manifest/artifact status agreement, checks Raw refs, follows explicit parent Run/item lineage, and rejects a non-empty output directory. Output must also be outside `data_root/runs/` and `data_root/.inflight/`; a compiled snapshot is never appended to an immutable Run. An evidence-bearing/attempted Artifact with a missing Raw ref is reported as an error and excluded from modeled facts. `BLOCKED` and `SKIPPED` remain coverage-only statuses and do not require a request or Raw record.

The output contains:

- `snapshot.json`: source Run hashes, entities, relations, observations, freshness, coverage, conflicts and hard boundaries.
- `validation.json`: deterministic issues and the snapshot hash.

Canonical identities use observed stable IDs. External services and generic topology nodes are scoped to source Run/item when cross-run stable identity is not proven. Display identity never participates in deduplication.

Stable ownership observations use `STABLE_OWNERSHIP_OBSERVATION`. Trace, Call Tree, external-call and other window-specific relationships use `WINDOWED_RUNTIME_OBSERVATION` and must carry time context. Each entity/relation carries Run, Artifact, optional Item and Raw refs.

## Validate

```bash
tingyun depth system-model-validate --compiled-dir compiled-model
```

Validation first enforces the committed snapshot and validation-result schemas, then checks the snapshot hash, unique entity/relation IDs, relation endpoints, declared source Runs, non-empty structured Evidence/Raw references, and required time context for runtime relations. Non-object JSON and malformed nested references return machine-readable `FAIL`; they cannot crash validation or pass as an empty model. `FAIL` is an integrity outcome, not an empty model.

## Diff

```bash
tingyun depth system-model-diff \
  --before model-a/snapshot.json \
  --after model-b/snapshot.json
```

Diff validates both input snapshots and its own output schema. It reports added, changed and `not_observed` entities/relations, coverage changes and new conflicts. Its fixed interpretation is `NOT_OBSERVED_IN_AFTER_INPUTS`: absence never means deleted, stopped, healthy or unhealthy.

## Relationship to Evidence Composition

Evidence Composition binds Alarm Seeds, Incidents, exact Windows, Candidate/Trace/Call Tree lineage and Source roles into an investigation-level Evidence Map and report-readiness assessment. System Model consumes explicit Runs to build a system-level observation snapshot. They share existing Evidence references, identity discipline, Call Tree extraction, schema validation and coverage semantics; neither executes a Workflow or generates conclusions.

## v0 supported depth

v0 extracts strong identities and relationships from targets, candidates, Trace, Call Tree, external calls, instance context, alarms, topology and performance artifacts. Stack/exception/metric-series artifacts remain preserved as source coverage but are not promoted into new causal model relationships. Unknown or unmodeled depth is reported rather than fabricated.
