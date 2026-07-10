# Investigation Depth Evidence Schema

Depth schemas are bounded additions, not a universal Evidence ontology.

- Metric semantic status is one of `VERIFIED`, `AMBIGUOUS`, `UNKNOWN`.
- A duration is named `duration_ms` only when the input unit is verified as ms; otherwise raw field/value/unit are retained without a normalized value.
- Scope is explicit (`business_system`, `application`, `instance`, `transaction`, `trace`, `alarm`, `external_dependency`) and is never inferred from a nearby name.
- Selection records strategy, ordering, filters, tie behavior, candidate count, source dataset, and rank; it never stores chain-of-thought.
- Local comparison/narrowing/diff results preserve supplied Run/Item/Raw refs and exact timestamps.
- Correction records supersede derived artifacts without editing old Runs.
- SOURCE Items point `source_run_id` to their current SOURCE Run and use `source_refs` for Raw provenance.

Completeness uses `FULL` only when an observed total is covered; otherwise `BOUNDED` or `UNKNOWN`. `overview.max` stays UNKNOWN and fixed-duration clusters stay candidate signals.
