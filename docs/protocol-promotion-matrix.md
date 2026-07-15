# Protocol Promotion Matrix

`tingyun depth promotion-matrix` is the machine-readable view. Status meanings:

- `CORE_LIVE_VALIDATED`: existing scoped Golden Path fact.
- `ADVANCED_READ_ONLY`: fixed runtime source recipe supported by existing protocol evidence; not default and not collectively Live-Proven.
- `RESEARCH_ONLY`: retained knowledge with insufficient runtime closure.
- `REJECTED`: forbidden or semantically unsafe, including every WRITE capability.

The detailed endpoint, identity, time, normalizer, and reason table is in `validation-analysis/branch-integration/04-source-capability-promotion-matrix.md`.

v1.1 adds local semantic/selection/composition contracts without promoting any endpoint: Candidate semantic kind, semantic action resolver, deterministic Candidate match, Trace target/sample assessment, Evidence Envelope adaptation, evidence compilation, and compiled validation. These are `LOCAL_ONLY_VERIFIED` in documentation terms: 0 HTTP, 0 Run, and no expansion of the READ safety allowlist. DubboProvider `TX,IF` direct Trace remains unresolved until focused Live proof exists.

The 2026-07-15 Capture corrected two existing Advanced recipes without expanding the allowlist: alarm detail normalization now understands key/value `parentGroup` arrays and multiple `metrics[]`; trace exceptions now require node-scoped `treeId + traceId + bizSystemId + queryTimestamp` instead of action-scoped fields. Trace search/list and non-empty stackTraces are Protocol `VERIFIED` but remain `RESEARCH_ONLY` at Runtime. Server-side export task creation remains `REJECTED` as WRITE.
