# v1.2 Final Verification

## Outcome

Implementation and offline validation status: **PASS / READY FOR GIT CLOSURE**.

This verification used the exact checkout at `/Users/wangrundong/work/ty-apm-cli`; `tingyun_cli` imported from `src/tingyun_cli/__init__.py` and reported package version `1.2.0`. No Live Tingyun request, private Run, private Capture Raw, credential, internal origin or LLM call was used.

## Research Convergence

- Canonical inputs: the four files in `research/protocol/`; generated outputs are navigation/audit products, not a second handwritten ledger.
- Generated counts: 400 Endpoints, 442 Variants, 29 Capabilities, 5 Workflows, 18 Gaps and 16 Runtime promotion rows.
- Research Health: `PASS`, zero issues. Protocol consistency checker: `PASS`.
- Machine output schemas: Research View and Research Diff both validate with zero violations.
- Two consecutive generations were byte-identical:
  - `research-index.json`: `2eb2d0bcaca93b6d94c7c8cc9829037a699c5bfe580bf74bd7b6ef46a137b6cc`
  - `research-overview.md`: `d29b99664aee0781f4631c7a0058e025380d1e6eb8f987e636ac3f680a46159d`
- Drift check after the second generation: `PASS`, empty drift list.

Health now audits advertised totals, duplicate IDs, duplicate method/path and Variant discriminants, unknown cross-ledger references, Runtime-to-protocol mapping, READ safety, Runtime verification maturity and human capability-matrix claims against the canonical Capability ledger.

## Runtime and Agent contracts

- The only new Live surface is exact-node `source trace-stack`: one bounded READ request from an explicit `trace_tree_node` with bizSystemId, treeId, traceId and queryTimestamp.
- Plain Trace input, incomplete identity, search/fan-out and unsafe surfaces block before HTTP.
- HTTP success with a Stack payload other than `data: array[string]` creates `FAILED` evidence with `PROTOCOL_SHAPE_MISMATCH`; a valid empty array remains `EMPTY`.
- Evidence Items preserve legacy `available_actions` and add explicit `action_contracts` / `action_blockers` with surface, exact Run/item input, CLI mapping, logical request budget and reason code.
- Trace Search, error representative automation, DubboProvider direct TX/IF resolution, unstable navigation URLs, writes and a generic Endpoint runner remain unpromoted.

## Evidence Composition compatibility

The sanitized v1.1 offline Manifest was compiled twice from immutable fixture Runs. Both compiles returned `SUCCESS`; validation returned `PASS`; all core products were byte-stable:

- `evidence-map.json`: `e22909410c0e302236465ea8d06cb1fbaf26ecffc23e3ae1c7203037b1f89ee7`
- `source-of-truth.json`: `39523b02c4e04c95713e6b86daaed24d2ff13ecf93d7c6341191615f925624e4`
- `coverage.json`: `dda653cde6db3b374e80520aefe3de59f2629d18a67adaad3a1499381765ad25`
- `report-readiness.json`: `806ca75b580178fb2cc7c176653574eb31f86c9e5624f338024dc922eb5d775c`
- `validation.json`: `e7f37090894f2675d12e57ec308385e06a367ceaeee94f8d51e3eea80544620b`

The expected `WRONG_TARGET_TRACE_REJECTED` audit warning remains preserved; there were no validation errors.

## System Model v0 offline closure

Manifest A explicitly bound four sanitized Runs: Collect, Trace, Call Tree and External Source. Two independent compiles each produced 12 entities and 11 relations, made 0 HTTP requests and had identical snapshot SHA-256:

`622a055ed531d12f0f3fa701222d2f3d06c0807e846a46be690ce2bede9b0cf6`

Both validations returned `PASS` with zero issues. Manifest B compiled one Collect Run into 3 entities and 2 relations; snapshot SHA-256:

`fd57380511bb46ba006db4b3f5710add2de43f2b574f6019c0db1b91bc3f2842`

Diff A -> B returned `SUCCESS`; its fixed absence semantics were `NOT_OBSERVED_IN_AFTER_INPUTS`. Both inputs were checked against the committed schema and semantic integrity rules before diffing. The model never emitted a deletion claim.

Regression coverage also proves:

- output cannot be written under immutable `runs/` or `.inflight/` storage;
- dependency order does not drop Trace -> root-node lineage;
- non-object JSON, malformed nested refs, empty Evidence refs and broken relation endpoints fail machine-readably;
- evidence-bearing/attempted Artifacts with missing Raw are excluded and fail compilation;
- coverage-only `BLOCKED` / `SKIPPED` Artifacts do not falsely require Raw;
- every emitted entity/relation has non-empty structured Run/Artifact/Raw provenance;
- compile/validate/diff use 0 HTTP, 0 LLM and create 0 Run.

## Terminal gates

| Gate | Result |
|---|---|
| `PYTHONPATH=src python3 -m pytest -q` | PASS — 228 tests |
| Protocol consistency | PASS |
| Research generate twice / drift check | PASS |
| Seven committed JSON schemas parse | PASS |
| Research/System Model output schema validation | PASS |
| Evidence Composition double compile/validate | PASS |
| System Model A double compile/validate, B compile, A -> B diff | PASS |
| CLI root/depth/source help contains documented commands | PASS |
| `python3 -m compileall -q src tests research/tools` | PASS |
| `git diff --check` | PASS |
| Added-line credential/private-key scan | PASS |

The full suite covers the existing Core Golden Path, Advanced Sources, local Depth, old sanitized Runs/Fixtures, Evidence Composition, safety, retry/storage/export contracts and the new v1.2 surfaces.

## Independent review closure

Two read-only reviews were run against the Goal and repository standards. Their initial findings drove additional red/green tests for Stack shape drift, System Model dependency order, output schemas, Research cross-ledger health, immutable Run protection, malformed snapshot handling, Evidence/Raw traceability, status-aware Raw semantics and diff input integrity.

- Spec re-review: **PASS**, no remaining implementation/spec finding.
- Standards re-review: **PASS**, no remaining hard finding; independent System Model targeted suite: 17 passed.

## Complexity and Git boundary

No database, background service, workflow executor, generic Endpoint runner, mutable current-state store, report/RCA generator or LLM dependency was introduced. Existing Run, Evidence, schema-validation and Call Tree extraction abstractions were reused.

This report is part of the terminal implementation commit. A commit cannot contain its own SHA, so the final commit SHA, push result and local `main == origin/main` proof are recorded in the terminal delivery response after Git closure.
