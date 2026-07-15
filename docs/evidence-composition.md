# Deterministic Evidence Composition

Evidence composition turns one explicit Investigation Manifest plus immutable
Runs into a deterministic evidence product. It performs no HTTP request, does
not create or edit a Run, does not mutate data-root, and does not choose a next
investigation step.

## Commands

```bash
tingyun depth evidence-compile \
  --manifest /path/to/investigation-manifest.json \
  --output-dir /path/to/compiled

tingyun depth evidence-validate \
  --compiled-dir /path/to/compiled
```

Compiler status is `SUCCESS` or `FAILED`; validator status is `PASS` or
`FAIL`. A failed compiler still publishes an atomic, auditable validation
product unless publication itself cannot start (for example,
`OUTPUT_DIR_NOT_EMPTY`).

## Output

```text
compiled/
├── source-of-truth.json
├── evidence-map.json
├── coverage.json
├── validation.json
├── report-readiness.json
└── extractions/
    ├── candidates/
    ├── traces/
    ├── call-trees/
    ├── external/
    ├── recent-requests/
    ├── timeseries/
    └── topology/
```

`source-of-truth.json` holds the Manifest hash, Run manifest hashes, canonical
registries, and required counts. `evidence-map.json` links Alarm -> Incident ->
Window -> Candidate -> Trace -> Call Tree/Source -> extraction -> Raw refs.
`coverage.json` reports inventory, context, Candidate, and deep-evidence
coverage. `validation.json` is the authoritative issue ledger and contains
hashes for every other compiled output. `report-readiness.json` assesses
evidence sufficiency only.

## Hard validation

- Candidate `collect_run_id` must equal its Window Run.
- Candidate identity is exact `source_run_id + item_ref` in that Run.
- Every binding Incident must be canonical and match its parent lineage.
- Trace target lineage is recomputed independently for both the Run manifest
  and Trace artifact item; successful wrong-target Runs/items are preserved in
  `rejected_trace_runs` and excluded from the Incident chain.
- Every target-correct Call Tree is retained and must point to its exact Trace.
- Bound Trace and Call Tree artifacts must be `SUCCESS` with their required
  nonempty shapes; `FAILED` and `EMPTY` are gaps, never evidence.
- Source role must match artifact kind and, for rankings, ranking provenance.
- Referenced Run, artifact, and Raw files must exist.
- Run IDs, artifact paths, and Raw refs must remain inside the bound data-root
  Run; path traversal and escaping symlinks are rejected.
- Only navigation proven `LIVE_OBSERVED` or
  `DERIVED_FROM_VERIFIED_ROUTE` propagates; guessed URLs are excluded.

An `ERROR` makes compilation `FAILED`; `WARNING` preserves a usable product
when the evidence is still valid (for example, an audited wrong-target Trace
that has a correct replacement).

The Run manifest artifact status and artifact payload status must agree. A
status mismatch is `ARTIFACT_STATUS_MISMATCH` and neither representation is
accepted as evidence until the immutable input is corrected/replaced.

## Deep extraction

Call Tree extraction retains all reachable `treeNode/nodeMap` nodes, including
Web, Dubbo, database/SQL, HTTP, Redis, errors, exceptions, and logged errors.
Every span retains node identity, parent, depth, type, name, total time,
exclusive time, and evidence ref. Ranking prefers exclusive time. When only
total time exists, `overlap_warning=true`; parent and child totals are never
summed as independent percentages.

## Determinism and publication

Core output contains no current timestamp, random ID, or temporary path. JSON
keys and registries are stably ordered. Files are written to a sibling staging
directory and atomically renamed only after all outputs and hashes exist.
Repeated compilation of identical inputs must be byte-identical.

## Boundary with System Model

Evidence Composition is investigation-scoped: its interface is the formal Investigation Manifest and its primary organization is Alarm/Incident/Window/evidence lineage plus readiness. System Model is system-scoped: its interface is an explicit list of immutable Run refs and its primary organization is observed entities, stable ownership observations, windowed runtime relations, freshness, coverage and diff.

System Model reuses the existing Run/Artifact/Item/Raw evidence reference shape, schema validator and Call Tree extractor. It does not copy the Evidence Compiler, does not consume report readiness, and does not convert a model snapshot into an Incident, RCA or report.
