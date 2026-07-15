# Investigation Depth Evidence Schema

Depth schemas are bounded additions, not a universal Evidence ontology.

- Metric semantic status is one of `VERIFIED`, `AMBIGUOUS`, `UNKNOWN`.
- A duration is named `duration_ms` only when the input unit is verified as ms; otherwise raw field/value/unit are retained without a normalized value.
- Scope is explicit (`business_system`, `application`, `instance`, `transaction`, `trace`, `trace_node`, `alarm`, `external_dependency`) and is never inferred from a nearby name.
- Selection records strategy, ordering, filters, tie behavior, candidate count, source dataset, and rank; it never stores chain-of-thought.
- Local comparison/narrowing/diff results preserve supplied Run/Item/Raw refs and exact timestamps.
- Correction records supersede derived artifacts without editing old Runs.
- SOURCE Items point `source_run_id` to their current SOURCE Run and use `source_refs` for Raw provenance.

Completeness uses `FULL` only when an observed total is covered; otherwise `BOUNDED` or `UNKNOWN`. `overview.max` stays UNKNOWN and fixed-duration clusters stay candidate signals.

## v1.1 evidence identity

- Candidate evidence preserves labels and exact wire identity while adding conservative `semantic_kind` and explicit action resolution.
- Composite `requestType` is a wire label, not semantic identity. The resolver requires both semantic kind and the exact label.
- Exception signals are `THROWN_EXCEPTION`, `LOGGED_ERROR_EVENT`, `ERROR_FLAG_FALSE_LOG_EVENT`, or `UNKNOWN_EXCEPTION_SIGNAL`; Candidate exception counts remain semantically unknown.
- A `trace_tree_node` item is emitted only when Call Tree provides an exact node ID and its source Trace Detail item provides traceId, bizSystemId, and queryTimestamp. It is the sole Runtime identity accepted by the node-scoped exception Source; actionGuid/applicationId/actionType are not substitutes.
- Evidence Envelope adapters expose Candidate rows, performance windows, exception events, and recursive Call Trees to existing bounded primitives without editing the source artifact.
- Compiled evidence uses Manifest binding identity, never same-name lookup. Deep spans retain node ID, parent, depth, total/exclusive time, type/name, and evidence ref.
- Only `LIVE_OBSERVED` and `DERIVED_FROM_VERIFIED_ROUTE` links propagate as verified navigation.
