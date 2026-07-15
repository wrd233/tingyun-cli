# v1.2 Offline Closure Report

## Research Convergence

- Generated source of truth: 400 Endpoints, 442 Variants, 29 Capabilities, 5 Workflows and 18 Gaps.
- Verification distribution: 201 VERIFIED / 12 PARTIALLY_VERIFIED / 187 DOCUMENTED_ONLY Endpoints; 22 VERIFIED / 7 PARTIALLY_VERIFIED Capabilities.
- Access distribution: 317 READ / 83 WRITE.
- Runtime registry: 1 Core, 12 Advanced, 2 Research-only and 1 Rejected row, all mapped to canonical protocol Capability IDs.
- Health: PASS with zero issues.
- Two consecutive generations were byte-stable after capability-matrix parsing and cross-ledger health checks: `research-index.json` SHA-256 `2eb2d0bcaca93b6d94c7c8cc9829037a699c5bfe580bf74bd7b6ef46a137b6cc`; overview SHA-256 `d29b99664aee0781f4631c7a0058e025380d1e6eb8f987e636ac3f680a46159d`.

## Runtime and Agent Contract

- `source trace-stack` accepts only exact `trace_tree_node` Evidence Items with treeId, traceId, bizSystemId and queryTimestamp.
- Request budget is one logical READ request. Raw request/response is persisted before normalized `trace_stack` evidence.
- Plain Trace input blocks before HTTP. No tree traversal or fan-out exists.
- A successful HTTP response with a non-`array[string]` Stack shape is a machine-readable `FAILED` Artifact, never `EMPTY`.
- Candidate, Trace, Alarm and Trace Node evidence now exposes machine-readable Action availability/blockers while retaining legacy `available_actions` behavior.
- Trace Search, error representative selection, DubboProvider direct TX/IF, unstable URLs, writes and generic execution remain blocked/research-only.

## System Model offline loop

Input A: four explicit sanitized Runs (Collect, Trace, Call Tree and External Source). Compile A was executed twice:

- status: SUCCESS; actual requests: 0;
- entities: 12; relations: 11; coverage: PARTIAL;
- repeated snapshot SHA-256: `622a055ed531d12f0f3fa701222d2f3d06c0807e846a46be690ce2bede9b0cf6` for both outputs;
- validator: PASS with zero issues.

The compiler now consumes dependency-bearing evidence in a deterministic order, so the Trace -> root-node relation is preserved regardless of Run ID ordering. Input/output schemas reject malformed snapshots and require non-empty structured Evidence/Raw refs; output directories inside immutable Run storage are blocked; attempted/evidence-bearing Artifacts with missing Raw refs are excluded from facts and fail compilation. Coverage-only `BLOCKED/SKIPPED` Artifacts remain valid without Raw.

Input B: one explicit sanitized Collect Run. Compile B produced 3 entities and 2 relations. Diff A -> B reported new biz-002 business/application/action facts and marked A-only Trace/Call Tree/external facts as `NOT_OBSERVED_IN_AFTER_INPUTS`; it emitted no deletion claim.

## Validation gates

The implementation was developed through vertical RED -> GREEN tests. The first post-implementation full suite exposed six compatibility regressions (empty `available_actions` presence and one missing safety fixture enumeration); all were repaired before documentation. Review-driven red tests then locked Stack protocol-shape failure, dependency-order independence, output schemas, cross-ledger Research checks, immutable Run output protection, non-object and nested malformed snapshot rejection, missing-Raw exclusion, `BLOCKED/SKIPPED` coverage semantics, and semantic integrity validation before diff. The current full suite passes 228 tests.

Final exact-checkout test, compile, protocol, schema, CLI help, fixture, generated-view drift, deterministic replay, `git diff --check`, secret scan, review, Git and remote-parity results are recorded in `02-final-verification.md` after the terminal gate run.
