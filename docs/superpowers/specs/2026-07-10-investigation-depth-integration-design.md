# Investigation Depth Integration Design

## Authority and outcome

Current `main` is the semantic authority for HTTP execution, authentication, retry, pacing, immutable Runs, failure states, action identity, provenance, and sanitized export. The donor branch supplies domain logic and documentation only after each capability is checked against those contracts. No donor commit is merged or cherry-picked.

The integrated product retains the three-request Core Collect Golden Path and adds two separate layers:

1. explicit one-request advanced read-only `source` acquisitions that create immutable `SOURCE` Runs;
2. deterministic local `depth` primitives and workflow plans that perform no HTTP and create no Run.

## Runtime architecture

`run_source_capability` validates the source reference, exact wire identity, time context, capability recipe, auth configuration, and read-only endpoint before acquiring the live lock. It then uses the existing `HttpExecutor` and `RunStore`, producing the same preflight, Raw, Evidence, Coverage, Manifest, retry/auth, and `FAILED`/`EMPTY` semantics as main.

The production source registry is the sole authority for runtime-exposed source paths. Every registry row names one fixed request builder, expected logical request count of one, source-kind/identity rules, normalizer, verification qualification, and promotion status. Research-only protocol rows never enter this registry or the safety allowlist.

Local primitives accept JSON or existing evidence values, return schema-versioned deterministic JSON, preserve supplied `source_run_id`, `item_ref`, scope, time window, and source references, and never instantiate transport or storage. Workflow plans name only integrated capabilities and explicitly mark research-only or unavailable steps.

## Promotion decisions

- `performance-error-series`, `performance-throughput-series`, alarm list/detail/metric series, recent-request rankings, application instances, external calls, and trace exceptions are advanced read-only, not Core or Golden Path.
- Core response performance remains part of `collect`; its source form is superseded by main.
- `responseList` returns continuation actions only when its own verified lineage and main's exact action-type identity gate both hold. Error/throughput rankings do not inherit that proof.
- component operations and alarm writes remain research-only; no WRITE or UNKNOWN endpoint enters runtime.
- ambiguous `overview.max` remains raw/research-only. Metric trust uses only `VERIFIED`, `AMBIGUOUS`, or `UNKNOWN`.

## Error and safety behavior

Invalid source/time/capability inputs produce machine-readable `BLOCKED` Runs before lock acquisition; plan/local commands have zero filesystem side effects. Missing default transport auth blocks before HTTP. Runtime HTTP remains serial and raw-before-normalized. Source request failures create `FAILED`, successful empty payloads create `EMPTY`, and retries/auth replay count actual attempts while preflight records one expected logical request.

## Verification

Tests cover every accepted donor behavior, every executable source path, zero-side-effect local operations, Core Collect's unchanged request count, main's 35 closure contracts, source Run provenance and immutability, workflow determinism, protocol consistency, CLI smoke, export leak closure, and a before/after fingerprint of private/live data roots. All work is offline with fake transports.

