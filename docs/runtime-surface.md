# Runtime Surface

## Core Agent Surface

`discover`, three-request `collect`, `inspect candidates`, `investigate_trace`, `inspect_call_tree`, and `sanitized-export`. This is the default mental model and scoped Live-validated Golden Path.

## Advanced Read-only Source Surface

`performance-error-series`, `performance-throughput-series`, alarm list/detail/metric, recent request response/error/throughput rankings, application instances, external calls, and trace exceptions. Each invocation is one fixed READ recipe and one immutable SOURCE Run. No automatic loops or fanout.

## Local-only Surface

Promotion matrix, Candidate exact matching, trace candidates/selection and sample assessment, Evidence Envelope adaptation, window narrowing/peak, path/error triage, window/instance/call-tree comparison, external candidate analysis, corrections, and five workflow plans. These perform 0 HTTP and create 0 Run.

## Deterministic Evidence Composition Surface

`depth evidence-compile` reads one formal Investigation Manifest and immutable Runs into a new compiled directory. `depth evidence-validate` verifies the product and its hashes. Both perform 0 HTTP, create 0 Run, and do not mutate data-root, `.inflight`, or `runs.jsonl`. They compile evidence and readiness only; report generation is not a runtime surface.

## Research-only or rejected

Component operations with uneven evidence, ambiguous `overview.max`, generic endpoint execution, unbounded scans, and all writes. None enters production safety.
